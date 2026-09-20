"""Continue a wall-time-limited study in a new identity, preserving the failed attempt."""
import argparse
import json
from pathlib import Path
import re
import shutil
import sys
import time

ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT))
from studies.cfd_step_sensitivity import sha, save, verify_case, reduce, evidence, analyze
from runners.solvers.cfd_step_runtime import native_step


def join_logs(initial,continued,checkpoint):
    """Preserve complete native history only through the actual restart checkpoint."""
    chunks=re.split(r'(?m)(?=^Time = \d+(?:s)?\s*$)',initial)
    kept=[];seen=[]
    for chunk in chunks:
        m=re.match(r'Time = (\d+)',chunk)
        if m and int(m[1])<=checkpoint:
            if not all('Solving for '+name+',' in chunk for name in ('Ux','Uy','p')):
                raise ValueError('Incomplete source iteration before restart checkpoint')
            kept.append(chunk);seen.append(int(m[1]))
    times=[int(v) for v in re.findall(r'(?m)^Time = (\d+)(?:s)?\s*$',continued)]
    if not seen or seen[-1]!=checkpoint or not times or times[0]!=checkpoint+1:
        raise ValueError('Native logs do not meet at the declared checkpoint')
    return '// DERIVED: initial native log through checkpoint, then continued native log.\n'+''.join(kept)+'\n'+continued


def continue_case(source,out):
    source=Path(source).resolve();out=Path(out).resolve()
    row=json.loads((source/'result.json').read_text());verify_case(source,row)
    if row['status']!='failed' or not any(s.get('timeout') for s in row['native_steps']):
        raise ValueError('Only an archived native timeout is eligible for continuation')
    checkpoints=sorted(int(p.name) for p in (source/'case').iterdir() if p.is_dir() and p.name.isdecimal() and int(p.name)>0 and all((p/name).is_file() for name in ('U','p','phi','wallShearStress')))
    if not checkpoints:raise ValueError('No complete native checkpoint; retain failure and use a fresh cold run')
    checkpoint=checkpoints[-1]
    out.mkdir(parents=True,exist_ok=False)
    def ignore_after_checkpoint(directory,names):
        return [name for name in names if Path(directory)==source/'case' and name.isdecimal() and int(name)>checkpoint]
    shutil.copytree(source/'case',out/'case',ignore=ignore_after_checkpoint)
    shutil.copytree(source/'case'/str(checkpoint),out/'restart-inputs')
    for name in ('config.json','log.blockMesh','log.checkMesh'):shutil.copyfile(source/name,out/name)
    shutil.copyfile(source/'log.simpleFoam',out/'log.simpleFoam.initial')
    control=out/'case/system/controlDict';old=control.read_text()
    updated,count=re.subn(r'startFrom\s+startTime\s*;','startFrom       latestTime;',old)
    if count!=1:raise ValueError('Source restart contract changed')
    control.write_text(updated)
    origin={'source_directory':str(source),'result_sha256':sha(source/'result.json'),
            'evidence_sha256':sha(source/'evidence.json'),'checkpoint':checkpoint,
            'checkpoint_hashes':{name:sha(source/'case'/str(checkpoint)/name) for name in ('U','p','phi','wallShearStress')},
            'extra_wall_limit_s':1800,'control_change':'startFrom startTime -> latestTime',
            'source_identity':row['identity']}
    identity={'protocol':'comacbench.cfd-study-continuation.v1','source_sha256':sha(__file__),'origin':origin}
    shutil.copyfile(__file__,out/'continuation-source.py');save(out/'continuation.json',identity)
    result={'id':row['id'],'identity':identity,'config':row['config'],'status':'running','valid':False,'native_steps':[]}
    started=time.monotonic();deadline=started+1800
    try:
        for command in ('checkMesh','simpleFoam'):
            step=native_step(out,command,deadline);result['native_steps'].append(step)
            if step['exit']!=0 or step['timeout']:raise ValueError(command+' failed or timed out during continuation')
        (out/'log.simpleFoam').rename(out/'log.simpleFoam.continued')
        combined=join_logs((out/'log.simpleFoam.initial').read_text(),(out/'log.simpleFoam.continued').read_text(),checkpoint)
        (out/'log.simpleFoam').write_text(combined)
        result.update(reduce(out,row['config']));result['status']='complete'
    except Exception as exc:result.update(status='failed',error=str(exc))
    result['seconds']=time.monotonic()-started
    result['total_attempt_seconds']=row['seconds']+result['seconds']
    result['evidence']=evidence(out);save(out/'result.json',result)
    print(json.dumps({k:result.get(k) for k in ('id','status','valid','seconds','error')},ensure_ascii=False))
    return result


def verify_continuation(work,row):
    identity=row['identity'];origin=identity['origin'];source=Path(origin['source_directory'])
    if sha(work/'continuation-source.py')!=identity['source_sha256']:raise ValueError('Continuation source drift')
    if sha(source/'result.json')!=origin['result_sha256'] or sha(source/'evidence.json')!=origin['evidence_sha256']:raise ValueError('Initial attempt drift')
    initial=json.loads((source/'result.json').read_text());verify_case(source,initial)
    if initial['identity']!=origin['source_identity'] or initial['config']!=row['config']:raise ValueError('Continuation identity/config mismatch')
    if not any(s.get('timeout') for s in initial['native_steps']):raise ValueError('Source was not a native timeout')
    if sha(work/'log.simpleFoam.initial')!=sha(source/'log.simpleFoam'):raise ValueError('Copied initial native log drift')
    for name,digest in origin['checkpoint_hashes'].items():
        if sha(work/'restart-inputs'/name)!=digest or sha(source/'case'/str(origin['checkpoint'])/name)!=digest:raise ValueError('Restart input snapshot changed')
    for name in ('0/U','0/p','system/fvSchemes','system/fvSolution','constant/transportProperties'):
        if sha(work/'case'/name)!=sha(source/'case'/name):raise ValueError('Numerical/physical settings changed on restart')
    for p in (source/'case/constant/polyMesh').iterdir():
        if p.is_file() and sha(work/'case/constant/polyMesh'/p.name)!=sha(p):raise ValueError('Restart mesh changed')
    expected=re.sub(r'startFrom\s+startTime\s*;','startFrom       latestTime;',(source/'case/system/controlDict').read_text())
    if (work/'case/system/controlDict').read_text()!=expected:raise ValueError('Unexpected control change')
    verify_case(work,row)
    if row['status']=='complete':
        combined=join_logs((work/'log.simpleFoam.initial').read_text(),(work/'log.simpleFoam.continued').read_text(),origin['checkpoint'])
        if (work/'log.simpleFoam').read_text()!=combined:raise ValueError('Derived convergence log drift')


def resolve(source,out,continuations):
    source=Path(source).resolve();out=Path(out).resolve();protocol=json.loads((source/'protocol.json').read_text())
    overrides={}
    for directory in continuations:
        work=Path(directory).resolve();row=json.loads((work/'result.json').read_text());verify_continuation(work,row)
        if not row['valid'] or row['status']!='complete':raise ValueError('Continuation has not passed convergence gates')
        if Path(row['identity']['origin']['source_directory']).parent!=source:raise ValueError('Continuation belongs to another study')
        if row['id'] in overrides:raise ValueError('Duplicate case override')
        overrides[row['id']]=work
    if not set(overrides)<=set(protocol['case_ids']):raise ValueError('Unexpected continuation case')
    out.mkdir(parents=True,exist_ok=False);origins={}
    for cid in protocol['case_ids']:
        target=overrides.get(cid,source/cid);row=json.loads((target/'result.json').read_text());verify_case(target,row)
        if not row['valid']:raise ValueError('Unresolved case: '+cid)
        (out/cid).symlink_to(target,target_is_directory=True)
        origins[cid]={'directory':str(target),'result_sha256':sha(target/'result.json')}
    save(out/'protocol.json',{'protocol':'comacbench.cfd-study-resolution.v1','reynolds':protocol['reynolds'],
                            'initial_study':str(source),'initial_protocol_sha256':sha(source/'protocol.json'),
                            'case_ids':protocol['case_ids'],'configs':protocol['configs'],'case_origins':origins})
    return analyze(out)


if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('command',choices=['continue','resolve']);p.add_argument('--source',required=True,type=Path);p.add_argument('--out',required=True,type=Path);p.add_argument('--continuations',nargs='*',default=[],type=Path);a=p.parse_args()
    if a.command=='continue':continue_case(a.source,a.out)
    else:resolve(a.source,a.out,a.continuations)
