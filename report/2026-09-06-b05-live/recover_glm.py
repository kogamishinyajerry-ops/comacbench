"""Preserve the timed-out attempt; resume its verified seven results in a fresh directory."""
from pathlib import Path
import contextlib
import fcntl
import json
import os
import shutil
import time
import urllib.request
import run_experiment as experiment
from response_ledger import ResponseLedger, EvidenceStop
from runners.common import write_json_atomic

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[1]
DEST = HERE/'glm-recovery'


def execute():
    protocol = experiment.read(HERE/'protocol.json')
    original_summary = experiment.read(HERE/'glm/summary.json')
    assert original_summary['status']=='stopped' and 'TimeoutError' in original_summary['stop_reason']
    for name,digest in {**protocol['frozen_files'],**protocol['prior_evidence_sha256']}.items():
        assert experiment.sha(ROOT/name)==digest,name
    config = {**protocol['models']['glm'],'transport_timeout_s':1800}
    protocol['models']['glm-recovery'] = config
    recovery_path = DEST/'protocol.json'
    if not recovery_path.exists():
        parent_files = {str(p.relative_to(ROOT)):experiment.sha(p)
                        for p in sorted((HERE/'glm').rglob('*')) if p.is_file()}
        shutil.copytree(HERE/'glm/runs',DEST/'runs')
        inherited = {str(p.relative_to(DEST)):experiment.sha(p)
                     for p in sorted((DEST/'runs').rglob('result_*.json'))}
        assert len(inherited)==7
        write_json_atomic(recovery_path,{'parent_protocol_sha256':experiment.sha(HERE/'protocol.json'),
            'parent_files':parent_files,'inherited_results':inherited,'config':config,
            'driver_sha256':experiment.sha(Path(__file__)),
            'reason':'Resume missing result after an uncertain timeout; model/prompt/seed unchanged.',
            'budget':None,'created_at_epoch':time.time()})
    recovery = experiment.read(recovery_path)
    assert recovery['config']==config
    assert recovery['driver_sha256']==experiment.sha(Path(__file__))
    for name,digest in recovery['parent_files'].items():
        assert experiment.sha(ROOT/name)==digest,name
    if not os.environ.get('GLM_API_KEY'):
        raise EvidenceStop('GLM_API_KEY unavailable')
    os.environ['GLM_BASE_URL'] = config['endpoint'].removesuffix('/chat/completions')
    guard = ResponseLedger(DEST/'requests.json',config,experiment.sha(recovery_path))
    transport = guard.transport
    def longer_wait(request,*args,**kwargs):
        kwargs['timeout'] = config['transport_timeout_s']
        return transport(request,*args,**kwargs)
    guard.transport = longer_wait
    summary = {'protocol_sha256':experiment.sha(recovery_path),
        'parent_protocol_sha256':experiment.sha(HERE/'protocol.json'),'model':config['model'],
        'groups':[],'cache_verification':[],'status':'running','started_at_epoch':time.time(),
        'inherited_completed_results':7,'transport_timeout_s':1800}
    opener = urllib.request.urlopen
    urllib.request.urlopen = guard.urlopen
    try:
        for group in protocol['groups']:
            guard.group = group['name']
            rc = experiment.invoke(experiment.command(group,protocol,'glm-recovery'))
            if rc:
                raise EvidenceStop(f'{group["name"]} exited {rc}')
        guard.phase = 'verify'
        count = len(guard.state['requests'])
        for group in protocol['groups']:
            out = DEST/'runs'/group['name']
            before = {p.name:p.read_bytes() for p in out.glob('result_*.json')}
            rc = experiment.invoke(experiment.command(group,protocol,'glm-recovery'))
            manifest = experiment.read(out/'run_manifest.json')
            assert not rc and before=={p.name:p.read_bytes() for p in out.glob('result_*.json')}
            assert manifest['extra']['resumed_tasks']==2
            assert manifest['extra']['selected_task_ids']==group['expected_task_ids']
            previous = experiment.read(HERE/'glm/runs'/group['name']/'run_manifest.json')
            assert manifest['extra']['resume_identity']==previous['extra']['resume_identity']
            snapshot = {p.name:p.read_bytes() for p in out.iterdir() if not p.name.startswith('.')}
            changed = experiment.command(group,protocol,'glm-recovery')
            changed[changed.index('--seed')+1] = str(protocol['seed']+1)
            rc = experiment.invoke(changed)
            assert rc and snapshot=={p.name:p.read_bytes() for p in out.iterdir() if not p.name.startswith('.')}
            summary['cache_verification'].append({'group':group['name'],'n_cached':2,
                'results_byte_identical':True,'mismatched_seed_rejected':True,'new_http_requests':0})
        assert len(guard.state['requests'])==count
        for name,digest in recovery['inherited_results'].items():
            assert experiment.sha(DEST/name)==digest,name
        summary['status'] = 'completed'
    except EvidenceStop as stop:
        summary.update(status='stopped',stop_reason=str(stop))
        print('[stopped]',str(stop),flush=True)
    finally:
        urllib.request.urlopen = opener
        for group in protocol['groups']:
            rows = [experiment.read(p) for p in sorted((DEST/'runs'/group['name']).glob('result_*.json'))]
            summary['groups'].append({'name':group['name'],'n_tasks':len(rows),
                'scores':[{'task_id':r['task_id'],'gate':r['validity_gate'],'score':r['score'],
                           'failure_mode':r['failure_mode']} for r in rows]})
        requests = experiment.read(HERE/'glm/requests.json')['requests']+guard.state['requests']
        summary.update(requests=len(requests),new_requests=len(guard.state['requests']),
            uncertain_requests=sum(r['status']!='received' for r in requests),
            usage={k:sum((r.get('usage') or {}).get(k,0) for r in requests)
                   for k in ('prompt_tokens','completion_tokens','total_tokens')},
            usage_note='Known response usage only; original timeout usage is unknown.',
            elapsed_s=round(time.time()-summary['started_at_epoch'],3))
        write_json_atomic(DEST/'summary.json',summary)
    print(json.dumps(summary,ensure_ascii=False,indent=2),flush=True)
    return 0 if summary['status']=='completed' else 2


if __name__=='__main__':
    DEST.mkdir(exist_ok=True)
    with (HERE/'.experiment.lock').open('a') as lock:
        fcntl.flock(lock,fcntl.LOCK_EX|fcntl.LOCK_NB)
        with (DEST/'execution.log').open('a',buffering=1) as log:
            with contextlib.redirect_stdout(log),contextlib.redirect_stderr(log):
                code = execute()
    raise SystemExit(code)
