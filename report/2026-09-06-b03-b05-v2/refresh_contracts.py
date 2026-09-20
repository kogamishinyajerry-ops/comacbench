"""Surgical prompt/hash refresh; assert references, keys and remaining specs unchanged."""
from pathlib import Path
import base64
import hashlib
import json
import re
import sys
import yaml

HERE=Path(__file__).resolve().parent
ROOT=HERE.parents[1]
sys.path.insert(0,str(ROOT))
from runners import gen_tasks_awcom,gen_tasks_office2


def main():
    saved=json.loads((HERE/'task-specs-before.json').read_text())
    mod=gen_tasks_awcom._load_gen_module()
    changed=[]
    for relative,before in saved.items():
        path=ROOT/relative;old=yaml.safe_load(before);tid=old['id']
        prompt=path.with_suffix('.md').read_text()
        if tid.startswith('awx_ce_'):
            card=gen_tasks_office2.synth_clause_card(int(tid.rsplit('_',1)[1])-1)
            prompt=gen_tasks_office2.clause_prompt(card)
            assert gen_tasks_office2.clause_ref_json(card)==old['reference']['reference_json']
        elif tid.startswith(('awc_acam_','awc_trc_')):
            family=tid.split('_')[1]
            prompt,ref=mod.GENS[family](1000+int(tid.rsplit('_',1)[1]))
            assert ref==old['reference']['reference_json']
        elif tid in gen_tasks_office2.SSB_PROMPT_CLARIFICATIONS:
            suffix=gen_tasks_office2.SSB_PROMPT_CLARIFICATIONS[tid]
            if not prompt.endswith(suffix):prompt+=suffix
        digest=hashlib.sha256(prompt.encode()).hexdigest()
        if digest==old['input']['prompt_sha256']:continue
        text,count=re.subn(r'(prompt_sha256: )[0-9a-f]{64}',r'\g<1>'+digest,before)
        assert count==1
        amended=yaml.safe_load(text);amended['input']['prompt_sha256']=old['input']['prompt_sha256']
        assert amended==old
        path.with_suffix('.md').write_text(prompt);path.write_text(text);changed.append(tid)
    baseline=json.loads(base64.b64decode((HERE/'before/answers.b64').read_bytes()))
    pool={item['id']:item for item in mod.gen()['pool']}
    for row in baseline:
        item=pool[row['id']]
        assert row['reference_json']==item['reference_json'] and row['exact_keys']==item['exact_keys']
        row['prompt_sha256']=hashlib.sha256(item['prompt'].encode()).hexdigest()
    (ROOT/'data/awcom/compliance/hidden/answers.b64').write_bytes(
        base64.b64encode(json.dumps(baseline,ensure_ascii=False).encode()))
    (HERE/'contract-refresh.json').write_text(json.dumps({'changed_public_tasks':changed,
        'public_reference_grader_weights_unchanged':True,'hidden_reference_and_exact_keys_unchanged':True,
        'hidden_pool_tasks':len(baseline)},indent=2))
    print('public prompt/hash refresh',len(changed),'hidden references unchanged',len(baseline))


if __name__=='__main__':main()
