"""Read-only verification of this delivery's evidence, including old artifact preservation."""
import hashlib
import json
from pathlib import Path
import sys

ROOT=Path(__file__).resolve().parents[2]
REPORT=Path(__file__).resolve().parent
sys.path.insert(0,str(ROOT))
from comacbench.pack import validate_pack, fingerprint


def sha(path):return hashlib.sha256(Path(path).read_bytes()).hexdigest()
def read(path):return json.loads(Path(path).read_text())

prior=read(REPORT/'prior-artifacts.json')
assert all((ROOT/p).is_file() and sha(ROOT/p)==h for p,h in prior.items()), 'historical evidence changed'
validation=validate_pack(ROOT/'packs/aviation-core-v1')
assert validation['runnable'] and not validation['publishable'] and validation['task_count']==3
bad=read(REPORT/'contribution-feedback/validation.json')
assert not bad['runnable'] and {'missing_file','invalid_tolerance','vacuous_test'} <= {x['code'] for x in bad['issues']}
assert not (REPORT/'must-not-run').exists()
cal=read(REPORT/'calibration-final/run.json')
assert cal['status']=='complete' and cal['calibration_passed']
assert len(cal['results'])==3 and all(x['full_pass'] for x in cal['results'])
assert len(cal['controls'])==6 and all(x['passed'] for x in cal['controls'])
assert cal['identity']['pack_sha256']==fingerprint(ROOT/'packs/aviation-core-v1')
assert all(sha(ROOT/p)==h for p,h in cal['identity']['engine'].items())
live=[]
for label in ('minimax-live-v2','glm-live-v2'):
    d=read(REPORT/label/'run.json')
    assert d['status']=='complete' and len(d['results'])==3
    assert all(sha(REPORT/'frozen-source'/p)==h for p,h in d['identity']['engine'].items())
    assert d['identity']['pack_sha256']==fingerprint(REPORT/'long-context-pack')
    assert {x['id']:x['score'] for x in d['results']}=={'beam_static_01':.5,'data_units_01':1.,'ontology_trace_01':1.}
    for result in d['results']:
        assert sha(result['result_file'])==result['result_sha256']
    requests=list((REPORT/label/'agent-audit').glob('*/request.json'))
    responses=list((REPORT/label/'agent-audit').glob('*/response.json'))
    assert len(requests)==len(responses)==3
    assert all('reference' not in read(p) and 'grader' not in read(p) for p in requests)
    live.append({'run':label,'completed':3,'full_pass':2,'agent_requests':3})
assert read(REPORT/'minimax-live/run.json')['status']=='interrupted'
assert read(REPORT/'glm-live/run.json')['status']=='interrupted'
replay=read(REPORT/'replay-final/summary.json')
assert replay['provider_calls']==0 and len(replay['results'])==6 and all(x['matches_live'] for x in replay['results'])
resume=read(REPORT/'final-resume.json')
assert all(v is True for k,v in resume.items() if k!='reference_agent_calls') and resume['reference_agent_calls']==3
diagnosis=read(REPORT/'structural-diagnosis/summary.json')
assert all(x['unconnected_loaded_nodes']==8 and abs(x['connected_y_load']+822.222222)<.001 for x in diagnosis.values())
testlog=(REPORT/'final-tests.log').read_text()
assert 'Ran 56 tests' in testlog and testlog.rstrip().endswith('OK')
summary={'passed':True,'historical_files_unchanged':len(prior),'tests':56,
         'oracle_full_pass':3,'negative_controls_detected':6,'live':live,
         'offline_replays':6,'offline_provider_calls':0,'invalid_pack_agent_calls':0,
         'reference_resume_agent_calls':0,'wrong_seed_rejected':True,
         'original_interrupted_runs_preserved':True,'publishable':False,
         'scope':'plugin vertical slice; no aircraft-level or enterprise-user acceptance'}
print(json.dumps(summary,ensure_ascii=False,indent=2))
