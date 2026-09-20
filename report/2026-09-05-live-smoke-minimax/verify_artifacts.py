"""Offline validation of the frozen experiment, recorded budget and resume evidence."""
from pathlib import Path
import hashlib
import json

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[1]


def read(path):
    return json.loads(path.read_text())


protocol = read(HERE/'protocol.json')
ledger = read(HERE/'requests.json')
summary = read(HERE/'summary.json')
prior = read(HERE.parent/'2026-09-05-live-smoke/requests.json')
assert summary['status']=='completed'
assert ledger['protocol_sha256']==summary['protocol_sha256']==hashlib.sha256((HERE/'protocol.json').read_bytes()).hexdigest()
for name,digest in protocol['frozen_files'].items():
    assert hashlib.sha256((ROOT/name).read_bytes()).hexdigest()==digest,name
requests = prior['requests']+ledger['requests']
charged = sum(r.get('usage',{}).get('completion_tokens',r['reserved_completion_tokens']) for r in requests)
assert len(requests)<=12 and charged<=50000
assert len(ledger['requests'])==8
assert all(r['status']=='received' and r['response_model']=='MiniMax-M3' and r['response_id'] for r in ledger['requests'])
assert len(summary['cache_verification'])==4
assert all(c['results_byte_identical'] and c['mismatched_seed_rejected'] and c['new_http_requests']==0 for c in summary['cache_verification'])
total = 0
for group in summary['groups']:
    folder=HERE/'runs'/group['name']
    manifest=read(folder/'run_manifest.json')
    rows=[read(p) for p in folder.glob('result_*.json')]
    assert manifest['n_tasks']==manifest['extra']['resumed_tasks']==len(rows)==group['n_tasks']==2
    assert manifest['extra']['resume_identity']['version']==1
    assert manifest['extra']['model']=='MiniMax-M3'
    assert sorted(r['task_id'] for r in rows)==sorted(manifest['extra']['selected_task_ids'])
    if group['name']=='hidden':
        for row in rows:
            assert not {'prompt','answer','raw','code'}&row['artifacts'].keys()
            fields=json.loads(row['artifacts']['layer_details']).get('fields',[])
            assert all('ref' not in f and 'got' not in f for f in fields)
    total+=len(rows)
assert total==8
previous=read(HERE.parent/'2026-09-05-trusted-resume/verification.json')
for name,digest in previous['source_sha256'].items():
    assert hashlib.sha256((ROOT/name).read_bytes()).hexdigest()==digest,name
print(f'PASS: {total} results, 4 manifests, cache verification, hidden redaction, '
      f'{len(requests)}/12 requests, {charged}/50000 output tokens used or reserved; source hashes unchanged.')
