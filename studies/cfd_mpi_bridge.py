"""Native MPI execution bridge with unchanged physical and numerical settings."""
import json
from pathlib import Path
import shutil
import subprocess
import sys
import time
import uuid

ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT))
from studies.cfd_step_sensitivity import sha,save,evidence
from studies.cfd_fourth_grid import IMAGE,POLICY,reduce

DECOMPOSE='''FoamFile { version 2.0; format ascii; class dictionary; object decomposeParDict; }
numberOfSubdomains 4;
method simple;
simpleCoeffs { n (4 1 1); }
'''


def mpi_step(work,stage,times=None):
    choices={'decomposePar':'decomposePar -case /work/case -latestTime',
             'simpleFoam':'mpirun --allow-run-as-root --bind-to none -np 4 simpleFoam -parallel -case /work/case'}
    if stage=='reconstructPar':
        if not times or any(type(t)!=int or t<=0 for t in times):raise ValueError('invalid reconstruction times')
        choices[stage]='reconstructPar -case /work/case -time '+','.join(map(str,times))
    if stage not in choices:raise ValueError('unsupported MPI step')
    name='comac-cfd-mpi-'+uuid.uuid4().hex
    cmd=['docker','run','--rm','--pull','never','--name',name,'--network','none','--platform','linux/amd64',
         '--cpus','4','--memory','4g','--pids-limit','256','-v',str(work.resolve())+':/work','-w','/work',
         '--entrypoint','bash',IMAGE,'-c','source /opt/openfoam10/etc/bashrc && '+choices[stage]]
    started=time.monotonic()
    try:
        with (work/('log.'+stage)).open('wb') as log:r=subprocess.run(cmd,stdout=log,stderr=subprocess.STDOUT,timeout=1800)
        if r.returncode:raise RuntimeError(stage+' exit '+str(r.returncode))
    finally:subprocess.run(['docker','rm','-f',name],stdout=subprocess.DEVNULL,stderr=subprocess.DEVNULL,timeout=15)
    return {'stage':stage,'exit':r.returncode,'seconds':time.monotonic()-started,'command':cmd}


def bridge(source,work):
    source=source.resolve();work=work.resolve();base=json.loads((source/'result.json').read_text())
    if not base.get('bridge_passed'):raise ValueError('need validated original-settings bridge')
    if work.exists():raise ValueError('output exists')
    work.mkdir(parents=True);(work/'case').mkdir()
    for name in ('constant','system'):shutil.copytree(source/'case'/name,work/'case'/name)
    shutil.copytree(source/'mapped-initial-fields',work/'case/0')
    for name in ('generated-inputs','mapped-initial-fields'):shutil.copytree(source/name,work/name)
    for name in ('log.blockMesh','log.checkMesh','log.mapFields'):shutil.copyfile(source/name,work/name)
    (work/'case/system/decomposeParDict').write_text(DECOMPOSE)
    row={k:base[k] for k in ('config','origin','source_sha256','policy')}
    row.update(id=work.name,kind='bridge',status='running',valid=False,steps=[],
               parallel={'source_sha256':sha(__file__),'ranks':4,'replay_source':str(source),
                         'replay_result_sha256':sha(source/'result.json'),'decompose_dict_sha256':sha(work/'case/system/decomposeParDict')})
    started=time.monotonic();save(work/'running.json',row)
    try:
        for name in ('decomposePar','simpleFoam'):row['steps'].append(mpi_step(work,name))
        times=sorted(int(p.name) for p in (work/'case/processor0').iterdir() if p.name.isdecimal() and int(p.name)>0)
        if len(times)<2:raise ValueError('need two native processor field times')
        row['steps'].append(mpi_step(work,'reconstructPar',times[-2:]))
        row.update(reduce(work,row['config']));row['status']='complete'
        origin=json.loads((Path(row['origin']['path'])/'result.json').read_text())
        row['bridge_relative_change']=abs(row['qoi']['x_over_h']-origin['qoi']['x_over_h'])/origin['qoi']['x_over_h']
        row['bridge_passed']=row['valid'] and row['bridge_relative_change']<=POLICY['bridge_qoi_change_max']
    except Exception as exc:row.update(status='failed',error=str(exc))
    row['seconds']=time.monotonic()-started;row['evidence']=evidence(work);save(work/'result.json',row)
    print(json.dumps({k:row.get(k) for k in ('id','valid','status','seconds','bridge_relative_change','bridge_passed','error')}),flush=True)
    return row

if __name__=='__main__':bridge(Path(sys.argv[1]),Path(sys.argv[2]))
