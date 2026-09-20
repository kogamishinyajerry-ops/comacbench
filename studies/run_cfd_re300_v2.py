"""New Re=300 identity: validated wall branches and provenance-aware continuation."""
import argparse
from concurrent.futures import ThreadPoolExecutor
import fcntl
import json
from pathlib import Path
import shutil
import sys
import tempfile
import time
ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT))
from studies.cfd_re300_v2 import config_for,write_case,reduce,decide
from studies.cfd_step_sensitivity import sha,save,evidence,DOMAINS
from studies.cfd_fourth_grid import field_dictionary
from studies.cfd_mpi_bridge import DECOMPOSE
from studies.verify_cfd_primary_delivery import verify_files
from studies.analyze_cfd_fourth_grid import common_geometry
from studies.run_cfd_re300 import native,identity as pilot_identity

OWN=['studies/cfd_wall_branch.py','studies/cfd_re300_v2.py','studies/run_cfd_re300_v2.py','studies/replay_cfd_wall_branch.py','studies/render_cfd_re300_v2.py','tests/test_cfd_wall_branch.py','docs/specs/cfd-re300-v2.md']

def identity(out):
    protocol=json.loads((out/'protocol.json').read_text())
    if protocol['identity']!='comacbench.cfd-re300.v2' or protocol['reference']!=6.751:raise ValueError('unexpected Re=300 identity')
    verify_files(ROOT,protocol['source_hashes']);verify_files(out/'frozen-source',protocol['source_hashes'])
    for path,digest in protocol['parent_hashes'].items():
        if sha(path)!=digest:raise ValueError('parent entry point drift: '+path)
    for record in protocol['parent_manifests']:
        path=Path(record['path'])
        if sha(path)!=record['sha256']:raise ValueError('parent delivery changed')
        verify_files(ROOT,json.loads(path.read_text())['files'])
    return protocol

def prepare(out,pilot):
    if out.exists():raise ValueError('output exists; retain it')
    previous=pilot_identity(pilot)
    manifest=pilot/'delivery-manifest.json';verify_files(ROOT,json.loads(manifest.read_text())['files'])
    from studies.report_cfd_re300_failure import reproduce
    receipt,_=reproduce(pilot)
    if not receipt['retention_fields_equal'] or receipt['native_runs_completed']!=2:raise ValueError('verified pilot pair required')
    hashes=dict(previous['source_hashes']);hashes.update(json.loads((pilot/'source-delivery.json').read_text())['files'])
    hashes.update({name:sha(ROOT/name) for name in OWN});verify_files(ROOT,hashes)
    if shutil.disk_usage(out.parent).free<6*1024**3:raise ValueError('need >=6 GiB before study creation')
    protocol=dict(previous,identity='comacbench.cfd-re300.v2',source_hashes=hashes,pilot=str(pilot),
                  wall_diagnostic='mutual_negative_branch_overlap/v1',adopted_matrix_cases=['re300-u5-d30-g1'],new_native_matrix_cases=15)
    protocol['parent_manifests']=previous['parent_manifests']+[{'path':str(manifest),'sha256':sha(manifest)}]
    protocol['parent_hashes']=dict(previous['parent_hashes'],**{str(p):sha(p) for p in [pilot/'protocol.json',pilot/'failure-analysis.json',pilot/'completion-verification.json']})
    out.mkdir(parents=True)
    for name in hashes:
        path=out/'frozen-source'/name;path.parent.mkdir(parents=True,exist_ok=True);shutil.copyfile(ROOT/name,path)
    save(out/'protocol.json',protocol);save(out/'parent-verification.json',receipt)
    return protocol


def compatibility_gate(out):
    receipt=json.loads((out/'compatibility-verification.json').read_text())
    if receipt['protocol_sha256']!=sha(out/'protocol.json') or receipt['passed'] is not True or receipt['cases']!=18 or receipt['snapshots']!=36:
        raise ValueError('complete verified 36-field compatibility gate required')
    ids={f're200-u{u}-d{d}-g{s}' for u,d in DOMAINS for s in (1,2,4,8)}|{'retention-control-u5-d30-g1','re300-u5-d30-g1'}
    expected={'compatibility/'+cid+'.json' for cid in ids}|{'compatibility/analysis.json'}
    if set(receipt['files'])!=expected:raise ValueError('compatibility seal must include every declared case')
    verify_files(out,receipt['files'])
    analysis=json.loads((out/'compatibility/analysis.json').read_text())
    if analysis.get('passed') is not True or len(analysis['rows'])!=18 or {r['id'] for r in analysis['rows']}!=ids or any(r['snapshots']!=2 or not r['valid'] or not r['native_unchanged'] for r in analysis['rows']):
        raise ValueError('incomplete or invalid compatibility matrix')
    return sha(out/'compatibility-verification.json')


def verify_case(out,work,reduce_fields=True):
    protocol=identity(out);row=json.loads((work/'result.json').read_text())
    if row['compatibility_sha256']!=compatibility_gate(out):raise ValueError('compatibility identity drift')
    if row['identity_sha256']!=sha(out/'protocol.json'):raise ValueError('case protocol identity changed')
    if row['id']!=work.name:raise ValueError('case identity/path mismatch')
    if row['config']!=config_for(row['config']['scale'],row['config']['upstream_h'],row['config']['downstream_h']):raise ValueError('case configuration drift')
    if sha(work/'evidence.json')!=row['evidence']['manifest_sha256']:raise ValueError('case evidence entry changed')
    files=json.loads((work/'evidence.json').read_text())['files'];verify_files(work,{k:v['sha256'] for k,v in files.items()})
    if row.get('native_execution')=='saved_field_reuse':
        original=Path(row['native_origin']['path'])
        if original!=Path(protocol['pilot'])/work.name or work.name not in ('retention-control-u5-d30-g1','re300-u5-d30-g1'):raise ValueError('invalid saved-field origin')
        if sha(original/'result.json')!=row['native_origin']['result_sha256'] or sha(original/'evidence.json')!=row['native_origin']['evidence_sha256']:raise ValueError('saved pilot drift')
        original_files=json.loads((original/'evidence.json').read_text())['files']
        verify_files(original,{k:v['sha256'] for k,v in original_files.items()})
        verify_files(work,{k:v['sha256'] for k,v in original_files.items()})
    elif row.get('native_execution')!='fresh_solve':raise ValueError('native execution origin missing')
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
    protocol=identity(out);gate=compatibility_gate(out);work=out/cid
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
         'native_execution':'fresh_solve','compatibility_sha256':gate,
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

def adopt_pilot(out,cid):
    protocol=identity(out);gate=compatibility_gate(out);work=out/cid
    if cid not in ('retention-control-u5-d30-g1','re300-u5-d30-g1'):raise ValueError('unsupported adoption')
    if work.exists():return verify_case(out,work)[0]
    source=Path(protocol['pilot'])/cid;old=json.loads((source/'result.json').read_text())
    entries=json.loads((source/'evidence.json').read_text())['files'];verify_files(source,{k:v['sha256'] for k,v in entries.items()})
    work.mkdir()
    for name in entries:
        p=work/name;p.parent.mkdir(parents=True,exist_ok=True);shutil.copyfile(source/name,p)
    row={'id':cid,'config':old['config'],'identity_sha256':sha(out/'protocol.json'),'compatibility_sha256':gate,
         'native_execution':'saved_field_reuse','native_origin':{'path':str(source),'result_sha256':sha(source/'result.json'),'evidence_sha256':sha(source/'evidence.json')},
         'origin':old['origin'],'steps':old['steps'],'purge_write':old['purge_write'],'seconds':old['seconds'],'status':'complete'}
    row.update(reduce(work,row['config'],True));row['evidence']=evidence(work);save(work/'result.json',row)
    return verify_case(out,work)[0]


def analyze(out,verify=False):
    protocol=identity(out);gate=compatibility_gate(out);retention=retention_check(out)
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
    result['compatibility_sha256']=gate
    result['native_execution_counts']={'fresh':sum(r['native_execution']=='fresh_solve' for r in rows),'reused':sum(r['native_execution']=='saved_field_reuse' for r in rows)}
    if verify:
        if json.loads((out/'analysis.json').read_text())!=result:raise ValueError('saved analysis differs')
    else:save(out/'analysis.json',result)
    print(json.dumps({'gate_passed':result['gate_passed'],'failed_gates':result['failed_gates'],'rows':len(rows)}),flush=True)
    return result

def run(out):
    protocol=identity(out);compatibility_gate(out);legacy=Path(protocol['legacy'])
    with (out/'run.lock').open('a') as lock:
        fcntl.flock(lock,fcntl.LOCK_EX|fcntl.LOCK_NB)
        if not (out/'retention-check.json').exists():
            for cid in ('retention-control-u5-d30-g1','re300-u5-d30-g1'):adopt_pilot(out,cid)
            save(out/'retention-check.json',retention_check(out))
        elif retention_check(out)!=json.loads((out/'retention-check.json').read_text()):raise ValueError('retention gate drift')
        jobs=[(out,f're300-u{u}-d{d}-g{s}',config_for(s,u,d),legacy/f're200-u{u}-d{d}-g{s}') for u,d in DOMAINS for s in (1,2,4)]
        with ThreadPoolExecutor(max_workers=2) as pool:lower=list(pool.map(lambda args:run_case(*args),jobs))
        if all(r['valid'] for r in lower):
            jobs=[(out,f're300-u{u}-d{d}-g8',config_for(8,u,d),out/f're300-u{u}-d{d}-g4') for u,d in DOMAINS]
            with ThreadPoolExecutor(max_workers=2) as pool:list(pool.map(lambda args:run_case(*args),jobs))
        analyze(out)


def main():
    p=argparse.ArgumentParser();p.add_argument('command',choices=['prepare','run','analyze','verify']);p.add_argument('--out',type=Path,required=True);p.add_argument('--pilot',type=Path);a=p.parse_args();out=a.out.resolve()
    if a.command=='prepare':prepare(out,a.pilot.resolve())
    elif a.command=='run':run(out)
    else:analyze(out,a.command=='verify')


if __name__=='__main__':main()
