"""Reference fixture for interface verification ONLY; has privileged answers by design."""
import json
from pathlib import Path
import sys

request=json.load(sys.stdin)
tid=request['task_id']
answers=Path(__file__).with_name('reference_answers')
if tid not in {'beam_static_01','data_units_01','ontology_trace_01'}:
    raise ValueError('unknown reference fixture')
print(json.dumps({'protocol':'comacbench.agent.v1','task_id':tid,
                  'answer':(answers/f'{tid}.py').read_text()},ensure_ascii=False))
