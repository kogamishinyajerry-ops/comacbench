"""Reproducible native CFD sensitivity experiment; never changes benchmark scores."""
import argparse
from concurrent.futures import ThreadPoolExecutor
import fcntl
import hashlib
import json
import math
from pathlib import Path
import re
import shutil
import sys
import time

ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT))
from runners.solvers.cfd_profile import TEMPLATES
from runners.solvers.cfd_step_runtime import environment, native_step, WALL_SHEAR
from runners.solvers.backward_step import mesh_data, mass_balance, reattachment, residuals
from runners.solvers.foam_text import dictionary, field_values
from comacbench.__main__ import engine_identity

DOMAINS=((5,30),(10,30),(5,60),(10,60))
REFERENCES={100:2.922,200:4.982}
POLICY={'fine_gci_max':.005,'fine_domain_effect_max':.0025,'qoi_change_max':1e-4,
        'mass_imbalance_max':1e-6,'p_residual_max':1e-8,'U_residual_max':1e-9}


def sha(path):return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def save(path,data):
    path=Path(path);tmp=path.with_suffix(path.suffix+'.tmp')
    tmp.write_text(json.dumps(data,ensure_ascii=False,indent=2,allow_nan=False)+'\n');tmp.replace(path)


def grid_convergence(values, r=2):
    """Coarse, medium, fine; reject oscillation/flatness/divergence explicitly."""
    if len(values)!=3 or not all(isinstance(v,(int,float)) and math.isfinite(v) for v in values) or r<=1:
        return {'applicable':False,'reason':'need three finite values and r > 1'}
    coarse,medium,fine=values;d0=medium-coarse;d1=fine-medium
    if d0*d1<=0 or abs(d1)>=abs(d0) or fine==0 or medium==0:
        return {'applicable':False,'reason':'non-monotonic, flat or non-converging sequence'}
    p=math.log(abs(d0/d1))/math.log(r);den=r**p-1
    fine_gci=1.25*abs(d1/fine)/den;medium_gci=1.25*abs(d0/medium)/den
    return {'applicable':True,'refinement_ratio':r,'observed_order':p,'extrapolated':fine+d1/den,
            'fine_gci':fine_gci,'medium_gci':medium_gci,'asymptotic_ratio':medium_gci/(r**p*fine_gci),
            'note':'Three-point fitted ratio is not independent proof of asymptotic convergence.'}


def write_case(case,scale,upstream,downstream,reynolds):
    if scale not in (1,2,4) or (upstream,downstream) not in DOMAINS or reynolds not in REFERENCES:
        raise ValueError('unsupported declared study parameters')
    case=Path(case);files=dict(TEMPLATES);ny=20*scale
    nx_up=5*upstream*scale;nx_down=(140+(33 if downstream==60 else 0))*scale
    mesh=files['system/blockMeshDict'].replace('-0.05',format(-upstream*.01,'.12g')).replace('0.30',format(downstream*.01,'.12g'))
    mesh=mesh.replace('(25 20 1)',f'({nx_up} {ny} 1)').replace('(140 20 1)',f'({nx_down} {ny} 1)')
    sections=[(10,100,1),(20,40,4)]+([(30,33,1)] if downstream==60 else [])
    grading='\n'.join(f'({length/downstream:.15g} {cells*scale/nx_down:.15g} {ratio})' for length,cells,ratio in sections)
    mesh,n=re.subn(r'\(0\.333333 0\.714286 1\)\s*\(0\.666667 0\.285714 4\)',grading,mesh)
    if n!=2:raise ValueError('public template grading changed')
    files['system/blockMeshDict']=mesh
    velocities='\n'.join(f'({6*((i+.5)/ny)*(1-(i+.5)/ny):.14g} 0 0)' for i in range(ny))
    files['0/U'],n=re.subn(r'value nonuniform List<vector>\s*20\s*\(.*?\);',f'value nonuniform List<vector>\n{ny}\n(\n{velocities}\n);',files['0/U'],flags=re.S)
    if n!=1:raise ValueError('public inlet template changed')
    files['constant/transportProperties']=files['constant/transportProperties'].replace('2e-4',format(.02/reynolds,'.14g'))
    files['system/controlDict']=files['system/controlDict'].replace('endTime         2000','endTime         30000').replace('writeInterval   100','writeInterval   500')+WALL_SHEAR
    solution=files['system/fvSolution']
    for old,new in [('1e-7','1e-10'),('1e-8','1e-11'),('1e-5','1e-8'),('1e-6','1e-9')]:solution=solution.replace(old,new)
    files['system/fvSolution']=solution
    for name,content in files.items():
        p=case/name;p.parent.mkdir(parents=True,exist_ok=True);p.write_text(content)
    return {'scale':scale,'upstream_h':upstream,'downstream_h':downstream,'reynolds':reynolds,
            'expected_cells':(nx_up+2*nx_down)*ny,'near_step_dx_h':.1/scale,
            'spanwise_layers':1,'grading_sections':[list(s) for s in sections]}


def inspect_mesh(case,config,log):
    mesh=mesh_data(case)
    if mesh['cells']!=config['expected_cells'] or 'Mesh OK.' not in log or not re.search(r'Number of regions:\s+1\b',log):
        raise ValueError('native mesh count/quality/region mismatch')
    points=mesh['points'];bounds=[[min(p[d] for p in points),max(p[d] for p in points)] for d in range(3)]
    expected=[[-config['upstream_h']*.01,config['downstream_h']*.01],[0,.02],[0,.01]]
    if any(abs(a-b)>1e-10 for row,other in zip(bounds,expected) for a,b in zip(row,other)):raise ValueError('native domain mismatch')
    centres=mesh['centres'];ids=mesh['ranges']['inlet']
    v=field_values(dictionary(case/'0/U')['boundaryField']['inlet']['value'],len(ids),True)
    for i,value in zip(ids,v):
        eta=(centres[i][1]-.01)/.01
        if abs(value[0]-6*eta*(1-eta))>1e-8 or abs(value[1])+abs(value[2])>1e-12:raise ValueError('native inlet face/profile mismatch')
    near=sorted(centres[i][0]/.01 for i in mesh['ranges']['lowerWall'] if abs(centres[i][1])<1e-10 and 0<centres[i][0]<.1)
    expected_x=[(i+.5)*.1/config['scale'] for i in range(100*config['scale'])]
    if len(near)!=len(expected_x) or max(abs(a-b) for a,b in zip(near,expected_x))>1e-6:raise ValueError('near-step mesh changed with domain length')
    return mesh,{'cells':mesh['cells'],'bounds_m':bounds,'inlet_faces':len(ids),'near_wall_x_h':near}


def reduce(work,config):
    case=work/'case';mesh,info=inspect_mesh(case,config,(work/'log.checkMesh').read_text())
    convergence=residuals((work/'log.simpleFoam').read_text());final=convergence['final']
    times=sorted(int(p.name) for p in case.iterdir() if p.is_dir() and p.name.isdecimal() and int(p.name)>0 and (p/'wallShearStress').is_file())
    if len(times)<2 or times[-1]!=convergence['iteration']:raise ValueError('need two native wall fields ending at converged iteration')
    last=reattachment(case,times[-1],mesh);previous=reattachment(case,times[-2],mesh)
    change=abs(last['x_over_h']-previous['x_over_h'])/abs(last['x_over_h'])
    mass=mass_balance(case,times[-1],mesh)
    checks={'native_convergence':convergence['passed'],
            'strict_residuals':final['p']<=POLICY['p_residual_max'] and max(final['Ux'],final['Uy'])<=POLICY['U_residual_max'],
            'qoi_stable':change<=POLICY['qoi_change_max'],
            'mass_conserved':mass['passed'] and mass['relative_imbalance']<=POLICY['mass_imbalance_max']}
    reference=REFERENCES[config['reynolds']]
    return {'valid':all(checks.values()),'checks':checks,'mesh':info,'convergence':convergence,'mass':mass,
            'qoi':last,'previous_qoi':previous['x_over_h'],'previous_iteration':times[-2],
            'relative_change':change,'reference':reference,'relative_error':abs(last['x_over_h']-reference)/reference}


def evidence(work):
    files={}
    for p in sorted(work.rglob('*')):
        if p.is_file() and p.name not in {'result.json','evidence.json'}:
            files[str(p.relative_to(work))]={'sha256':sha(p),'bytes':p.stat().st_size}
    save(work/'evidence.json',{'protocol':'comacbench.cfd-study-evidence.v1','files':files})
    return {'manifest_sha256':sha(work/'evidence.json'),'file_count':len(files)}


def run_case(out,config,identity):
    cid=f"re{config['reynolds']}-u{config['upstream_h']}-d{config['downstream_h']}-g{config['scale']}"
    work=out/cid;result_file=work/'result.json'
    if result_file.exists():
        row=json.loads(result_file.read_text())
        if row.get('identity')!=identity or row['config']!=config:raise ValueError('case identity mismatch: '+cid)
        verify_case(work,row);return row
    if work.exists():raise ValueError('unfinished directory retained; use a fresh --out: '+str(work))
    work.mkdir();save(work/'config.json',config)
    row={'id':cid,'identity':identity,'config':config,'status':'running','valid':False,'native_steps':[]}
    started=time.monotonic();deadline=started+1800
    try:
        generated=write_case(work/'case',config['scale'],config['upstream_h'],config['downstream_h'],config['reynolds'])
        if generated!=config:raise ValueError('generator identity changed')
        for name in ('blockMesh','checkMesh','simpleFoam'):
            step=native_step(work,name,deadline);row['native_steps'].append(step)
            if step['exit']!=0 or step['timeout']:raise ValueError(name+' failed or timed out')
            if name=='checkMesh':inspect_mesh(work/'case',config,(work/'log.checkMesh').read_text())
        row.update(reduce(work,config));row['status']='complete'
    except Exception as exc:
        row['status']='failed';row['error']=str(exc)
    row['seconds']=time.monotonic()-started;row['evidence']=evidence(work);save(result_file,row)
    print(json.dumps({'id':cid,'status':row['status'],'valid':row['valid'],'seconds':round(row['seconds'],2),
                      'qoi':row.get('qoi',{}).get('x_over_h'),'error':row.get('error')},ensure_ascii=False),flush=True)
    return row


def verify_case(work,row):
    p=work/'evidence.json'
    if sha(p)!=row['evidence']['manifest_sha256']:raise ValueError('evidence manifest drift')
    for name,item in json.loads(p.read_text())['files'].items():
        if sha(work/name)!=item['sha256']:raise ValueError('native artifact drift: '+name)
    if row['status']=='complete':
        fresh=reduce(work,row['config'])
        if fresh['valid']!=row['valid'] or fresh['qoi']['x_over_h']!=row['qoi']['x_over_h']:raise ValueError('QoI reduction mismatch')


def analyze(out):
    protocol=json.loads((out/'protocol.json').read_text())
    rows=[json.loads((out/cid/'result.json').read_text()) for cid in protocol['case_ids']]
    for row in rows:verify_case(out/row['id'],row)
    valid=all(row['valid'] and row['status']=='complete' for row in rows)
    groups=[]
    for up,down in DOMAINS:
        group=sorted((r for r in rows if r['config']['upstream_h']==up and r['config']['downstream_h']==down),key=lambda r:r['config']['scale'])
        if len(group)==3:
            gci=grid_convergence([r['qoi']['x_over_h'] for r in group]) if all(r.get('qoi') for r in group) else {'applicable':False,'reason':'missing valid result'}
            groups.append({'upstream_h':up,'downstream_h':down,'gci':gci})
    fine=[r for r in rows if r['config']['scale']==4 and r.get('qoi')]
    ref=REFERENCES[protocol['reynolds']]
    domain=(max(r['qoi']['x_over_h'] for r in fine)-min(r['qoi']['x_over_h'] for r in fine))/ref if len(fine)>1 else None
    all_gci=bool(groups) and all(g['gci']['applicable'] and g['gci']['fine_gci']<=POLICY['fine_gci_max'] for g in groups)
    effects=[]
    for scale in (1,2,4):
        vals={(r['config']['upstream_h'],r['config']['downstream_h']):r['qoi']['x_over_h'] for r in rows if r['config']['scale']==scale and r.get('qoi')}
        if len(vals)==4:
            effects.append({'scale':scale,'inlet_at_d30':(vals[10,30]-vals[5,30])/ref,
                           'outlet_at_u5':(vals[5,60]-vals[5,30])/ref,
                           'interaction':(vals[10,60]-vals[10,30]-vals[5,60]+vals[5,30])/ref})
    gate=valid and all_gci and domain is not None and domain<=POLICY['fine_domain_effect_max']
    decision={'gate_passed':gate,'current_tolerance':.1,'suggested_tolerance':None,
              'status':'insufficient_evidence','policy':POLICY,'fine_domain_effect':domain}
    if gate:
        observed=max(r['relative_error'] for r in rows)
        gci_term=max(g['gci']['fine_gci']*next(r['qoi']['x_over_h'] for r in fine if r['config']['upstream_h']==g['upstream_h'] and r['config']['downstream_h']==g['downstream_h'])/ref for g in groups)
        iteration=max(r['relative_change']*r['qoi']['x_over_h']/ref for r in rows)
        allowance=observed+gci_term+domain+iteration+.0005/ref
        suggested=math.ceil(allowance/.005)*.005
        decision.update(status='study_screening_band',suggested_tolerance=suggested,
                        allowance_terms={'observed_error':observed,'fine_gci':gci_term,'domain':domain,'iteration':iteration,'reference_rounding':.0005/ref},
                        unrounded_allowance=allowance,
                        note='Conservative study screening policy, not a statistical confidence interval; old scores unchanged.')
    summary={'protocol':'comacbench.cfd-sensitivity-analysis.v1','reynolds':protocol['reynolds'],
             'protocol_sha256':sha(out/'protocol.json'),'results_sha256':{r['id']:sha(out/r['id']/'result.json') for r in rows},
             'case_count':len(rows),'valid_count':sum(r['valid'] for r in rows),'groups':groups,'domain_effects':effects,
             'tolerance_decision':decision,'rows':[{k:v for k,v in r.items() if k not in {'identity','convergence','qoi'}}|{'qoi':{k:v for k,v in r.get('qoi',{}).items() if k!='curve'}} for r in rows]}
    save(out/'analysis.json',summary)
    print(json.dumps({'cases':len(rows),'valid':sum(r['valid'] for r in rows),'decision':decision},ensure_ascii=False),flush=True)
    return summary


def main():
    parser=argparse.ArgumentParser();parser.add_argument('command',choices=['run','analyze','verify']);parser.add_argument('--out',required=True,type=Path)
    parser.add_argument('--reynolds',type=int,choices=[100,200],default=100);parser.add_argument('--prior-decision',type=Path)
    args=parser.parse_args();out=args.out.resolve()
    if args.command=='analyze':analyze(out);return
    if args.command=='verify':
        protocol=json.loads((out/'protocol.json').read_text())
        for cid in protocol['case_ids']:verify_case(out/cid,json.loads((out/cid/'result.json').read_text()))
        print(json.dumps({'verified':len(protocol['case_ids'])}));return
    prior=None
    if args.reynolds!=100:
        if not args.prior_decision:raise ValueError('Re=200 requires prior Re=100 tolerance decision')
        prior_doc=json.loads(args.prior_decision.read_text())
        if prior_doc['reynolds']!=100 or not prior_doc['tolerance_decision']['gate_passed']:raise ValueError('prior tolerance gate did not pass')
        prior={'path':str(args.prior_decision.resolve()),'sha256':sha(args.prior_decision)}
    identity={'engine':engine_identity(),'study_source':sha(__file__),'environment':environment(),'policy':POLICY,'prior_decision':prior}
    out.mkdir(parents=True,exist_ok=True)
    with (out/'.lock').open('a+') as lock:
        fcntl.flock(lock,fcntl.LOCK_EX|fcntl.LOCK_NB)
        configs=[]
        # Re=200 receives the same full factorial, only after the Re=100 gate.
        for up,down in DOMAINS:
            for scale in (1,2,4):
                configs.append({'scale':scale,'upstream_h':up,'downstream_h':down,'reynolds':args.reynolds,
                                'expected_cells':(5*up+2*(140+(33 if down==60 else 0)))*20*scale**2,
                                'near_step_dx_h':.1/scale,'spanwise_layers':1,
                                'grading_sections':[[10,100,1],[20,40,4]]+([[30,33,1]] if down==60 else [])})
        protocol={'identity':identity,'reynolds':args.reynolds,'configs':configs,
                  'case_ids':[f"re{args.reynolds}-u{c['upstream_h']}-d{c['downstream_h']}-g{c['scale']}" for c in configs]}
        if (out/'protocol.json').exists():
            if json.loads((out/'protocol.json').read_text())!=protocol:raise ValueError('protocol identity drift; use new --out')
        else:
            save(out/'protocol.json',protocol)
            for name in identity['engine']:
                dest=out/'frozen-source'/name;dest.parent.mkdir(parents=True,exist_ok=True);shutil.copyfile(ROOT/name,dest)
            shutil.copyfile(__file__,out/'frozen-source/cfd_step_sensitivity.py')
        with ThreadPoolExecutor(max_workers=2) as pool:
            list(pool.map(lambda c:run_case(out,c,identity),configs))
        analyze(out)


if __name__=='__main__':main()
