"""Frozen eight-task live smoke. --prepare is offline; --execute spends the fixed budget."""
from pathlib import Path
import argparse
import contextlib
import fcntl
import hashlib
import json
import os
import runpy
import shlex
import shutil
import sys
import time
import urllib.request

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[1]
sys.path.insert(0,str(ROOT))
from runners.common import write_json_atomic
from budget_guard import BudgetGuard, BudgetStop

GROUPS = [
    ('extract','qa_grounded','awext.clause_extract',['awx_ce_01','awx_ce_02'],[]),
    ('compliance','qa_grounded','awcom.compliance',['awc_acam_01','awc_rev_01'],[]),
    ('hidden','qa_grounded','awcom.compliance',[],['--hidden','2']),
    ('formula','design_artifact','spreadsheetbench.verified_subset',['ssb_17_35','ssb_22_47'],['--iterate','1']),
]


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def prepare():
    path = HERE/'protocol.json'
    if path.exists():
        raise SystemExit('protocol already frozen; existing experiment preserved')
    workspace = HERE/'workspace'
    workspace.mkdir(exist_ok=True)
    (workspace/'data').symlink_to(ROOT/'data',target_is_directory=True)
    for _,_,suite,ids,_ in GROUPS:
        target = workspace/'tasks'/suite
        target.mkdir(parents=True,exist_ok=True)
        for tid in ids:
            for ext in ('.yaml','.md'):
                shutil.copy2(ROOT/'tasks'/suite/(tid+ext),target/(tid+ext))
    seed = 20260905
    from runners.hidden_runtime import load_hidden_pool
    tasks,_,revision = load_hidden_pool(workspace,'awcom.compliance')
    # Runner performs the deterministic family-balanced draw; pool is frozen here.
    paths = [*ROOT.joinpath('runners').rglob('*.py'),
             *workspace.joinpath('tasks').rglob('*.yaml'),*workspace.joinpath('tasks').rglob('*.md'),
             HERE/'budget_guard.py',HERE/'run_experiment.py']
    from runners.common import load_tasks
    from runners.run_state import referenced_files
    for suite in sorted({g[2] for g in GROUPS}):
        taskdir = workspace/'tasks'/suite
        paths.extend(Path(p) for p in referenced_files(load_tasks(taskdir),taskdir,{})
                     if Path(p).is_file())
    protocol = {'version':1,'created_at_epoch':time.time(),'purpose':'trusted resume live smoke',
        'model':'deepseek-v4-flash','seed':seed,'provider':'openai_compat',
        'request_defaults':{'temperature':0.0,'max_tokens':16384,'thinking':'provider default enabled'},
        'budget':{'endpoint':'https://api.deepseek.com/chat/completions','model':'deepseek-v4-flash',
                  'max_requests':12,'max_completion_tokens':50000,'max_request_bytes':32000,'max_seconds':1200},
        'groups':[{'name':n,'module':'runners.'+a,'suite':s,'public_ids':ids,'flags':flags}
                  for n,a,s,ids,flags in GROUPS],
        'hidden_pool':{'revision':revision,'size':len(tasks),'selected_count':2},
        'frozen_files':{str(p.relative_to(ROOT)):sha(p) for p in sorted(set(paths))},
        'safe_rerun_command':shlex.join([sys.executable,str(HERE/'run_experiment.py'),'--execute']),
        'price_source':'https://api-docs.deepseek.com/quick_start/pricing/',
        'price_usd_per_million':{'peak':{'input_miss':0.44,'input_hit':0.014,'output':1.32},
                               'off_peak':{'input_miss':0.22,'input_hit':0.007,'output':0.66}},
        'price_read_date':'2026-09-05','notes':['No request body modification or extra model hints.',
            'Stop on transport/usage uncertainty; keep full output reservation.',
            'No score-driven retries; standard provider parse retries count toward the same budget.',
            'This is a convenience sample, not a capability estimate or cross-model comparison.']}
    write_json_atomic(path,protocol)
    print('Prepared 8 tasks, including 2 dynamically selected hidden tasks; no model requests.')


def command(group,protocol):
    return [group['module'],'--tasks',str(HERE/'workspace/tasks'/group['suite']),
            '--out',str(HERE/'runs'/group['name']),'--provider','openai_compat',
            '--model',protocol['model'],'--seed',str(protocol['seed']),'--resume',*group['flags']]


def invoke(argv):
    sys.argv = argv
    try:
        runpy.run_module(argv[0],run_name='__main__')
    except SystemExit as result:
        return result.code or 0
    return 0


def execute():
    protocol_path = HERE/'protocol.json'
    protocol = json.loads(protocol_path.read_text())
    for name,digest in protocol['frozen_files'].items():
        if sha(ROOT/name) != digest:
            raise SystemExit(f'frozen source changed: {name}; use a new experiment')
    secret = os.environ.get('DEEPSEEK_API_KEY')
    if not secret:
        raise SystemExit('DEEPSEEK_API_KEY is not available in the process environment')
    os.environ.update(BM_API_BASE='https://api.deepseek.com',BM_MODEL=protocol['model'],BM_API_KEY=secret)
    guard = BudgetGuard(HERE/'requests.json',protocol['budget'],sha(protocol_path))
    summary = {'protocol_sha256':sha(protocol_path),'groups':[],'cache_verification':[],
               'started_at_epoch':time.time(),'status':'running'}
    original_opener = urllib.request.urlopen
    urllib.request.urlopen = guard.urlopen
    try:
        for group in protocol['groups']:
            print('[group]',group['name'],flush=True)
            rc = invoke(command(group,protocol))
            if rc:
                raise BudgetStop(f'{group["name"]} runner exited {rc}')
        # The same CLI must reuse every result; any attempted HTTP request fails closed.
        guard.phase = 'verify'
        requests_before = len(guard.state['requests'])
        for group in protocol['groups']:
            out = HERE/'runs'/group['name']
            before = {p.name:p.read_bytes() for p in out.glob('result_*.json')}
            rc = invoke(command(group,protocol))
            after = {p.name:p.read_bytes() for p in out.glob('result_*.json')}
            if rc or before != after:
                raise BudgetStop('identical replay changed completed results')
            manifest = json.loads((out/'run_manifest.json').read_text())
            if manifest['extra']['resumed_tasks'] != len(before):
                raise BudgetStop('replay did not reuse the complete execution set')
            snapshot = {p.name:p.read_bytes() for p in out.iterdir() if not p.name.startswith('.')}
            changed = command(group,protocol)
            changed[changed.index('--seed')+1] = str(protocol['seed']+1)
            rc = invoke(changed)
            if not rc or snapshot != {p.name:p.read_bytes() for p in out.iterdir() if not p.name.startswith('.')}:
                raise BudgetStop('mismatched seed was accepted or modified existing output')
            summary['cache_verification'].append({'group':group['name'],'n_cached':len(before),
                'results_byte_identical':True,'mismatched_seed_rejected':True,'new_http_requests':0})
        if len(guard.state['requests']) != requests_before:
            raise BudgetStop('verification generated new model requests')
        summary['status'] = 'completed'
    except BudgetStop as stop:
        summary.update(status='stopped',stop_reason=str(stop))
        print('[stopped]',str(stop),flush=True)
    finally:
        urllib.request.urlopen = original_opener
        for group in protocol['groups']:
            out = HERE/'runs'/group['name']
            rows = [json.loads(p.read_text()) for p in sorted(out.glob('result_*.json'))]
            summary['groups'].append({'name':group['name'],'n_tasks':len(rows),
                'gate_passed':sum(r['validity_gate']==1 for r in rows),
                'full_score':sum(r['score']==1 for r in rows),
                'scores':[{'task_id':r['task_id'],'gate':r['validity_gate'],'score':r['score'],
                           'failure_mode':r['failure_mode']} for r in rows]})
        summary.update(requests=len(guard.state['requests']),
                       completion_tokens_charged_or_reserved=guard.used_completion_tokens(),
                       elapsed_s=round(time.time()-summary['started_at_epoch'],3))
        write_json_atomic(HERE/'summary.json',summary)
    print(json.dumps(summary,ensure_ascii=False,indent=2),flush=True)
    return 0 if summary['status']=='completed' else 2


if __name__ == '__main__':
    parser=argparse.ArgumentParser()
    mode=parser.add_mutually_exclusive_group(required=True)
    mode.add_argument('--prepare',action='store_true')
    mode.add_argument('--execute',action='store_true')
    args=parser.parse_args()
    if args.prepare:
        prepare()
    else:
        with (HERE/'.experiment.lock').open('a') as lock:
            fcntl.flock(lock,fcntl.LOCK_EX|fcntl.LOCK_NB)
            with (HERE/'execution.log').open('a',buffering=1) as logfile:
                with contextlib.redirect_stdout(logfile),contextlib.redirect_stderr(logfile):
                    code=execute()
        raise SystemExit(code)
