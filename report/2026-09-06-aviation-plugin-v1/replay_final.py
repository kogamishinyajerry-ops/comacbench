"""Offline replay of frozen live answers after the external solver-budget fix.

No provider calls; keep the original live scores and trace their response hashes.
"""
import importlib
import json
from pathlib import Path
import sys
from unittest.mock import patch

sys.path.insert(0,str(Path(__file__).resolve().parents[2]))

import yaml
from runners.common import TaskSpec, environment_digest, sha256_file
from runners.providers import extract_code_block

ROOT=Path(__file__).resolve().parents[2]
REPORT=Path(__file__).resolve().parent
rows=[]
for label in ('minimax-live-v2','glm-live-v2'):
    prior=json.loads((REPORT/label/'run.json').read_text())
    for t in prior['validation']['tasks']:
        response=next((REPORT/label/'agent-audit').glob(t['id']+'-*/response.json'))
        raw=json.loads(response.read_text())['answer']
        task_path=ROOT/'packs/aviation-core-v1'/t['path']
        task=TaskSpec(yaml.safe_load(task_path.read_text()),task_path)
        module=importlib.import_module('runners.'+t['adapter'])
        with patch.object(module,'get_answer',return_value={'answer':extract_code_block(raw),
             'meta':{'provider':'external','model':'recorded-replay','source_response_sha256':sha256_file(response)}}):
            result=module.run_task(task,provider='external',model='recorded-replay',seed=0,
                env_digest=environment_digest(),prompt_cache={task.id:(task_path.parent/(task.id+'.md')).read_text()},
                assets_root=ROOT/'packs/aviation-core-v1',oracle_cache=None)
        old=next(x for x in prior['results'] if x['id']==t['id'])
        assert result['score']==old['score']
        assert result['validity_gate']==old['validity_gate']
        dest=REPORT/'replay-final'/label;dest.mkdir(parents=True,exist_ok=True)
        (dest/f'result_{task.id}.json').write_text(json.dumps(result,ensure_ascii=False,indent=2)+'\n')
        rows.append({'model_run':label,'task_id':task.id,'score':result['score'],
                     'matches_live':True,'source_response_sha256':sha256_file(response)})
summary={'kind':'offline_recorded_replay','provider_calls':0,'results':rows}
(REPORT/'replay-final/summary.json').write_text(json.dumps(summary,ensure_ascii=False,indent=2)+'\n')
print(json.dumps(summary,ensure_ascii=False))
