"""Isolated fourth-grid study; immutable legacy solver/scoring contracts."""
import argparse
from concurrent.futures import ThreadPoolExecutor
import json
import math
from pathlib import Path
import re
import shutil
import subprocess
import sys
import time
import uuid

ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT))
from runners.solvers.foam_text import Reader, FoamError, dictionary, field_values
from runners.solvers.backward_step import mesh_data, residuals
from runners.solvers.cfd_step_runtime import IMAGE
from studies.cfd_step_sensitivity import write_case as old_write_case, sha, save, evidence, grid_convergence, DOMAINS, REFERENCES, verify_case
from studies.cfd_wall_gradient_diagnostic import wall_gradient, crossing

POLICY={'fine_gci_max':.005,'fine_domain_effect_max':.0025,'p_residual_max':1e-9,
        'U_residual_max':1e-10,'qoi_change_max':1e-5,'mass_imbalance_max':1e-6,
        'inlet_flux_match_max':1e-8,'fine_inlet_bias_max':1e-4,
        'fine_wall_gap_max':.001,'bridge_qoi_change_max':1e-5}


def area_integral(y0,y1,width):
    """Analytic volume flux through an inlet strip, with physical y in metres."""
    if not all(math.isfinite(v) for v in (y0,y1,width)) or not .01-1e-14<=y0<y1<=.02+1e-14 or width<=0:
        raise ValueError('invalid inlet strip')
    a=(y0-.01)/.01;b=(y1-.01)/.01
    return width*.01*((3*b*b-2*b*b*b)-(3*a*a-2*a*a*a))


def field_dictionary(path):
    p=Path(path)
    if p.is_symlink() or not p.is_file() or p.stat().st_size>128*1024*1024:
        raise FoamError('study field must be regular ASCII and <=128 MiB')
    data=Reader(p.read_text(encoding='utf-8')).mapping()
    if data.get('FoamFile',{}).get('format')!=['ascii']:raise FoamError('ASCII required')
    return data


def write_case(case,scale,upstream,downstream,reynolds):
    if scale not in (1,2,4,8):raise ValueError('unsupported grid')
    case=Path(case)
    config=old_write_case(case,min(scale,4),upstream,downstream,reynolds)
    if scale==8:
        mesh=case/'system/blockMeshDict';text=mesh.read_text()
        nxup=5*upstream*4;nxdn=(140+(33 if downstream==60 else 0))*4
        text=text.replace(f'({nxup} 80 1)',f'({nxup*2} 160 1)').replace(f'({nxdn} 80 1)',f'({nxdn*2} 160 1)')
        mesh.write_text(text)
        config.update(scale=8,expected_cells=config['expected_cells']*4,near_step_dx_h=.1/8)
        p=case/'0/U';values='\n'.join(f'({6*((i+.5)/160)*(1-(i+.5)/160):.14g} 0 0)' for i in range(160))
        p.write_text(re.sub(r'value nonuniform List<vector>\s*80\s*\(.*?\);',f'value nonuniform List<vector>\n160\n(\n{values}\n);',p.read_text(),flags=re.S))
    p=case/'system/fvSolution'
    text=p.read_text().replace('smoother        GaussSeidel','smoother        DICGaussSeidel')
    # Only SIMPLE convergence thresholds change here, linear solve tolerances stay fixed.
    text=text.replace('p               1e-8','p               1e-9').replace('U               1e-9','U               1e-10')
    p.write_text(text)
    p=case/'system/controlDict';p.write_text(p.read_text().replace('writeInterval   500','writeInterval   100').replace('endTime         30000','endTime         60000'))
    return config


def native(work,step,source=None,deadline=None):
    commands={'blockMesh':'blockMesh -case /work/case','checkMesh':'checkMesh -case /work/case',
              'mapFields':'mapFields -case /work/case -consistent -sourceTime latestTime /source',
              'simpleFoam':'simpleFoam -case /work/case'}
    if step not in commands:raise ValueError('unsupported native command')
    name='comac-g4-'+uuid.uuid4().hex
    command=['docker','run','--rm','--pull','never','--name',name,'--network','none',
             '--platform','linux/amd64','--cpus','2','--memory','4g','--pids-limit','128',
             '-v',str(work.resolve())+':/work','-w','/work']
    if source:command+=['-v',str(source.resolve())+':/source:ro']
    command+=['--entrypoint','bash',IMAGE,'-c','source /opt/openfoam10/etc/bashrc && '+commands[step]]
    started=time.monotonic();timeout=False;code=None
    try:
        with (work/('log.'+step)).open('wb') as f:
            code=subprocess.run(command,stdout=f,stderr=subprocess.STDOUT,timeout=max(1,(deadline or started+14400)-started)).returncode
    except subprocess.TimeoutExpired:timeout=True
    finally:
        subprocess.run(['docker','rm','-f',name],stdout=subprocess.DEVNULL,stderr=subprocess.DEVNULL,timeout=15)
    result={'step':step,'exit':code,'timeout':timeout,'seconds':time.monotonic()-started,'command':command}
    if code!=0 or timeout:raise RuntimeError(json.dumps(result))
    return result


def inlet_check(case,mesh,iteration):
    ids=mesh['ranges']['inlet'];Udata=field_dictionary(case/str(iteration)/'U');Pdata=field_dictionary(case/str(iteration)/'phi')
    if Pdata['dimensions']!=[['0','3','-1','0','0','0','0']]:raise ValueError('phi dimensions')
    values=field_values(Udata['boundaryField']['inlet']['value'],len(ids),True)
    phi=field_values(Pdata['boundaryField']['inlet']['value'],len(ids))
    flux=exact=area=0.;max_face_error=0.;strips=[]
    for face,u,f in zip(ids,values,phi):
        points=[mesh['points'][p] for p in mesh['faces'][face]]
        ys=[p[1] for p in points];zs=[p[2] for p in points];xs=[p[0] for p in points]
        if max(xs)-min(xs)>1e-12 or abs(u[1])+abs(u[2])>1e-12:raise ValueError('non-planar inlet/transverse flow')
        a=(max(ys)-min(ys))*(max(zs)-min(zs));q=area_integral(min(ys),max(ys),max(zs)-min(zs))
        flux+=u[0]*a;exact+=q;area+=a;max_face_error=max(max_face_error,abs(f+u[0]*a)/max(abs(f),1e-30))
        strips.append((min(ys),max(ys)))
    strips.sort()
    if any(abs(a[1]-b[0])>1e-12 for a,b in zip(strips,strips[1:])):raise ValueError('inlet gap/overlap')
    native_flux=-sum(phi);bias=flux/exact-1
    match=abs(native_flux-flux)/exact
    nominal_nu=float(dictionary(case/'constant/transportProperties')['nu'][-1])
    passed=abs(area/1e-4-1)<=1e-10 and abs(exact/1e-4-1)<=1e-10 and match<=POLICY['inlet_flux_match_max'] and max_face_error<=POLICY['inlet_flux_match_max']
    return {'passed':passed,'area_m2':area,'analytic_flux_m3_s':exact,'velocity_area_flux_m3_s':flux,
            'native_phi_flux_m3_s':native_flux,'relative_bias':bias,'phi_match_relative':match,
            'max_face_phi_match_relative':max_face_error,'effective_reynolds':native_flux/area*.02/nominal_nu,
            'faces':len(ids),'midpoint_bias_prediction':1/(2*len(ids)**2)}


def wall_check(case,mesh,iteration):
    U=field_dictionary(case/str(iteration)/'U');bc=U['boundaryField']
    turbulence=dictionary(case/'constant/turbulenceProperties')
    laminar=turbulence['simulationType']==['laminar']
    no_slip=all(bc[p]['type']==['noSlip'] or bc[p]['type']==['fixedValue'] and all(all(abs(x)<1e-14 for x in v) for v in field_values(bc[p]['value'],len(mesh['ranges'][p]),True)) for p in ('lowerWall','upperWall'))
    empty=bc['frontAndBack']['type']==['empty']
    velocity=field_values(U['internalField'],mesh['cells'],True);centres={}
    for i,c in enumerate(mesh['centres']):
        if abs(c[2])<1e-12:centres[mesh['owner'][i]]=(c[0],c[1])
    if len(centres)!=mesh['cells']:raise ValueError('not single-layer planar mesh')
    columns={}
    for cell,(x,y) in centres.items():columns.setdefault(round(x,10),[]).append((y,cell))
    for column in columns.values():column.sort()
    nu=float(dictionary(case/'constant/transportProperties')['nu'][-1]);first=[];quad=[];y1s=[];ratios=[]
    for face in mesh['ranges']['lowerWall']:
        x,y,_=mesh['centres'][face]
        if abs(y)>1e-12 or x<=0:continue
        owner=mesh['owner'][face];xc,y1=centres[owner];column=columns[round(x,10)]
        if abs(xc-x)>1e-10 or column[0][1]!=owner or len(column)<2:raise ValueError('wall stencil alignment')
        y2,second=column[1]
        first.append((x/.01,nu*velocity[owner][0]/y1))
        quad.append((x/.01,nu*wall_gradient(y1,y2,velocity[owner][0],velocity[second][0])))
        y1s.append(y1);ratios.append(y2/y1)
    return {'passed':laminar and no_slip and empty,'laminar':laminar,'no_slip':no_slip,'empty_2d':empty,
            'first_cell_x_over_h':crossing(sorted(first)),'quadratic_x_over_h':crossing(sorted(quad)),
            'first_wall_distance_m':[min(y1s),max(y1s)],'y2_over_y1':[min(ratios),max(ratios)],
            'diagnostic_only':True,'method':'quadratic du/dy on actual unequal wall distances, no wall function'}


def native_qoi(case,mesh,iteration):
    data=field_dictionary(case/str(iteration)/'wallShearStress')
    if data['dimensions']!=[['0','2','-2','0','0','0','0']]:raise ValueError('shear dimensions')
    ids=mesh['ranges']['lowerWall'];vals=field_values(data['boundaryField']['lowerWall']['value'],len(ids),True)
    curve=sorted((mesh['centres'][i][0]/.01,-v[0]) for i,v in zip(ids,vals) if abs(mesh['centres'][i][1])<1e-10 and mesh['centres'][i][0]>0)
    return {'iteration':iteration,'x_over_h':crossing(curve),'curve':curve}


def reduce(work,config):
    case=work/'case';mesh=mesh_data(case);log=(work/'log.checkMesh').read_text()
    if mesh['cells']!=config['expected_cells'] or 'Mesh OK.' not in log or not re.search(r'Number of regions:\s+1\b',log):raise ValueError('native mesh invalid')
    bounds=[[min(p[d] for p in mesh['points']),max(p[d] for p in mesh['points'])] for d in range(3)]
    expected=[[-config['upstream_h']*.01,config['downstream_h']*.01],[0,.02],[0,.01]]
    if any(abs(a-b)>1e-10 for row,other in zip(bounds,expected) for a,b in zip(row,other)):raise ValueError('domain bounds')
    convergence=residuals((work/'log.simpleFoam').read_text());it=convergence['iteration'];final=convergence['final']
    times=sorted(int(p.name) for p in case.iterdir() if p.name.isdecimal() and int(p.name)>0 and (p/'wallShearStress').is_file())
    if len(times)<2 or times[-1]!=it:raise ValueError('need two saved native fields ending at convergence')
    qoi=native_qoi(case,mesh,it);prev=native_qoi(case,mesh,times[-2]);change=abs(qoi['x_over_h']-prev['x_over_h'])/qoi['x_over_h']
    inlet=inlet_check(case,mesh,it);wall=wall_check(case,mesh,it)
    wall['relative_native_gap']=abs(wall['quadratic_x_over_h']-qoi['x_over_h'])/qoi['x_over_h']
    data=field_dictionary(case/str(it)/'phi');flux={p:sum(field_values(data['boundaryField'][p]['value'],len(ids))) for p,ids in mesh['ranges'].items() if p!='frontAndBack'}
    imbalance=abs(sum(flux.values()))/abs(flux['inlet']);leak=(abs(flux['lowerWall'])+abs(flux['upperWall']))/abs(flux['inlet'])
    native_log=(work/'log.simpleFoam').read_text()
    checks={'native_convergence':f'SIMPLE solution converged in {it} iterations' in native_log and '\nEnd\n' in native_log,
            'strict_residuals':final['p']<=POLICY['p_residual_max'] and max(final['Ux'],final['Uy'])<=POLICY['U_residual_max'],
            'qoi_stable':change<=POLICY['qoi_change_max'],'mass_conserved':imbalance<=POLICY['mass_imbalance_max'] and leak<1e-8,
            'inlet_verified':inlet['passed'],'wall_contract':wall['passed']}
    return {'valid':all(checks.values()),'checks':checks,'qoi':qoi,'convergence':convergence,'relative_change':change,
            'previous_iteration':times[-2],'previous_qoi':prev['x_over_h'],'mesh':{'cells':mesh['cells'],'bounds':bounds},
            'mass':{'relative_imbalance':imbalance,'wall_leak':leak,'flux':flux},'inlet':inlet,'wall':wall}


def run_case(root,cid,config,source,kind='fourth',face_average=False):
    work=root/cid
    if work.exists():raise ValueError('output exists; retained: '+str(work))
    source=source.resolve();origin=json.loads((source/'result.json').read_text())
    verify_case(source,origin)
    work.mkdir(parents=True);started=time.monotonic();row={'id':cid,'config':config,'kind':kind,'valid':False,'status':'running','steps':[]}
    row['origin']={'path':str(source),'result_sha256':sha(source/'result.json'),'evidence_sha256':sha(source/'evidence.json')}
    row['source_sha256']=sha(__file__);row['policy']=POLICY;save(work/'running.json',row)
    try:
        actual=write_case(work/'case',config['scale'],config['upstream_h'],config['downstream_h'],config['reynolds'])
        if actual!=config:raise ValueError('config mismatch')
        # Store exact generated inputs before native mapping. Source is mounted read-only.
        shutil.copytree(work/'case',work/'generated-inputs')
        for step in ('blockMesh','checkMesh','mapFields'):
            row['steps'].append(native(work,step,source/'case' if step=='mapFields' else None,started+14400))
        for name in ('U','p'):
            p=work/'case/0'/name;generated=(work/'generated-inputs/0'/name).read_text()
            text=p.read_text();p.write_text(text[:text.index('boundaryField')]+generated[generated.index('boundaryField'):])
        if face_average:
            n=20*config['scale'];p=work/'case/0/U';text=p.read_text();prefix,tail=text.split('boundaryField',1)
            values='\n'.join(f'({area_integral(.01+i*.01/n,.01+(i+1)*.01/n,.01)/(1e-4/n):.14g} 0 0)' for i in range(n))
            tail,count=re.subn(r'value nonuniform List<vector>\s*'+str(n)+r'\s*\(.*?\);',f'value nonuniform List<vector>\n{n}\n(\n{values}\n);',tail,flags=re.S)
            if count!=1:raise ValueError('face average boundary replacement')
            p.write_text(prefix+'boundaryField'+tail)
        shutil.copytree(work/'case/0',work/'mapped-initial-fields')
        row['steps'].append(native(work,'simpleFoam',deadline=started+14400))
        row.update(reduce(work,config));row['status']='complete'
        if kind=='bridge':
            row['bridge_relative_change']=abs(row['qoi']['x_over_h']-origin['qoi']['x_over_h'])/origin['qoi']['x_over_h']
            row['bridge_passed']=row['valid'] and row['bridge_relative_change']<=POLICY['bridge_qoi_change_max']
    except Exception as exc:row.update(status='failed',error=str(exc))
    row['seconds']=time.monotonic()-started;row['evidence']=evidence(work);save(work/'result.json',row)
    print(json.dumps({k:row.get(k) for k in ('id','status','valid','seconds','error','bridge_relative_change','bridge_passed')}) ,flush=True)
    return row


def expansion_allowed(data):
    """Pure complete-matrix check; native provenance additionally checked by CLI."""
    try:
        rows=data['rows'];groups=data['groups']
        return data['reynolds']==100 and len(rows)==16 and {(r['config']['upstream_h'],r['config']['downstream_h'],r['config']['scale']) for r in rows}=={(u,d,s) for u,d in DOMAINS for s in (1,2,4,8)} and all(r['valid'] for r in rows) and len(groups)==4 and all(g['gci']['applicable'] and g['gci']['fine_gci']<=POLICY['fine_gci_max'] for g in groups) and data['fine_domain_effect']<=POLICY['fine_domain_effect_max'] and data['diagnostics_passed'] and data['bridges_passed']
    except (KeyError,TypeError,ValueError):return False


def main():
    p=argparse.ArgumentParser();p.add_argument('command',choices=['bridges','fourth','inlet-pair']);p.add_argument('--out',type=Path,required=True);p.add_argument('--prior',type=Path,required=True);a=p.parse_args();a.out.mkdir(exist_ok=True,parents=True)
    if a.command=='fourth':
        bridges=[json.loads((a.out/f'bridge-u5-d{d}/result.json').read_text()) for d in (30,60)]
        if not all(r.get('bridge_passed') for r in bridges):raise ValueError('bridge failed')
    jobs=[]
    domains=DOMAINS if a.command=='fourth' else [(5,30),(5,60)] if a.command=='bridges' else [(5,30)]
    for u,d in domains:
        scale=8 if a.command=='fourth' else 4
        config={'scale':scale,'upstream_h':u,'downstream_h':d,'reynolds':100,'expected_cells':(5*u+2*(140+(33 if d==60 else 0)))*20*scale**2,'near_step_dx_h':.1/scale,'spanwise_layers':1,'grading_sections':[[10,100,1],[20,40,4]]+([[30,33,1]] if d==60 else [])}
        cid=f're100-u{u}-d{d}-g8' if a.command=='fourth' else f'bridge-u{u}-d{d}' if a.command=='bridges' else 'inlet-face-average-u5-d30-g4'
        jobs.append((a.out,cid,config,a.prior/f're100-u{u}-d{d}-g4','bridge' if a.command=='bridges' else a.command,a.command=='inlet-pair'))
    with ThreadPoolExecutor(max_workers=2) as pool:list(pool.map(lambda args:run_case(*args),jobs))

if __name__=='__main__':main()
