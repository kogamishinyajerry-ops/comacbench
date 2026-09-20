"""Verify retained evidence without calling a provider or rewriting prior results."""
from pathlib import Path
import hashlib
import json
import re
import sys

ROOT = Path(__file__).resolve().parents[2]
REPORT = Path(__file__).resolve().parent
sys.path.insert(0, str(ROOT))
from comacbench.__main__ import engine_identity
from comacbench.pack import fingerprint


def read(path):
    return json.loads(path.read_text())


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


history = read(REPORT / 'prior-artifacts.json')
for path, expected in history.items():
    assert sha(ROOT / path) == expected, path
v1 = read(ROOT / 'report/2026-09-06-aviation-plugin-v1/reference-final/run.json')
assert fingerprint(ROOT / 'packs/aviation-core-v1') == v1['identity']['pack_sha256']
engine = engine_identity()
rows = {}
for label in ('calibration-final', 'reference-interface', 'minimax-replay', 'glm-replay'):
    doc = read(REPORT / label / 'run.json')
    assert doc['status'] == 'complete'
    assert doc['identity']['engine'] == engine, label
    assert doc['identity']['pack_sha256'] == fingerprint(ROOT / 'packs/aviation-structures-v2')
    assert len(doc['results']) == 1
    row = doc['results'][0]
    assert sha(Path(row['result_file'])) == row['result_sha256']
    result = read(Path(row['result_file']))
    evidence = json.loads(result['artifacts']['engineering_evidence'])
    assert evidence['complete']
    for name, item in evidence['files'].items():
        assert hashlib.sha256(item['text'].encode()).hexdigest() == item['sha256'], name
    audit = row['details']['deck_audit']
    if label.endswith('replay'):
        assert row['validity_gate'] == 0 and row['score'] == 0
        assert doc['agent']['agent_kind'] == 'recorded_replay'
        assert audit['summary']['unconnected_loaded_nodes'] == 8
        assert 'ccx_s' not in row['details']
        assert 'model.dat' not in evidence['files']
        assert len(list((REPORT / label / 'agent-audit').glob('*/request.json'))) == 1
    else:
        assert row['full_pass'] and row['score'] == 1 and audit['passed']
        assert len(audit['checks']) == 6 and all(c['status'] == 'pass' for c in audit['checks'])
        assert evidence['files']['model.dat']['origin'] == 'solver'
        assert 'Job finished' in evidence['files']['model.solver.log']['text']
    rows[label] = {'score': row['score'], 'gate': row['validity_gate'], 'evidence_level': row['evidence_level']}
    if label == 'calibration-final':
        assert doc['calibration_passed']
        assert len(doc['controls']) == 8
        assert all(c['passed'] and c['score'] == 0 and c['expected_issue'] in c['actual_issues'] for c in doc['controls'])
for item in read(REPORT / 'replay-agents/provenance.json'):
    assert item['provider_calls'] == 0
    assert sha(ROOT / item['source']) == item['sha256']
    assert sha(REPORT / 'replay-agents' / (item['model'] + '.json')) == item['sha256']
first = read(REPORT / 'calibration/run.json')
for path, expected in first['identity']['engine'].items():
    assert sha(REPORT / 'calibration-source' / path) == expected
resume = read(REPORT / 'resume.json')
assert resume['new_agent_requests'] == 0 and resume['wrong_seed_state_unchanged'] and resume['result_bytes_unchanged']
invalid = read(REPORT / 'contribution-feedback/validation.json')
assert not invalid['runnable'] and not (REPORT / 'must-not-run').exists()
assert {'missing_file', 'invalid_deck_contract', 'invalid_tolerance'} <= {i['code'] for i in invalid['issues']}
log = (REPORT / 'all-tests.log').read_text()
assert re.search(r'Ran 66 tests.*\n\nOK', log, re.S)
assert 'factory 格式断言通过' in (REPORT / 'workbench-build.log').read_text()
assert read(REPORT / 'plugin-tests-final.log')['invalid_pack_agent_launches'] == 0
summary = {'passed': True, 'tests': 66, 'reference_full_pass': 1, 'negative_controls_detected': 8,
           'external_reference_full_pass': 1, 'recorded_replays': 2, 'live_provider_calls': 0,
           'historical_files_unchanged': len(history), 'v1_pack_unchanged': True,
           'same_identity_new_requests': 0, 'wrong_identity_rejected': True,
           'invalid_contribution_blockers': invalid['summary']['blocker'],
           'invalid_contribution_agent_calls': 0, 'runs': rows,
           'published': False, 'active_dsh_mounted': False}
print(json.dumps(summary, ensure_ascii=False, indent=2))
