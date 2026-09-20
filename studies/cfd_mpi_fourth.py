"""Four-rank native continuation after verified unchanged-settings MPI bridges."""
from concurrent.futures import ThreadPoolExecutor
import json
from pathlib import Path
import shutil
import subprocess
import sys
import time
import uuid

ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT))
from studies.cfd_step_sensitivity import sha,save,evidence,verify_case
from studies.cfd_fourth_grid import IMAGE,POLICY,write_case,native,reduce
from studies.cfd_mpi_bridge import DECOMPOSE


def step(work,stage,deadline,times=None):
    commands={'decomposePar':'decomposePar -case /work/case -latestTime',
              'simpleFoam':'mpirun --allow-run-as-root --bind-to none -np 4 simpleFoam -parallel -case /work/case'}
    if stage=='reconstructPar':
        if len(times or [])!=2 or any(type(t)!=int or t<=0 for t in times) or times[0]>=times[1]:raise ValueError('invalid reconstruction times')
        commands[stage]='reconstructPar -case /work/case -time '+','.join(map(str,times))
    if stage not in commands:raise ValueError('unsupported native MPI command')
    name='comac-cfd-mpi-'+uuid.uuid4().hex
    cmd=['docker','run','--rm','--pull','never','--name',name,'--network','none','--platform','linux/amd64',
         '--cpus','4','--memory','4g','--pids-limit','256','-v',str(work.resolve())+':/work','-w','/work',
         '--entrypoint','bash',IMAGE,'-c','source /opt/openfoam10/etc/bashrc && '+commands[stage]]
    started=time.monotonic()
    try:
        with (work/('log.'+stage)).open('wb') as log:r=subprocess.run(cmd,stdout=log,stderr=subprocess.STDOUT,timeout=max(1,deadline-started))
        if r.returncode:raise RuntimeError(stage+' exit '+str(r.returncode))
    finally:subprocess.run(['docker','rm','-f',name],stdout=subprocess.DEVNULL,stderr=subprocess.DEVNULL,timeout=15)
    return {'stage':stage,'exit':r.returncode,'seconds':time.monotonic()-started,'command':cmd}


def run(out,cid,source,config=None):
    work=out/cid;source=source.resolve();base=json.loads((source/'result.json').read_text())
    if work.exists():raise ValueError('output exists')
    verify_case(source,base)
    restart=config is None;config=config or base['config'];started=time.monotonic();deadline=started+14400
    row={'id':cid,'config':config,'kind':'fourth','status':'running','valid':False,'steps':[],
         'source_sha256':sha(ROOT/'studies/cfd_fourth_grid.py'),'policy':POLICY,
         'parallel':{'source_sha256':sha(__file__),'ranks':4,'decompose_source_sha256':sha(ROOT/'studies/cfd_mpi_bridge.py')}}
    work.mkdir(parents=True)
    try:
        if restart:
            if base['status']!='interrupted_for_verified_mpi':raise ValueError('expected preserved serial attempt')
            row['origin']=base['origin'];row['continuation']=base['continuation']
            fields=('U','p','phi','wallShearStress');case=source/'case'
            checkpoint=max(int(p.name) for p in case.iterdir() if p.name.isdecimal() and int(p.name)>0 and all((p/f).is_file() for f in fields))
            def ignore(path,names):return [n for n in names if n.isdecimal() and int(n)>checkpoint] if Path(path)==case else []
            shutil.copytree(case,work/'case',ignore=ignore)
            for name in ('generated-inputs','mapped-initial-fields','restart-inputs'):shutil.copytree(source/name,work/name)
            for name in ('log.blockMesh','log.checkMesh','log.mapFields','log.simpleFoam.initial'):shutil.copyfile(source/name,work/name)
            shutil.copyfile(source/'log.simpleFoam',work/'log.simpleFoam.serial')
            shutil.copytree(case/str(checkpoint),work/'parallel-restart-inputs')
            row['parallel']['restart']={'source':str(source),'source_result_sha256':sha(source/'result.json'),
                                       'source_evidence_sha256':sha(source/'evidence.json'),'checkpoint':checkpoint,
                                       'fields':{f:sha(work/'parallel-restart-inputs'/f) for f in fields}}
        else:
            if not base['valid'] or base['status']!='complete':raise ValueError('initialization source must be converged')
            row['origin']={'path':str(source),'result_sha256':sha(source/'result.json'),'evidence_sha256':sha(source/'evidence.json')}
            actual=write_case(work/'case',config['scale'],config['upstream_h'],config['downstream_h'],config['reynolds'])
            if actual!=config:raise ValueError('configuration mismatch')
            shutil.copytree(work/'case',work/'generated-inputs')
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


def main():
    out=Path(sys.argv[1]).resolve();prior=Path(sys.argv[2]).resolve()
    verification=json.loads((out/'mpi-verification.json').read_text());speed=json.loads((out/'mpi-speed-check.json').read_text())
    if not verification['passed'] or not speed['passed']:raise ValueError('MPI adoption gates failed')
    jobs=[(out,f're100-u{u}-d30-g8',out/f'serial-attempts/re100-u{u}-d30-g8',None) for u in (5,10)]
    for u in (5,10):
        c={'scale':8,'upstream_h':u,'downstream_h':60,'reynolds':100,'expected_cells':(5*u+346)*1280,'near_step_dx_h':.0125,
           'spanwise_layers':1,'grading_sections':[[10,100,1],[20,40,4],[30,33,1]]}
        jobs.append((out,f're100-u{u}-d60-g8',prior/f're100-u{u}-d60-g4',c))
    with ThreadPoolExecutor(max_workers=2) as pool:list(pool.map(lambda args:run(*args),jobs))

if __name__=='__main__':main()
