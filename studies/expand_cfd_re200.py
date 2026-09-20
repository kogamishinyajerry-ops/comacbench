"""Re=200 execution is conditional on independently reproduced Re=100 evidence."""
import argparse
from concurrent.futures import ThreadPoolExecutor
import json
from pathlib import Path
import shutil
import sys

ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT))
from studies.analyze_cfd_fourth_grid import analyze as verify_re100,verify_new,decide,common_geometry,geometric_inlet
from studies.cfd_step_sensitivity import sha,save,DOMAINS
from studies.cfd_fourth_grid import run_case
from runners.solvers.backward_step import mesh_data


def require_parent(parent):
    parent=Path(parent).resolve();fresh=verify_re100(parent)
    if json.loads((parent/'analysis.json').read_text())!=fresh:raise ValueError('Re=100 saved analysis drift')
    if fresh['reynolds']!=100 or fresh['gate_passed'] is not True:raise ValueError('Re=100 scientific gate has not passed; no Re=200 execution')
    return {'path':str(parent),'analysis_sha256':sha(parent/'analysis.json'),'protocol_sha256':sha(parent/'protocol.json')}


def run(parent,out):
    parent=Path(parent).resolve();authorization=require_parent(parent)
    out=Path(out).resolve()
    if out.exists():raise ValueError('Re=200 output exists; retained')
    prior_protocol=json.loads((parent/'protocol.json').read_text())
    if prior_protocol['runner_source']!='studies/cfd_fourth_grid.py':raise ValueError('Only bridged original execution settings may expand')
    old=(parent/prior_protocol['prior']).resolve()
    protocol={k:prior_protocol[k] for k in ('execution_version','runner_source','grid_scales','domains','source_hashes','parallel_source','parallel_ranks')}
    protocol['source_hashes']=dict(protocol['source_hashes'],**{'studies/cfd_mpi_re200.py':sha(ROOT/'studies/cfd_mpi_re200.py')})
    protocol['parallel_source']='studies/cfd_mpi_re200.py'
    protocol.update(protocol='comacbench.cfd-re200.v1',reynolds=200,prior=str(old),parent_verified=authorization,
                    expansion_source_sha256=sha(__file__),spec_sha256=sha(ROOT/'docs/specs/cfd-re200-v1.md'))
    out.mkdir(parents=True)
    shutil.copytree(parent/'frozen-source',out/'frozen-source');shutil.copyfile(__file__,out/'frozen-source/expand_cfd_re200.py')
    shutil.copyfile(ROOT/'studies/cfd_mpi_re200.py',out/'frozen-source/studies/cfd_mpi_re200.py')
    shutil.copyfile(ROOT/'docs/specs/cfd-re200-v1.md',out/'frozen-source/docs/specs/cfd-re200-v1.md');save(out/'protocol.json',protocol)
    def job(u,d,scale,source):
        config={'scale':scale,'upstream_h':u,'downstream_h':d,'reynolds':200,'expected_cells':(5*u+2*(140+(33 if d==60 else 0)))*20*scale**2,
                'near_step_dx_h':.1/scale,'spanwise_layers':1,'grading_sections':[[10,100,1],[20,40,4]]+([[30,33,1]] if d==60 else [])}
        return out,f're200-u{u}-d{d}-g{scale}',config,source
    initial=[job(u,d,s,old/f're100-u{u}-d{d}-g{s}') for u,d in DOMAINS for s in (1,2,4)]
    with ThreadPoolExecutor(max_workers=2) as pool:results=list(pool.map(lambda args:run_case(*args),initial))
    if not all(r['valid'] for r in results):raise ValueError('Re=200 lower-grid matrix incomplete; no fine-grid expansion')
    fine=[job(u,d,8,out/f're200-u{u}-d{d}-g4') for u,d in DOMAINS]
    from studies.cfd_mpi_re200 import run as run_mpi
    with ThreadPoolExecutor(max_workers=2) as pool:list(pool.map(lambda args:run_mpi(args[0],args[1],args[3],args[2]),fine))


def analyze(out,verify=False):
    out=Path(out).resolve();protocol=json.loads((out/'protocol.json').read_text());parent=Path(protocol['parent_verified']['path'])
    if require_parent(parent)!=protocol['parent_verified']:raise ValueError('parent verification drift')
    if sha(__file__)!=protocol['expansion_source_sha256'] or sha(out/'frozen-source/expand_cfd_re200.py')!=protocol['expansion_source_sha256']:raise ValueError('expansion source drift')
    if sha(ROOT/'docs/specs/cfd-re200-v1.md')!=protocol['spec_sha256'] or sha(out/'frozen-source/docs/specs/cfd-re200-v1.md')!=protocol['spec_sha256']:raise ValueError('Re=200 specification drift')
    for name,digest in protocol['source_hashes'].items():
        if sha(ROOT/name)!=digest or sha(out/'frozen-source'/name)!=digest:raise ValueError('Re=200 frozen source drift: '+name)
    rows=[];count=0
    for u,d in DOMAINS:
        for s in (1,2,4,8):
            work=out/f're200-u{u}-d{d}-g{s}';r,n=verify_new(work,out);count+=n
            if r['config']['reynolds']!=200:raise ValueError('mixed Reynolds family')
            r['geometric_inlet']=geometric_inlet(work/'case',mesh_data(work/'case'),r['qoi']['iteration']);r['artifact_path']=str(work)
            r.pop('convergence',None);r['qoi'].pop('curve',None);rows.append(r)
    bridges=[json.loads((parent/f'bridge-u5-d{d}/result.json').read_text()) for d in (30,60)]
    data=decide(rows,bridges,200);data['parent_verified']=protocol['parent_verified'];data['expanded_re200']=True
    data['common_domain_geometry']=common_geometry(out,200);data['verification']={'passed':True,'native_files':count,'new_model_calls':0}
    data['provenance']={'protocol_sha256':sha(out/'protocol.json'),'analysis_source_sha256':sha(__file__),
                        'reconstruction_source_sha256':sha(ROOT/'studies/cfd_mpi_reconstruction.py'),
                        'result_hashes':{r['id']:sha(Path(r['artifact_path'])/'result.json') for r in rows}}
    if verify:
        if json.loads((out/'analysis.json').read_text())!=data:raise ValueError('Re=200 saved analysis differs')
    else:save(out/'analysis.json',data)
    print(json.dumps({'reynolds':200,'gate_passed':data['gate_passed'],'failed_gates':data['failed_gates']}))


def main():
    p=argparse.ArgumentParser();p.add_argument('command',choices=['run','analyze','verify','preflight']);p.add_argument('--parent',type=Path);p.add_argument('--out',type=Path,required=True);a=p.parse_args()
    if a.command in ('analyze','verify'):analyze(a.out,a.command=='verify')
    elif a.command=='preflight':print(json.dumps(require_parent(a.parent)))
    else:run(a.parent,a.out)

if __name__=='__main__':main()
