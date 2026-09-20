"""Re=200 fine grids use v1 warm-start validation and frozen MPI execution."""
import json
from pathlib import Path
import shutil
import time
from studies.analyze_cfd_fourth_grid import verify_new
from studies.cfd_step_sensitivity import sha,save,evidence,DOMAINS
from studies.cfd_fourth_grid import POLICY,write_case,native,reduce
from studies.cfd_mpi_bridge import DECOMPOSE
from studies.cfd_mpi_fourth import step

ROOT=Path(__file__).resolve().parents[1]


def run(out,cid,source,config):
    out=Path(out).resolve();source=Path(source).resolve();work=out/cid
    if config.get('reynolds')!=200 or config.get('scale')!=8 or (config.get('upstream_h'),config.get('downstream_h')) not in DOMAINS:raise ValueError('Re=200 G3 configuration required')
    if work.exists():raise ValueError('output exists; retained')
    base,_=verify_new(source,out)
    expected=dict(config,scale=4,expected_cells=config['expected_cells']//4,near_step_dx_h=.025)
    if not base['valid'] or base['status']!='complete' or base['config']!=expected:raise ValueError('verified same-domain Re=200 G2 source required')
    started=time.monotonic();deadline=started+14400
    row={'id':cid,'config':config,'kind':'fourth','status':'running','valid':False,'steps':[],
         'source_sha256':sha(ROOT/'studies/cfd_fourth_grid.py'),'policy':POLICY,
         'origin':{'path':str(source),'result_sha256':sha(source/'result.json'),'evidence_sha256':sha(source/'evidence.json')},
         'parallel':{'source_sha256':sha(__file__),'ranks':4,'execution_source_sha256':sha(ROOT/'studies/cfd_mpi_fourth.py'),
                     'decompose_source_sha256':sha(ROOT/'studies/cfd_mpi_bridge.py')}}
    work.mkdir(parents=True)
    try:
        if write_case(work/'case',8,config['upstream_h'],config['downstream_h'],200)!=config:raise ValueError('configuration mismatch')
        shutil.copytree(work/'case',work/'generated-inputs');save(work/'running.json',row)
        for stage in ('blockMesh','checkMesh','mapFields'):row['steps'].append(native(work,stage,source/'case' if stage=='mapFields' else None,deadline))
        for field in ('U','p'):
            p=work/'case/0'/field;text=p.read_text();generated=(work/'generated-inputs/0'/field).read_text()
            p.write_text(text[:text.index('boundaryField')]+generated[generated.index('boundaryField'):])
        shutil.copytree(work/'case/0',work/'mapped-initial-fields')
        (work/'case/system/decomposeParDict').write_text(DECOMPOSE)
        row['parallel']['decompose_dict_sha256']=sha(work/'case/system/decomposeParDict');save(work/'running.json',row)
        for stage in ('decomposePar','simpleFoam'):row['steps'].append(step(work,stage,deadline))
        times=[]
        for rank in range(4):
            times.append(sorted(int(p.name) for p in (work/f'case/processor{rank}').iterdir() if p.name.isdecimal() and int(p.name)>0 and all((p/f).is_file() for f in ('U','p','phi','wallShearStress')))[-2:])
        if len(times[0])!=2 or any(t!=times[0] for t in times):raise ValueError('processor field times incomplete or inconsistent')
        row['steps'].append(step(work,'reconstructPar',deadline,times[0]));row['parallel']['reconstructed_times']=times[0]
        row.update(reduce(work,config));row['status']='complete'
    except Exception as exc:row.update(status='failed',error=str(exc))
    row['seconds']=time.monotonic()-started;row['evidence']=evidence(work);save(work/'result.json',row)
    print(json.dumps({k:row.get(k) for k in ('id','valid','status','seconds','error')}),flush=True)
    return row
