"""Privileged fixture: interface proof only, not a model. Reads no grader paths."""
import hashlib,json,sys
from pathlib import Path
r=json.load(sys.stdin)
assert r["task_id"]=="backward_step_01"
assert len(r['assets'])==8
for asset in r['assets']:
    p=Path(asset['path'])
    assert p.is_file() and str(p).startswith('inputs/')
    assert hashlib.sha256(p.read_bytes()).hexdigest()==asset['sha256']
print(json.dumps({"protocol":"comacbench.agent.v1","task_id":r["task_id"],"answer":Path(__file__).with_name("cfd_reference_answer.py").read_text()}))
