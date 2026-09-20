"""Offline contract, identity, provenance and prior-evidence verification."""
from pathlib import Path
import base64
import hashlib
import json
import subprocess
import sys
import yaml

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[1]
sys.path.insert(0,str(ROOT))
from runners.common import write_json_atomic


def read(path):
    return json.loads(path.read_text())


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def baseline(path):
    return subprocess.check_output(['git','show','HEAD:'+path],cwd=ROOT)


protocol = read(HERE/'protocol.json')
assert protocol['budget'] is None
for name,digest in {**protocol['frozen_files'],**protocol['prior_evidence_sha256']}.items():
    assert sha(ROOT/name) == digest, name

# Check the narrow data change independently of the generation script.
for i in range(1,6):
    path = f'tasks/awcom.compliance/awc_rev_{i:02d}.yaml'
    old,new = yaml.safe_load(baseline(path)),yaml.safe_load((ROOT/path).read_bytes())
    prompt_hash = new['input'].pop('prompt_sha256')
    old['input'].pop('prompt_sha256')
    assert old == new, path
    assert sha((ROOT/path).with_suffix('.md')) == prompt_hash
old = json.loads(base64.b64decode(baseline('data/awcom/compliance/hidden/answers.b64')))
new = json.loads(base64.b64decode((ROOT/'data/awcom/compliance/hidden/answers.b64').read_bytes()))
assert len(old) == len(new) == 45
changed = []
for before,after in zip(old,new):
    if before['prompt_sha256'] != after['prompt_sha256']:
        assert before['id'].startswith('awc_rev_')
        changed.append(before['id'])
    assert {k:v for k,v in before.items() if k!='prompt_sha256'} == {
        k:v for k,v in after.items() if k!='prompt_sha256'}
assert len(changed) == 15

output = {'status':'passed','protocol_sha256':sha(HERE/'protocol.json'),
          'public_reference_and_grader_unchanged':True,'hidden_reference_and_exact_keys_unchanged':True,
          'hidden_prompt_hashes_updated':len(changed),'frozen_source_files_checked':len(protocol['frozen_files']),
          'prior_json_artifacts_byte_identical':len(protocol['prior_evidence_sha256']), 'models':{}}
prior = HERE.parent/'2026-09-05-live-smoke-minimax'
for alias,config in protocol['models'].items():
    directory = HERE/('glm-recovery' if alias=='glm' else alias)
    summary,ledger = read(directory/'summary.json'),read(directory/'requests.json')
    assert summary['status'] == 'completed'
    if alias=='glm':
        recovery = read(directory/'protocol.json')
        assert ledger['protocol_sha256']==summary['protocol_sha256']==sha(directory/'protocol.json')
        assert recovery['parent_protocol_sha256']==summary['parent_protocol_sha256']==output['protocol_sha256']
        assert recovery['driver_sha256']==sha(HERE/'recover_glm.py')
        assert recovery['config']['transport_timeout_s']==1800
        assert len(recovery['inherited_results'])==7
        for name,digest in recovery['parent_files'].items():
            assert sha(ROOT/name)==digest,name
        for name,digest in recovery['inherited_results'].items():
            assert sha(directory/name)==digest,name
        parent_ledger = read(HERE/'glm/requests.json')
        uncertain = [r for r in parent_ledger['requests'] if r['status']!='received']
        assert len(uncertain)==1 and uncertain[0]['error_type']=='TimeoutError'
        assert all(r['status']=='received' for r in ledger['requests'])
        assert ledger['requests'][0]['request_sha256']==uncertain[0]['request_sha256']
        requests = parent_ledger['requests']+ledger['requests']
    else:
        assert ledger['protocol_sha256'] == summary['protocol_sha256'] == output['protocol_sha256']
        requests = ledger['requests']
    assert len(summary['cache_verification']) == 4
    assert all(c['n_cached']==2 and c['results_byte_identical'] and
               c['mismatched_seed_rejected'] and c['new_http_requests']==0
               for c in summary['cache_verification'])
    successful = [r for r in requests if r['status']=='received']
    assert len(successful) >= 8
    assert summary['requests']==len(requests)
    assert all(r['status']=='received' and r['response_id'] and
               r['response_model'].lower()==config['model'].lower() and
               r['request_model']==config['model'] and len(r['response_sha256'])==64
               for r in successful)
    total,gate,full = 0,0,0
    for group in protocol['groups']:
        folder = directory/'runs'/group['name']
        manifest = read(folder/'run_manifest.json')
        identity = manifest['extra']['resume_identity']
        token = hashlib.sha256(json.dumps(identity,sort_keys=True,ensure_ascii=False).encode()).hexdigest()
        rows = [read(p) for p in sorted(folder.glob('result_*.json'))]
        assert manifest['n_tasks']==manifest['extra']['resumed_tasks']==len(rows)==2
        assert sorted(r['task_id'] for r in rows)==sorted(group['expected_task_ids'])
        assert manifest['extra']['model']==identity['provider']['model']==config['model']
        assert identity['provider']['name']==config['provider']
        assert identity != read(prior/'runs'/group['name']/'run_manifest.json')['extra']['resume_identity']
        if alias == 'glm':
            assert identity != read(HERE/'minimax/runs'/group['name']/'run_manifest.json')['extra']['resume_identity']
            assert identity == read(HERE/'glm/runs'/group['name']/'run_manifest.json')['extra']['resume_identity']
        for row in rows:
            assert row['artifacts']['resume_identity']==token
            metadata = json.loads(row['artifacts']['model_meta'])
            assert metadata['model'].lower()==config['model'].lower()
            if group['name']=='hidden':
                assert not {'prompt','answer','raw','code'} & row['artifacts'].keys()
                details = json.loads(row['artifacts']['layer_details'])
                assert all('ref' not in f and 'got' not in f for f in details.get('fields',[]))
            total += 1
            gate += row['validity_gate']==1
            full += row['score']==1
        recorded = next(g for g in summary['groups'] if g['name']==group['name'])
        assert recorded['n_tasks']==len(rows)
        assert recorded['scores']==[{'task_id':r['task_id'],'gate':r['validity_gate'],
            'score':r['score'],'failure_mode':r['failure_mode']} for r in rows]
    assert total==8
    output['models'][alias] = {'model':config['model'],'results':total,'gate_passed':gate,
        'full_score':full,'requests':len(requests),'usage':summary['usage'],
        'result_directory':directory.name,
        'uncertain_requests':len(requests)-len(successful),
        'cached_results_byte_identical':8,'mismatched_seed_rejected_groups':4,
        'response_models_verified':True,'new_identity_verified':True}

write_json_atomic(HERE/'verification.json',output)
print(json.dumps(output,ensure_ascii=False,indent=2))
