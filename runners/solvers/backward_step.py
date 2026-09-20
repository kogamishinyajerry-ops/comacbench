"""Engineering checks for one bounded native OpenFOAM backward-step profile."""
from pathlib import Path
import copy
import math
import re
from .foam_text import FoamError, Reader, dictionary, tokens, counted, field_values, number, integer
from .cfd_profile import PROFILE, TEMPLATES, THRESHOLDS

INPUTS=('0/U','0/p','constant/transportProperties','constant/turbulenceProperties',
        'system/blockMeshDict','system/controlDict','system/fvSchemes','system/fvSolution')
STAGES=('inputs','mesh','solver','convergence','conservation','qoi')
ISSUE_CODES={'precomputed_output','missing_input','unsupported_input','boundary_mismatch',
             'fluid_mismatch','mesh_below_minimum','mesh_invalid','inlet_profile_mismatch',
             'solver_failed','not_converged','mass_imbalance','invalid_native_field',
             'qoi_unstable','qoi_outside_reference','script_failed','evidence_capture_failed'}


def equivalent(value):
    if isinstance(value,dict):return {k:equivalent(v) for k,v in value.items()}
    if isinstance(value,list):return [equivalent(v) for v in value]
    try:return number(value)
    except (ValueError,TypeError):return value


def require(condition, message):
    if not condition:raise FoamError(message)


def audit_inputs(case):
    case=Path(case)
    issues=[]
    def bad(code, field, message, fix):
        issues.append({'code':code,'field':field,'message':message,'suggested_fix':fix})
    if case.is_symlink():
        bad('precomputed_output','case','算例根目录不能是符号链接。','生成正规算例目录。')
        return {'passed':False,'issues':issues,'parsed':{}}
    for path in case.rglob('*'):
        name=str(path.relative_to(case))
        if path.is_symlink() or path.is_file() and name not in INPUTS or path.is_dir() and name not in {'0','constant','system'}:
            bad('precomputed_output',name,'只接收声明的原生输入；不能提供预制场、日志、自报 QoI 或符号链接。','删除预制结果，由平台从本次真实求解场重算。')
    for name in INPUTS:
        if not (case/name).is_file():
            bad('missing_input',name,'缺少必需的原生算例文件。','按公开材料清单补齐文件。')
    parsed={}
    for name in INPUTS:
        if not (case/name).is_file():continue
        code='unsupported_input'
        try:
            if name=='system/fvSchemes':
                require(tokens((case/name).read_text())==tokens(TEMPLATES[name]),'离散格式须使用公开模板，仅可调整空白和注释。')
                continue
            data=dictionary(case/name)
            expected=Reader(TEMPLATES[name]).mapping()
            parsed[name]=copy.deepcopy(data)
            # File headers carry no runtime options; only the public header is accepted.
            require(equivalent(data.pop('FoamFile'))==equivalent(expected.pop('FoamFile')),'FoamFile 头不符合公开方言。')
            if name=='system/controlDict':
                end=integer(data['endTime'][0]);require(1<=end<=3000,'endTime 必须在 1..3000。')
                data['endTime']=expected['endTime']
            if name=='system/blockMeshDict':
                blocks=data['blocks'][0];ref=expected['blocks'][0]
                require(len(blocks)==len(ref),'需要公开的三个连通六面体块。')
                for i in (2,7,12):
                    nx,ny,nz=[integer(v) for v in blocks[i]]
                    require(1<=nx<=400 and 1<=ny<=100 and nz==1,'网格划分超出公开资源范围或不满足二维单层。')
                    blocks[i]=ref[i]
            if name in ('0/U','0/p'):
                code='boundary_mismatch'
                if name=='0/U':
                    inlet=data['boundaryField']['inlet']
                    require(inlet['value'][0:2]==['nonuniform','List<vector>'],'入口须提供实际面顺序的非均匀速度向量。')
                    field_values(inlet['value'],integer(inlet['value'][2]),True)
                    inlet['value']=expected['boundaryField']['inlet']['value']
            if name.startswith('constant/'):
                code='fluid_mismatch'
            require(equivalent(data)==equivalent(expected),'字段缺失、多余或数值与公开输入契约不一致。')
        except (ValueError,TypeError,KeyError,IndexError,OSError,RecursionError) as e:
            bad(code,name,str(e),'对照 templates/ 修复该文件；本版只支持声明的输入方言。')
    return {'passed':not issues,'issues':issues,'parsed':parsed}


def mesh_data(case):
    base=Path(case)/'constant/polyMesh'
    mesh={k:counted(base/k,k) for k in ('points','faces','owner','neighbour','boundary')}
    pts=mesh['points'];faces=mesh['faces']
    require(len(mesh['owner'])==len(faces),'owner 长度错误')
    require(all(len(f)==4 and all(0<=p<len(pts) for p in f) for f in faces),'需要合法四边形面')
    mesh['centres']=[tuple(sum(pts[p][d] for p in f)/len(f) for d in range(3)) for f in faces]
    mesh['cells']=max(mesh['owner'])+1
    ranges={}
    for name,patch in mesh['boundary'].items():
        start=integer(patch['startFace'][0]);n=integer(patch['nFaces'][0])
        require(start>=len(mesh['neighbour']) and start+n<=len(faces),'patch 范围错误')
        ranges[name]=list(range(start,start+n))
    require(sorted(i for ids in ranges.values() for i in ids)==list(range(len(mesh['neighbour']),len(faces))),'边界面缺失或重叠')
    mesh['ranges']=ranges
    return mesh


def audit_mesh(case, mesh_log, inputs):
    mesh=mesh_data(case)
    require('Mesh OK.' in mesh_log and re.search(r'Number of regions:\s+1\b',mesh_log),'checkMesh 未确认单连通有效网格')
    require(set(mesh['ranges'])=={'inlet','outlet','lowerWall','upperWall','frontAndBack'},'原生网格 patch 错误')
    require(mesh['cells']>=THRESHOLDS['min_cells'],'mesh_below_minimum')
    pts=mesh['points'];centres=mesh['centres'];ranges=mesh['ranges']
    require(all(any(abs(p[2]-z)<1e-10 for z in (0,.01)) for p in pts),'需要厚度 0.01 m 的单层二维网格')
    # Geometry, topology and grading are fixed by the input profile. Inspect actual
    # discretization as well, including the recirculation zone and first wall cell.
    wall=[i for i in ranges['lowerWall'] if abs(centres[i][1])<1e-10 and centres[i][0]>0]
    require(len(wall)>10,'下游底壁面不足')
    near=[i for i in wall if centres[i][0]<=.06]
    require(bool(near),'缺少再附着区域网格')
    require(max(max(pts[p][0] for p in mesh['faces'][i])-min(pts[p][0] for p in mesh['faces'][i]) for i in near)<=.00101,'mesh_below_minimum')
    owner_points={}
    wanted={mesh['owner'][i] for i in near}
    for i,f in enumerate(mesh['faces']):
        owners=[mesh['owner'][i]]+([mesh['neighbour'][i]] if i<len(mesh['neighbour']) else [])
        for c in owners:
            if c in wanted:owner_points.setdefault(c,set()).update(f)
    require(max(max(pts[p][1] for p in ids) for ids in owner_points.values())<=.0003,'mesh_below_minimum')
    velocities=field_values(inputs['0/U']['boundaryField']['inlet']['value'],len(ranges['inlet']),True)
    for i,v in zip(ranges['inlet'],velocities):
        eta=(centres[i][1]-.01)/.01
        require(abs(v[0]-6*eta*(1-eta))<1e-7 and abs(v[1])+abs(v[2])<1e-12,'inlet_profile_mismatch')
    return mesh,{'cells':mesh['cells'],'inlet_faces':len(velocities),'downstream_wall_faces':len(wall),
                 'mesh_ok':True,'single_region':True}


def residuals(log):
    curve=[];step=None
    for line in log.splitlines():
        m=re.fullmatch(r'Time = (\d+)(?:s)?',line.strip())
        if m:
            step={'iteration':int(m[1])};curve.append(step)
        m=re.search(r'Solving for (p|Ux|Uy), Initial residual = ([^,]+),',line)
        if m and step is not None:step[m[1]]=number(m[2])
    require(bool(curve) and all(all(k in row for k in ('p','Ux','Uy')) for row in curve),'原生日志残差序列缺失')
    final=curve[-1]
    require(all(row[k]>=0 for row in curve for k in ('p','Ux','Uy')),'负残差无效')
    drops={k:math.log10(max(max(row[k] for row in curve[:10]),1e-300)/max(final[k],1e-300)) for k in ('p','Ux','Uy')}
    converged=bool(re.search(r'SIMPLE solution converged in '+str(final['iteration'])+r' iterations',log))
    passed=converged and '\nEnd\n' in log and all(final[k]<=THRESHOLDS['max_p_residual' if k=='p' else 'max_U_residual'] and drops[k]>=THRESHOLDS['min_residual_decades'] for k in drops)
    return {'passed':passed,'iteration':final['iteration'],'final':final,'drop_decades':drops,'curve':curve}


def mass_balance(case, iteration, mesh):
    data=dictionary(Path(case)/str(iteration)/'phi')
    require(equivalent(data['dimensions'])==[[0,3,-1,0,0,0,0]],'phi 必须为 m³/s')
    require(set(data['boundaryField'])==set(mesh['ranges']),'phi patch 不完整')
    flux={}
    for name,ids in mesh['ranges'].items():
        if name=='frontAndBack':
            require(data['boundaryField'][name]['type']==['empty'],'phi 二维面必须 empty')
            continue
        flux[name]=sum(field_values(data['boundaryField'][name]['value'],len(ids)))
    incoming=-flux['inlet'];outgoing=flux['outlet']
    imbalance=abs(sum(flux.values()))/max(incoming,1e-30)
    wall_leak=(abs(flux['lowerWall'])+abs(flux['upperWall']))/max(incoming,1e-30)
    return {'passed':incoming>0 and outgoing>0 and abs(incoming/1e-4-1)<.005 and wall_leak<1e-8 and imbalance<=THRESHOLDS['max_mass_imbalance'],
            'flux_m3_s':flux,'relative_imbalance':imbalance,'wall_leak_ratio':wall_leak}


def reattachment(case, iteration, mesh):
    data=dictionary(Path(case)/str(iteration)/'wallShearStress')
    require(equivalent(data['dimensions'])==[[0,2,-2,0,0,0,0]],'壁面剪切须为运动应力 m²/s²')
    ids=mesh['ranges']['lowerWall']
    values=field_values(data['boundaryField']['lowerWall']['value'],len(ids),True)
    curve=sorted((mesh['centres'][i][0]/.01,-v[0]) for i,v in zip(ids,values) if abs(mesh['centres'][i][1])<1e-10 and mesh['centres'][i][0]>0)
    require(len(curve)>=10 and curve[0][0]<.1 and curve[-1][0]>=6,'下游壁面剪切采样不足')
    require(all(a[0]<b[0] for a,b in zip(curve,curve[1:])),'壁面横坐标须唯一递增')
    brackets=[(a,b) for a,b in zip(curve,curve[1:]) if a[1]<0<=b[1]]
    require(bool(brackets),'未找到负到正的壁面剪切零点')
    a,b=brackets[0]
    value=a[0]-a[1]*(b[0]-a[0])/(b[1]-a[1])
    return {'iteration':iteration,'x_over_h':value,'bracket':[a,b],'curve':curve,
            'method':'downstream bottom wall: -native wallShearStress.x, linear zero crossing'}


def audit_solution(case, log, mesh, reference):
    result={'checks':{},'issues':[]}
    def check(stage, code, message, fn):
        try:
            value=fn();passed=value.get('passed',True)
            result[stage]=value
        except (ValueError,TypeError,KeyError,IndexError,OSError) as e:
            passed=False;message+='：'+str(e)
        result['checks'][stage]='passed' if passed else 'failed'
        if not passed:result['issues'].append({'code':code,'field':stage,'message':message,'suggested_fix':'修复输入后重新求解；平台只接受本次原生输出。'})
        return passed
    if not check('convergence','not_converged','原生残差未满足收敛声明、绝对阈值及至少四数量级下降。',lambda:residuals(log)):
        return result
    iteration=result['convergence']['iteration']
    check('conservation','mass_imbalance','入口、出口与壁面通量未满足质量守恒。',lambda:mass_balance(case,iteration,mesh))
    def qoi():
        times=sorted(int(p.name) for p in Path(case).iterdir() if p.is_dir() and p.name.isdecimal() and int(p.name)>0 and (p/'wallShearStress').is_file())
        require(len(times)>=2 and times[-1]==iteration,'末次原生场时间不匹配或缺少前一保存场')
        last=reattachment(case,times[-1],mesh);previous=reattachment(case,times[-2],mesh)
        change=abs(last['x_over_h']-previous['x_over_h'])/abs(last['x_over_h'])
        require(change<=THRESHOLDS['max_qoi_change'],'qoi_unstable：末两场零点尚不稳定')
        error=abs(last['x_over_h']-reference)/abs(reference)
        return {**last,'previous_x_over_h':previous['x_over_h'],'previous_iteration':times[-2],
                'relative_change':change,'reference':reference,'relative_error':error,
                'within_reference':error<=THRESHOLDS['max_relative_error']}
    check('qoi','invalid_native_field','无法从末两次原生壁面剪切场重算可信 QoI。',qoi)
    return result
