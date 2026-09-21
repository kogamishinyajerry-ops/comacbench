"""Native Re=300 matrix with frozen sources, bounded I/O and fail-closed replay."""
import argparse
from concurrent.futures import ThreadPoolExecutor
from studies._win_compat import fcntl
import json
from pathlib import Path
import shutil
import subprocess
import sys
import tempfile
import time
import uuid

ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT))
from studies.cfd_re300 import config_for,write_case,reduce,decide
from studies.cfd_step_sensitivity import sha,save,evidence,DOMAINS
from studies.cfd_fourth_grid import IMAGE,field_dictionary
from studies.cfd_mpi_bridge import DECOMPOSE
from studies.verify_cfd_primary_delivery import verify_files
from studies.analyze_cfd_fourth_grid import common_geometry

OWN=['studies/cfd_re300.py','studies/run_cfd_re300.py','studies/render_cfd_re300.py','tests/test_cfd_re300.py','docs/specs/cfd-re300-v1.md']


def identity(out):
    protocol=json.loads((out/'protocol.json').read_text())
    if protocol['identity']!='comacbench.cfd-re300.v1' or protocol['reference']!=6.751:raise ValueError('unexpected Re=300 identity')
    verify_files(ROOT,protocol['source_hashes']);verify_files(out/'frozen-source',protocol['source_hashes'])
    for path,digest in protocol['parent_hashes'].items():
        if sha(path)!=digest:raise ValueError('parent entry point drift: '+path)
    for record in protocol['parent_manifests']:
        path=Path(record['path'])
        if sha(path)!=record['sha256']:raise ValueError('parent delivery changed')
        verify_files(ROOT,json.loads(path.read_text())['files'])
    return protocol


def prepare(out,parent,legacy,preflight):
    if out.exists():raise ValueError('output exists; retained')
    old=json.loads((preflight/'legacy-parent-verify.log').read_text())
    fresh=json.loads((preflight/'primary-parent-verify.log').read_text().splitlines()[-1])
    analysis=json.loads((parent/'analysis.json').read_text())
    if old.get('reynolds')!=200 or not fresh.get('passed') or fresh['analysis_sha256']!=sha(parent/'analysis.json') or analysis['gate_passed'] is not True or len(analysis['rows'])!=16 or analysis['field_snapshots_verified']!=32:
        raise ValueError('complete independently replayed Re=200 v2 gate required')
    source_hashes=dict(json.loads((legacy/'protocol.json').read_text())['source_hashes'])
    source_hashes.update(json.loads((parent/'source-delivery.json').read_text())['files'])
    source_hashes.update({name:sha(ROOT/name) for name in OWN})
    manifests=[{'path':str(p/'delivery-manifest.json'),'sha256':sha(p/'delivery-manifest.json')} for p in (legacy,parent)]
    for record in manifests:verify_files(ROOT,json.loads(Path(record['path']).read_text())['files'])
    verify_files(ROOT,source_hashes)
    if shutil.disk_usage(out.parent).free<6*1024**3:raise ValueError('need >=6 GiB before creating study')
    protocol={'identity':'comacbench.cfd-re300.v1','reference':6.751,'parent':str(parent),'legacy':str(legacy),
              'parent_hashes':{str(p):sha(p) for p in [parent/'analysis.json',parent/'identity.json',parent/'completion-verification.json',legacy/'analysis.json',preflight/'legacy-parent-verify.log',preflight/'primary-parent-verify.log']},
              'parent_manifests':manifests,'source_hashes':source_hashes,'matrix':[f're300-u{u}-d{d}-g{s}' for u,d in DOMAINS for s in (1,2,4,8)],
              'purge_write':2,'max_concurrency':2,'native_deadline_seconds':14400,'minimum_start_free_bytes':6*1024**3,
              'stop_free_bytes':4*1024**3,'image':IMAGE,'new_model_calls':0,'allow_re400':False}
    out.mkdir(parents=True)
    for name in source_hashes:
        target=out/'frozen-source'/name;target.parent.mkdir(parents=True,exist_ok=True);shutil.copyfile(ROOT/name,target)
    save(out/'protocol.json',protocol);save(out/'parent-verification.json',fresh)
    return protocol


def native(work,stage,deadline,source=None,ranks=1,times=None):
    commands={'blockMesh':'blockMesh -case /work/case','checkMesh':'checkMesh -case /work/case',
              'mapFields':'mapFields -case /work/case -consistent -sourceTime latestTime /source',
              'decomposePar':'decomposePar -case /work/case -latestTime',
              'simpleFoam':'simpleFoam -case /work/case' if ranks==1 else 'mpirun --allow-run-as-root --bind-to none -np 4 simpleFoam -parallel -case /work/case'}
    if stage=='reconstructPar':
        if len(times or [])!=2 or any(type(t)!=int or t<=0 for t in times) or times[0]>=times[1]:raise ValueError('invalid reconstruction time pair')
        commands[stage]='reconstructPar -case /work/case -time '+','.join(map(str,times))
    if stage not in commands or ranks not in (1,4) or (stage=='mapFields')!=(source is not None):raise ValueError('undeclared native action')
    if shutil.disk_usage(work).free<4*1024**3:raise ValueError('disk reserve below 4 GiB')
    name='comac-re300-'+uuid.uuid4().hex
    cmd=['docker','run','--rm','--pull','never','--name',name,'--network','none','--platform','linux/amd64',
         '--cpus',str(2 if ranks==1 else 4),'--memory','4g','--pids-limit','256','-v',str(work)+':/work','-w','/work']
    if source:cmd+=['-v',str(source)+':/source:ro']
    cmd+=['--entrypoint','bash',IMAGE,'-c','source /opt/openfoam10/etc/bashrc && '+commands[stage]]
    started=time.monotonic();save(work/'native-active.json',{'stage':stage,'container':name,'command':cmd,'started_unix':time.time()})
    with (work/('log.'+stage)).open('wb') as log:
        process=subprocess.Popen(cmd,stdout=log,stderr=subprocess.STDOUT)
        try:
            while process.poll() is None:
                if time.monotonic()>deadline:raise TimeoutError('native attempt exceeded four hours')
                if shutil.disk_usage(work).free<4*1024**3:raise RuntimeError('disk reserve below 4 GiB; native attempt stopped')
                time.sleep(2)
            if process.returncode:raise RuntimeError(stage+' exit '+str(process.returncode))
        finally:
            subprocess.run(['docker','rm','-f',name],stdout=subprocess.DEVNULL,stderr=subprocess.DEVNULL,timeout=20)
            if process.poll() is None:process.terminate();process.wait(timeout=20)
            save(work/'native-active.json',{'stage':stage,'container':name,'finished':True,'exit':process.returncode})
    return {'stage':stage,'exit':process.returncode,'seconds':time.monotonic()-started,'command':cmd}


def verify_case(out,work,reduce_fields=True):
    protocol=identity(out);row=json.loads((work/'result.json').read_text())
    if row['identity_sha256']!=sha(out/'protocol.json'):raise ValueError('case protocol identity changed')
    if row['config']!=config_for(row['config']['scale'],row['config']['upstream_h'],row['config']['downstream_h']):raise ValueError('case configuration drift')
    if sha(work/'evidence.json')!=row['evidence']['manifest_sha256']:raise ValueError('case evidence entry changed')
    files=json.loads((work/'evidence.json').read_text())['files'];verify_files(work,{k:v['sha256'] for k,v in files.items()})
    source=Path(row['origin']['path'])
    if sha(source/'result.json')!=row['origin']['result_sha256'] or sha(source/'evidence.json')!=row['origin']['evidence_sha256']:raise ValueError('initialization origin drift')
    expected=dict(row['config']);expected['reynolds']=200
    if row['config']['scale']==8:
        expected=dict(row['config'],scale=4,expected_cells=row['config']['expected_cells']//4,near_step_dx_h=.025)
        if source!=out/f"re300-u{expected['upstream_h']}-d{expected['downstream_h']}-g4":raise ValueError('G3 source domain/identity')
        verify_case(out,source,reduce_fields)
    elif source!=Path(protocol['legacy'])/f"re200-u{expected['upstream_h']}-d{expected['downstream_h']}-g{expected['scale']}":raise ValueError('lower-grid source domain/identity')
    if json.loads((source/'result.json').read_text())['config']!=expected:raise ValueError('source configuration mismatch')
    source_files=json.loads((source/'evidence.json').read_text())['files'];verify_files(source,{k:v['sha256'] for k,v in source_files.items()})
    with tempfile.TemporaryDirectory() as tmp:
        generated=Path(tmp)/'case';c=row['config'];write_case(generated,c['scale'],c['upstream_h'],c['downstream_h'],row['purge_write'])
        for p in generated.rglob('*'):
            if not p.is_file():continue
            rel=p.relative_to(generated)
            if sha(p)!=sha(work/'generated-inputs'/rel):raise ValueError('generated template drift: '+str(rel))
            if str(rel) not in ('0/U','0/p') and p.read_bytes()!=(work/'case'/rel).read_bytes():raise ValueError('native input drift: '+str(rel))
        for f in ('U','p'):
            if sha(work/'mapped-initial-fields'/f)!=sha(work/'case/0'/f):raise ValueError('initial state changed')
            if field_dictionary(work/'case/0'/f)['boundaryField']!=field_dictionary(generated/'0'/f)['boundaryField']:raise ValueError('mapping changed boundary')
    if row['config']['scale']==8 and (work/'case/system/decomposeParDict').read_text()!=DECOMPOSE:raise ValueError('MPI decomposition drift')
    if row['status']=='complete' and reduce_fields:
        fresh=json.loads(json.dumps(reduce(work,row['config'])))
        if any(row[k]!=value for k,value in fresh.items()):raise ValueError('saved reduction differs')
    return row,len(files)


def run_case(out,cid,config,source,purge=2):
    protocol=identity(out);work=out/cid
    if config!=config_for(config['scale'],config['upstream_h'],config['downstream_h']):raise ValueError('unsupported case configuration')
    u,d,s=config['upstream_h'],config['downstream_h'],config['scale']
    expected_source=out/f're300-u{u}-d{d}-g4' if s==8 else Path(protocol['legacy'])/f're200-u{u}-d{d}-g{s}'
    if source!=expected_source:raise ValueError('source must be the frozen same-domain case')
    if cid!=f're300-u{u}-d{d}-g{s}' and not (cid=='retention-control-u5-d30-g1' and (u,d,s,purge)==(5,30,1,0)):raise ValueError('case identity does not match configuration')
    if type(purge)!=int or purge not in (0,2) or (purge==0)!=(cid=='retention-control-u5-d30-g1'):raise ValueError('retention does not match case identity')
    if (work/'result.json').exists():
        row,_=verify_case(out,work)
        if not row['valid']:raise ValueError('failed attempt retained; use new identity')
        return row
    if work.exists():raise ValueError('unfinished attempt retained: '+cid)
    if shutil.disk_usage(out).free<protocol['minimum_start_free_bytes']:raise ValueError('need >=6 GiB before starting case')
    if config['scale']==8:
        parent,_=verify_case(out,source)
        if not parent['valid']:raise ValueError('G2 source is invalid')
        expected=dict(config,scale=4,expected_cells=config['expected_cells']//4,near_step_dx_h=.025)
    else:
        parents=json.loads((Path(protocol['parent'])/'analysis.json').read_text())['rows']
        parent=next((r for r in parents if r['id']==source.name),None);expected=dict(config,reynolds=200)
    if parent is None or not parent['valid'] or parent['config']!=expected:raise ValueError('valid same-domain source required')
    files=json.loads((source/'evidence.json').read_text())['files'];verify_files(source,{k:v['sha256'] for k,v in files.items()})
    started=time.monotonic();deadline=started+14400;work.mkdir()
    row={'id':cid,'config':config,'identity_sha256':sha(out/'protocol.json'),'status':'running','valid':False,'purge_write':purge,'steps':[],
         'origin':{'path':str(source),'result_sha256':sha(source/'result.json'),'evidence_sha256':sha(source/'evidence.json')}}
    save(work/'running.json',row)
    try:
        if write_case(work/'case',config['scale'],config['upstream_h'],config['downstream_h'],purge)!=config:raise ValueError('writer config mismatch')
        shutil.copytree(work/'case',work/'generated-inputs')
        for stage in ('blockMesh','checkMesh','mapFields'):
            row['phase']=stage;save(work/'running.json',row);row['steps'].append(native(work,stage,deadline,source/'case' if stage=='mapFields' else None))
        for f in ('U','p'):
            p=work/'case/0'/f;text=p.read_text();generated=(work/'generated-inputs/0'/f).read_text()
            p.write_text(text[:text.index('boundaryField')]+generated[generated.index('boundaryField'):])
        shutil.copytree(work/'case/0',work/'mapped-initial-fields')
        ranks=4 if config['scale']==8 else 1
        if ranks==4:
            (work/'case/system/decomposeParDict').write_text(DECOMPOSE)
            row['steps'].append(native(work,'decomposePar',deadline,ranks=4))
        row['phase']='simpleFoam';save(work/'running.json',row);row['steps'].append(native(work,'simpleFoam',deadline,ranks=ranks))
        if ranks==4:
            times=sorted(int(p.name) for p in (work/'case/processor0').iterdir() if p.name.isdecimal() and int(p.name)>0 and all((p/f).is_file() for f in ('U','p','phi','wallShearStress')))
            if len(times)!=2:raise ValueError('rolling MPI pair missing')
            row['steps'].append(native(work,'reconstructPar',deadline,ranks=4,times=times))
        row['phase']='independent_reduction';save(work/'running.json',row)
        row.update(reduce(work,config,True));row['status']='complete'
    except Exception as exc:row.update(status='failed',error=str(exc))
    row['seconds']=time.monotonic()-started;row['evidence']=evidence(work);save(work/'result.json',row)
    print(json.dumps({k:row.get(k) for k in ('id','status','valid','seconds','error','qoi')},ensure_ascii=False),flush=True)
    return row


def retention_check(out):
    a,_=verify_case(out,out/'retention-control-u5-d30-g1');b,_=verify_case(out,out/'re300-u5-d30-g1')
    if not a['valid'] or not b['valid'] or [a['previous_iteration'],a['qoi']['iteration']]!=[b['previous_iteration'],b['qoi']['iteration']]:raise ValueError('retention pair did not converge identically')
    checked=[]
    for t in (a['previous_iteration'],a['qoi']['iteration']):
        for f in ('U','p','phi','wallShearStress'):
            left=out/a['id']/'case'/str(t)/f;right=out/b['id']/'case'/str(t)/f
            if field_dictionary(left)!=field_dictionary(right):raise ValueError('retention changed native field: '+f)
            checked.append({'time':t,'field':f,'control_sha256':sha(left),'rolling_sha256':sha(right)})
    available=sorted(int(p.name) for p in (out/b['id']/'case').iterdir() if p.name.isdecimal() and int(p.name)>0)
    if available!=[b['previous_iteration'],b['qoi']['iteration']]:raise ValueError('purgeWrite did not retain exactly two output times')
    return {'passed':True,'fields':checked,'rolling_times':available,'control_result_sha256':sha(out/a['id']/'result.json'),'rolling_result_sha256':sha(out/b['id']/'result.json')}


def analyze(out,verify=False):
    protocol=identity(out);retention=retention_check(out)
    if json.loads((out/'retention-check.json').read_text())!=retention:raise ValueError('retention check changed')
    rows=[];count=0;feedback=[]
    for cid in protocol['matrix']:
        work=out/cid
        if not (work/'result.json').exists():feedback.append({'case':cid,'issue':'missing native result'});continue
        row,n=verify_case(out,work);count+=n;rows.append(row)
        if not row['valid']:feedback.append({'case':cid,'issue':row.get('error','native checks failed')})
    compact=[{k:v for k,v in row.items() if k not in ('snapshots','steps','convergence')} for row in rows]
    result=decide(compact,retention['passed']);result['feedback']=feedback
    if len(rows)==16 and all(r['valid'] for r in rows):result['common_geometry']=common_geometry(out,300)
    result['verification']={'native_records':count,'source_files':len(protocol['source_hashes']),'new_model_calls':0}
    result['protocol_sha256']=sha(out/'protocol.json')
    if verify:
        if json.loads((out/'analysis.json').read_text())!=result:raise ValueError('saved analysis differs')
    else:save(out/'analysis.json',result)
    print(json.dumps({'gate_passed':result['gate_passed'],'failed_gates':result['failed_gates'],'rows':len(rows)}),flush=True)
    return result


def run(out):
    protocol=identity(out);legacy=Path(protocol['legacy'])
    with (out/'run.lock').open('a') as lock:
        fcntl.flock(lock,fcntl.LOCK_EX|fcntl.LOCK_NB)
        if not (out/'retention-check.json').exists():
            config=config_for(1,5,30);source=legacy/'re200-u5-d30-g1'
            run_case(out,'retention-control-u5-d30-g1',config,source,0)
            run_case(out,'re300-u5-d30-g1',config,source,2)
            save(out/'retention-check.json',retention_check(out))
        else:
            if retention_check(out)!=json.loads((out/'retention-check.json').read_text()):raise ValueError('retention gate drift')
        jobs=[(out,f're300-u{u}-d{d}-g{s}',config_for(s,u,d),legacy/f're200-u{u}-d{d}-g{s}') for u,d in DOMAINS for s in (1,2,4)]
        with ThreadPoolExecutor(max_workers=2) as pool:lower=list(pool.map(lambda args:run_case(*args),jobs))
        if all(r['valid'] for r in lower):
            jobs=[(out,f're300-u{u}-d{d}-g8',config_for(8,u,d),out/f're300-u{u}-d{d}-g4') for u,d in DOMAINS]
            with ThreadPoolExecutor(max_workers=2) as pool:list(pool.map(lambda args:run_case(*args),jobs))
        analyze(out)


def main():
    p=argparse.ArgumentParser();p.add_argument('command',choices=['prepare','run','analyze','verify']);p.add_argument('--out',type=Path,required=True);p.add_argument('--parent',type=Path);p.add_argument('--legacy',type=Path);p.add_argument('--preflight',type=Path);a=p.parse_args();out=a.out.resolve()
    if a.command=='prepare':prepare(out,a.parent.resolve(),a.legacy.resolve(),a.preflight.resolve())
    elif a.command=='run':run(out)
    else:analyze(out,a.command=='verify')


if __name__=='__main__':main()
