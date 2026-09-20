"""Fresh B05 identity, same eight samples, two real providers, uncapped usage."""
from pathlib import Path
import argparse
import contextlib
import fcntl
import hashlib
import json
import os
import runpy
import shutil
import sys
import time
import urllib.request

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[1]
PRIOR = HERE.parent/'2026-09-05-live-smoke-minimax'
sys.path.insert(0,str(ROOT))
from runners.common import load_tasks, write_json_atomic
from runners.run_state import referenced_files
from response_ledger import ResponseLedger, EvidenceStop

GROUPS = [
    ('extract','qa_grounded','awext.clause_extract',['awx_ce_01','awx_ce_02'],[]),
    ('compliance','qa_grounded','awcom.compliance',['awc_acam_01','awc_rev_01'],[]),
    ('hidden','qa_grounded','awcom.compliance',[],['--hidden','2']),
    ('formula','design_artifact','spreadsheetbench.verified_subset',['ssb_17_35','ssb_22_47'],['--iterate','1']),
]
MODELS = {
    'minimax':{'provider':'openai_compat','model':'MiniMax-M3',
               'endpoint':'https://api.minimaxi.com/v1/chat/completions',
               'max_tokens':16384,'thinking':'provider default'},
    'glm':{'provider':'glm','model':'glm-5.3-flash',
           'endpoint':'https://open.bigmodel.cn/api/coding/paas/v4/chat/completions',
           'max_tokens':32768,'thinking':{'type':'enabled'}},
}


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def read(path):
    return json.loads(path.read_text())


def prepare():
    if (HERE/'protocol.json').exists():
        raise SystemExit('protocol already frozen; use a new directory for a new identity')
    workspace = HERE/'workspace'
    workspace.mkdir(exist_ok=True)
    (workspace/'data').symlink_to(ROOT/'data',target_is_directory=True)
    groups = []
    for name,adapter,suite,ids,flags in GROUPS:
        target = workspace/'tasks'/suite
        target.mkdir(parents=True,exist_ok=True)
        for tid in ids:
            for ext in ('.yaml','.md'):
                shutil.copy2(ROOT/'tasks'/suite/(tid+ext),target/(tid+ext))
        previous = read(PRIOR/'runs'/name/'run_manifest.json')
        groups.append({'name':name,'module':'runners.'+adapter,'suite':suite,'flags':flags,
                       'expected_task_ids':previous['extra']['selected_task_ids']})
    paths = [*ROOT.joinpath('runners').rglob('*.py'),*workspace.joinpath('tasks').rglob('*.yaml'),
             *workspace.joinpath('tasks').rglob('*.md'),HERE/'run_experiment.py',HERE/'response_ledger.py',
             ROOT/'data/awcom/compliance/hidden/generator.py',ROOT/'data/awcom/compliance/hidden/answers.b64']
    for suite in sorted({g[2] for g in GROUPS}):
        taskdir = workspace/'tasks'/suite
        paths.extend(Path(p) for p in referenced_files(load_tasks(taskdir),taskdir,{}) if Path(p).is_file())
    from runners.hidden_runtime import load_hidden_pool
    hidden,_,revision = load_hidden_pool(workspace,'awcom.compliance')
    protocol = {'version':1,'created_at_epoch':time.time(),'purpose':'B05 input contract live rerun',
        'seed':20260905,'harness_arm':'H0','budget':None,
        'budget_authorization':'User explicitly removed MiniMax/GLM budget limits; retain fixed eight samples per model.',
        'models':MODELS,'groups':groups,'hidden_pool':{'size':len(hidden),'revision':revision},
        'frozen_files':{str(p.relative_to(ROOT)):sha(p) for p in sorted(set(paths))},
        'prior_evidence_sha256':{str(p.relative_to(ROOT)):sha(p) for p in
            sorted(PRIOR.joinpath('runs').rglob('*.json'))},
        'notes':['MiniMax request settings match the prior run; only B05 input contracts changed.',
                 'GLM uses existing native preset with explicit model; no fallback or default change.',
                 'No score-driven retries or grader feedback. Provider parse retry policy unchanged.',
                 'Stop on transport or response identity uncertainty. Cache verification forbids HTTP.',
                 'Response ledger records IDs, hashes and usage, never keys or hidden prompt/answer bodies.',
                 'Small convenience sample; GLM and MiniMax use different per-response output limits.']}
    write_json_atomic(HERE/'protocol.json',protocol)
    print('Frozen same 8 task IDs for MiniMax and GLM, H0; no API calls.')


def command(group,protocol,alias):
    config = protocol['models'][alias]
    return [group['module'],'--tasks',str(HERE/'workspace/tasks'/group['suite']),
            '--out',str(HERE/alias/'runs'/group['name']), '--provider',config['provider'],
            '--model',config['model'],'--seed',str(protocol['seed']),'--resume',*group['flags']]


def invoke(argv):
    sys.argv = argv
    try:
        runpy.run_module(argv[0],run_name='__main__')
    except SystemExit as result:
        return result.code or 0
    return 0


def execute(alias):
    protocol = read(HERE/'protocol.json')
    for name,digest in {**protocol['frozen_files'],**protocol['prior_evidence_sha256']}.items():
        if sha(ROOT/name) != digest:
            raise EvidenceStop(f'frozen source/evidence changed: {name}; use a new experiment')
    config = protocol['models'][alias]
    if alias == 'minimax':
        key = os.environ.get('MINIMAX_M3_API_KEY') or os.environ.get('MINIMAX_API_KEY')
        if not key:
            raise EvidenceStop('MiniMax key is unavailable')
        os.environ.update(BM_API_BASE=config['endpoint'].removesuffix('/chat/completions'),
                          BM_MODEL=config['model'],BM_API_KEY=key)
    else:
        if not os.environ.get('GLM_API_KEY'):
            raise EvidenceStop('GLM key is unavailable')
        os.environ['GLM_BASE_URL'] = config['endpoint'].removesuffix('/chat/completions')
    directory = HERE/alias
    guard = ResponseLedger(directory/'requests.json',config,sha(HERE/'protocol.json'))
    summary = {'protocol_sha256':sha(HERE/'protocol.json'),'model':config['model'],
               'groups':[],'cache_verification':[],'started_at_epoch':time.time(),'status':'running'}
    original_opener = urllib.request.urlopen
    urllib.request.urlopen = guard.urlopen
    try:
        for group in protocol['groups']:
            guard.group = group['name']
            rc = invoke(command(group,protocol,alias))
            if rc:
                raise EvidenceStop(f'{group["name"]} runner exited {rc}')
            manifest = read(directory/'runs'/group['name']/'run_manifest.json')
            if manifest['extra']['selected_task_ids'] != group['expected_task_ids']:
                raise EvidenceStop('selected sample IDs changed')
        guard.phase = 'verify'
        requests_before = len(guard.state['requests'])
        for group in protocol['groups']:
            out = directory/'runs'/group['name']
            before = {p.name:p.read_bytes() for p in out.glob('result_*.json')}
            rc = invoke(command(group,protocol,alias))
            after = {p.name:p.read_bytes() for p in out.glob('result_*.json')}
            manifest = read(out/'run_manifest.json')
            if rc or before != after or manifest['extra']['resumed_tasks'] != len(before):
                raise EvidenceStop('matching replay failed to reuse byte-identical results')
            snapshot = {p.name:p.read_bytes() for p in out.iterdir() if not p.name.startswith('.')}
            changed = command(group,protocol,alias)
            changed[changed.index('--seed')+1] = str(protocol['seed']+1)
            rc = invoke(changed)
            if not rc or snapshot != {p.name:p.read_bytes() for p in out.iterdir() if not p.name.startswith('.')}:
                raise EvidenceStop('mismatched seed accepted or modified output')
            summary['cache_verification'].append({'group':group['name'],'n_cached':len(before),
                'results_byte_identical':True,'mismatched_seed_rejected':True,'new_http_requests':0})
        if len(guard.state['requests']) != requests_before:
            raise EvidenceStop('cache verification made an API call')
        summary['status'] = 'completed'
    except EvidenceStop as stop:
        summary.update(status='stopped',stop_reason=str(stop))
        print('[stopped]',str(stop),flush=True)
    finally:
        urllib.request.urlopen = original_opener
        for group in protocol['groups']:
            rows = [read(p) for p in sorted((directory/'runs'/group['name']).glob('result_*.json'))]
            summary['groups'].append({'name':group['name'],'n_tasks':len(rows),
                'scores':[{'task_id':r['task_id'],'gate':r['validity_gate'],'score':r['score'],
                           'failure_mode':r['failure_mode']} for r in rows]})
        requests = guard.state['requests']
        summary.update(requests=len(requests),
            usage={k:sum((r.get('usage') or {}).get(k,0) for r in requests)
                   for k in ('prompt_tokens','completion_tokens','total_tokens')},
            elapsed_s=round(time.time()-summary['started_at_epoch'],3))
        write_json_atomic(directory/'summary.json',summary)
    print(json.dumps(summary,ensure_ascii=False,indent=2),flush=True)
    return 0 if summary['status']=='completed' else 2


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    mode = parser.add_mutually_exclusive_group(required=True)
    mode.add_argument('--prepare',action='store_true')
    mode.add_argument('--execute',choices=tuple(MODELS))
    args = parser.parse_args()
    if args.prepare:
        prepare()
    else:
        folder = HERE/args.execute
        folder.mkdir(exist_ok=True)
        with (HERE/'.experiment.lock').open('a') as lock:
            fcntl.flock(lock,fcntl.LOCK_EX|fcntl.LOCK_NB)
            with (folder/'execution.log').open('a',buffering=1) as log:
                with contextlib.redirect_stdout(log),contextlib.redirect_stderr(log):
                    code = execute(args.execute)
        raise SystemExit(code)
