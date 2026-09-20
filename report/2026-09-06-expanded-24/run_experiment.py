"""Frozen 24-task expansion; two independent model processes, serialized LibreOffice."""
from pathlib import Path
from collections import defaultdict
import argparse
import contextlib
import copy
import fcntl
import hashlib
import json
import os
import random
import runpy
import shutil
import subprocess
import sys
import time
import urllib.request
import yaml

HERE=Path(__file__).resolve().parent
ROOT=HERE.parents[1]
PRIOR=ROOT/'report/2026-09-06-b05-live'
sys.path.insert(0,str(ROOT))
from runners.common import load_tasks,write_json_atomic
from runners.run_state import referenced_files
from runners.hidden_runtime import load_hidden_pool
from runners import providers
from ledger import Ledger,EvidenceStop
from table_preflight import TABLE_IDS

GROUPS=[
    ('extract','qa_grounded','awext.clause_extract',[f'awx_ce_{i:02d}' for i in range(3,9)],[]),
    ('compliance','qa_grounded','awcom.compliance',
     ['awc_acam_02','awc_acam_03','awc_rev_02','awc_rev_03','awc_trc_01','awc_trc_02'],[]),
    ('hidden','qa_grounded','awcom.compliance',[],['--hidden','6']),
    ('formula','design_artifact','spreadsheetbench.verified_subset',TABLE_IDS,['--iterate','1']),
]
MODELS={
    'minimax':{'provider':'minimax','model':'MiniMax-M3',
        'endpoint':'https://api.minimaxi.com/v1/chat/completions','transport_timeout_s':1800},
    'glm':{'provider':'glm','model':'glm-5.3-flash',
        'endpoint':'https://open.bigmodel.cn/api/coding/paas/v4/chat/completions','transport_timeout_s':1800},
}


def read(path):return json.loads(path.read_text())
def sha(path):return hashlib.sha256(path.read_bytes()).hexdigest()


def hidden_draw(pool,seed):
    families=defaultdict(list)
    rng=random.Random(20260826 ^ seed)
    for task in pool:families[task.id.rsplit('_',1)[0]].append(task.id)
    for family in families:rng.shuffle(families[family])
    picked=[]
    while len(picked)<6:
        for family in sorted(families):
            if families[family] and len(picked)<6:picked.append(families[family].pop())
    return sorted(picked)


def prepare():
    if (HERE/'protocol.json').exists():raise SystemExit('already frozen')
    audit=read(ROOT/'report/2026-09-06-ssb22-audit/audit.json')
    assert audit['status']=='quarantined'
    preflight=read(HERE/'table-preflight.json')
    assert [r['task_id'] for r in preflight]==TABLE_IDS
    assert all(r['status']=='passed' and r['changed_cell_count']>0 for r in preflight)
    workspace=HERE/'workspace';workspace.mkdir(exist_ok=True)
    if not (workspace/'data').exists():
        (workspace/'data').symlink_to(ROOT/'data',target_is_directory=True)
    assert (workspace/'data').is_symlink() and (workspace/'data').resolve()==ROOT/'data'
    previous={tid for g in read(PRIOR/'protocol.json')['groups'] for tid in g['expected_task_ids']}
    pool,_,rev=load_hidden_pool(ROOT,'awcom.compliance')
    seed=20260906
    while set(hidden_draw(pool,seed)) & previous:seed+=1
    groups=[]
    overlays={}
    for name,adapter,suite,ids,flags in GROUPS:
        target=workspace/'tasks'/suite;target.mkdir(parents=True,exist_ok=True)
        for tid in ids:
            assert tid not in previous
            source=ROOT/'tasks'/suite/(tid+'.yaml')
            spec=yaml.safe_load(source.read_text())
            if name=='formula':
                overlays[tid]={'grader.numeric_rel_tol':{'from':spec['grader']['numeric_rel_tol'],'to':0},
                              'reference.rel_tol':{'from':spec['reference']['rel_tol'],'to':0}}
                spec['grader']['numeric_rel_tol']=0
                spec['reference']['rel_tol']=0
                (target/source.name).write_text(yaml.safe_dump(spec,allow_unicode=True,sort_keys=False))
            else:shutil.copy2(source,target/source.name)
            shutil.copy2(source.with_suffix('.md'),target/source.with_suffix('.md').name)
        groups.append({'name':name,'module':'runners.'+adapter,'suite':suite,'flags':flags,
                       'expected_task_ids':hidden_draw(pool,seed) if name=='hidden' else sorted(ids)})
    paths=[*ROOT.joinpath('runners').rglob('*.py'),*workspace.joinpath('tasks').rglob('*.*'),
           HERE/'ledger.py',HERE/'run_experiment.py',HERE/'table_preflight.py',HERE/'table-preflight.json',
           ROOT/'report/2026-09-06-ssb22-audit/audit.json',
           ROOT/'data/awcom/compliance/hidden/generator.py',ROOT/'data/awcom/compliance/hidden/answers.b64']
    for _,_,suite,ids,_ in GROUPS:
        for tid in ids:paths.extend([ROOT/'tasks'/suite/(tid+'.yaml'),ROOT/'tasks'/suite/(tid+'.md')])
        td=workspace/'tasks'/suite
        paths.extend(Path(p) for p in referenced_files(load_tasks(td),td,{}) if Path(p).is_file())
    protocol={'version':1,'created_at_epoch':time.time(),'seed':seed,'models':MODELS,'groups':groups,
        'budget':None,'n_tasks_per_model':24,'harness_arm':'H0','numeric_policy':'strict-copy-v1',
        'overlays':overlays,'excluded_tasks':{'ssb_22_47':audit['classification']},
        'hidden_pool_revision':rev,'sampling':'6 per group; public IDs fixed; first seed >=20260906 with no prior hidden overlap',
        'request_settings':{'temperature':0,'max_tokens':32768,'thinking':'native preset; GLM enabled, MiniMax default'},
        'execution_policy':{'provider_processes':2,'requests_per_provider_in_flight':1,
                            'libreoffice':'cross-process exclusive lock; original command unchanged'},
        'frozen_files':{str(p.relative_to(ROOT)):sha(p) for p in sorted(set(paths)) if p.is_file()},
        'prior_json_hashes':{str(p.relative_to(ROOT)):sha(p) for p in sorted(PRIOR.rglob('*.json'))},
        'notes':['No score-driven retries. Native provider parse retries retained.',
                 'MiniMax now uses native preset max_tokens=32768; not a controlled before/after comparison.',
                 'Canonical tasks/gold/grader unchanged; zero tolerance only in six experiment task copies.',
                 'Capture public responses and workbooks; never persist hidden prompts or answers.',
                 'Report changed-cell accuracy separately from unchanged-cell-dominated overall score.']}
    write_json_atomic(HERE/'protocol.json',protocol)
    print(json.dumps({'seed':seed,'groups':groups,'n_tasks_per_model':24},ensure_ascii=False))


def command(group,protocol,alias,provider=None):
    config=protocol['models'][alias]
    args=[group['module'],'--tasks',str(HERE/'workspace/tasks'/group['suite']),
        '--out',str(HERE/alias/'runs'/group['name']),'--provider',provider or config['provider'],
        '--seed',str(protocol['seed']),'--resume',*group['flags']]
    if provider!='oracle':args+=['--model',config['model']]
    return args


def invoke(argv):
    sys.argv=argv
    try:runpy.run_module(argv[0],run_name='__main__')
    except SystemExit as result:return result.code or 0
    return 0


def execute(alias,oracle=False):
    protocol=read(HERE/'protocol.json')
    for name,digest in {**protocol['frozen_files'],**protocol['prior_json_hashes']}.items():
        if sha(ROOT/name)!=digest:raise EvidenceStop('frozen source/evidence changed: '+name)
    directory=HERE/alias
    config=protocol['models']['minimax' if oracle else alias]
    if oracle:protocol['models'][alias]=config
    elif alias=='glm':
        if not os.environ.get('GLM_API_KEY'):raise EvidenceStop('GLM key unavailable')
        os.environ['GLM_BASE_URL']=config['endpoint'].removesuffix('/chat/completions')
    elif not (os.environ.get('MINIMAX_M3_API_KEY') or os.environ.get('MINIMAX_API_KEY')):
        raise EvidenceStop('MiniMax key unavailable')
    guard=Ledger(directory/'requests.json',config,sha(HERE/'protocol.json'))
    if oracle:guard.phase='verify'
    summary={'status':'running','protocol_sha256':sha(HERE/'protocol.json'),'model':config['model'],
             'evidence_kind':'offline oracle' if oracle else 'real model','groups':[],
             'cache_verification':[],'started_at_epoch':time.time()}
    opener,answer,run=urllib.request.urlopen,providers.get_answer,subprocess.run
    captures=defaultdict(int)
    def with_task(task,*args,**kwargs):
        guard.task_id=task.id
        return answer(task,*args,**kwargs)
    def serialize_office(args,*rest,**kwargs):
        if isinstance(args,(list,tuple)) and args and args[0]=='soffice':
            with (HERE/'.soffice.lock').open('a') as lock:
                fcntl.flock(lock,fcntl.LOCK_EX)
                result=run(args,*rest,**kwargs)
                source=Path(args[-1])
                if source.name=='output.xlsx' and guard.task_id and guard.group=='formula':
                    captures[guard.task_id]+=1
                    target=directory/'workbooks'/guard.task_id;target.mkdir(parents=True,exist_ok=True)
                    index=captures[guard.task_id]
                    shutil.copy2(source,target/f'run{index}-output.xlsx')
                    converted=Path(args[args.index('--outdir')+1])/source.name
                    if converted.exists():shutil.copy2(converted,target/f'run{index}-recalculated.xlsx')
                return result
        return run(args,*rest,**kwargs)
    urllib.request.urlopen=guard.urlopen;providers.get_answer=with_task;subprocess.run=serialize_office
    try:
        for group in protocol['groups']:
            guard.group=group['name']
            rc=invoke(command(group,protocol,alias,'oracle' if oracle else None))
            if rc:raise EvidenceStop(group['name']+' runner failed; sensitive provider error detail suppressed')
            manifest=read(directory/'runs'/group['name']/'run_manifest.json')
            assert manifest['extra']['selected_task_ids']==group['expected_task_ids']
        guard.phase='verify'
        count=len(guard.state['requests'])
        for group in protocol['groups']:
            out=directory/'runs'/group['name']
            before={p.name:p.read_bytes() for p in out.glob('result_*.json')}
            rc=invoke(command(group,protocol,alias,'oracle' if oracle else None))
            assert not rc and before=={p.name:p.read_bytes() for p in out.glob('result_*.json')}
            assert read(out/'run_manifest.json')['extra']['resumed_tasks']==6
            snap={p.name:p.read_bytes() for p in out.iterdir() if not p.name.startswith('.')}
            changed=command(group,protocol,alias,'oracle' if oracle else None)
            changed[changed.index('--seed')+1]=str(protocol['seed']+1)
            assert invoke(changed)
            assert snap=={p.name:p.read_bytes() for p in out.iterdir() if not p.name.startswith('.')}
            summary['cache_verification'].append({'group':group['name'],'n_cached':6,
                'results_byte_identical':True,'mismatched_seed_rejected':True,'new_http_requests':0})
        assert len(guard.state['requests'])==count
        summary['status']='completed'
    except EvidenceStop as stop:
        summary.update(status='stopped',stop_reason=str(stop));print('[stopped]',str(stop),flush=True)
    finally:
        urllib.request.urlopen=opener;providers.get_answer=answer;subprocess.run=run
        for group in protocol['groups']:
            rows=[read(p) for p in sorted((directory/'runs'/group['name']).glob('result_*.json'))]
            summary['groups'].append({'name':group['name'],'n_tasks':len(rows),
                'scores':[{'task_id':r['task_id'],'gate':r['validity_gate'],'score':r['score'],
                           'failure_mode':r['failure_mode']} for r in rows]})
        requests=guard.state['requests']
        summary.update(requests=len(requests),
            usage={k:sum((r.get('usage') or {}).get(k,0) for r in requests)
                   for k in ('prompt_tokens','completion_tokens','total_tokens')},
            uncertain_requests=sum(r['status']!='received' for r in requests),
            elapsed_s=round(time.time()-summary['started_at_epoch'],3))
        write_json_atomic(directory/'summary.json',summary)
    print(json.dumps(summary,ensure_ascii=False,indent=2),flush=True)
    return 0 if summary['status']=='completed' else 2


if __name__=='__main__':
    parser=argparse.ArgumentParser()
    mode=parser.add_mutually_exclusive_group(required=True)
    mode.add_argument('--prepare',action='store_true')
    mode.add_argument('--execute',choices=['minimax','glm','oracle'])
    args=parser.parse_args()
    if args.prepare:prepare()
    else:
        folder=HERE/args.execute;folder.mkdir(exist_ok=True)
        with (folder/'.lock').open('a') as lock:
            fcntl.flock(lock,fcntl.LOCK_EX|fcntl.LOCK_NB)
            with (folder/'execution.log').open('a',buffering=1) as log:
                with contextlib.redirect_stdout(log),contextlib.redirect_stderr(log):
                    code=execute(args.execute,args.execute=='oracle')
        raise SystemExit(code)
