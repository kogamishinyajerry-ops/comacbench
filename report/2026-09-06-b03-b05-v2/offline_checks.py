"""Production run_task controls and prior-public-code replay; no provider requests."""
from pathlib import Path
import hashlib
import json
import sys
import urllib.request

HERE=Path(__file__).resolve().parent
ROOT=HERE.parents[1]
PRIOR=ROOT/'report/2026-09-06-expanded-24-v2'
sys.path.insert(0,str(ROOT))
from runners.common import load_tasks,environment_digest,write_json_atomic
from runners.design_artifact import run_task
from runners.providers import extract_code_block,strip_think


def read(p):return json.loads(p.read_text())
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def no_http(*args,**kwargs):raise AssertionError('offline check attempted HTTP')


def main():
    out=HERE/'offline'
    if out.exists():raise SystemExit('preserve existing offline evidence')
    out.mkdir();urllib.request.urlopen=no_http
    preflight={r['task_id']:r for r in read(HERE/'table-preflight.json')}
    tasks=[t for t in load_tasks(ROOT/'tasks/spreadsheetbench.verified_subset') if t.id in preflight]
    digest=environment_digest()
    def evaluate(task,code,arm):
        folder=out/arm;folder.mkdir(exist_ok=True)
        code_path=folder/f'{task.id}.py';code_path.write_text(code)
        row=run_task(task,provider='oracle',model=None,seed=20260906,env_digest=digest,
            prompt_cache={task.id:'Offline fixture code; no prompt sent to a model'},assets_root=ROOT,
            oracle_cache={task.id:code})
        row['artifacts']['offline_evidence']=json.dumps({'kind':arm,'source_sha256':sha(code_path),
            'notice':'offline fixture or replay; not a new model response'})
        write_json_atomic(folder/f'result_{task.id}.json',row)
        print(arm,task.id,row['validity_gate'],row['score'],flush=True)
        return {'task_id':task.id,'gate':row['validity_gate'],'score':row['score'],
                'physics':row['subscores']['physics'],'failure_mode':row['failure_mode']}
    controls=[];replays=[]
    for task in tasks:
        tid=task.id;g=task['grader'];tol=1e-12 if tid=='ssb_341_40' else 0
        g['numeric_rel_tol']=task['reference']['rel_tol']=tol
        input_file=Path(task['input']['assets'][0]['path']).name
        correct=(ROOT/g['oracle_source']).read_text()
        changed=preflight[tid]['changed_cells']
        reset=changed[:max(1,len(changed)//2)]
        suffix=('\nimport openpyxl\nw=openpyxl.load_workbook("output.xlsx")\n'
                f's=w[{g["answer_sheet"]!r}]\n')
        partial=(correct+suffix+f'initial=openpyxl.load_workbook({input_file!r})\n'
            f'for coordinate in {reset!r}:\n'
            f'    s[coordinate]=initial[{g["answer_sheet"]!r}][coordinate].value\n'
            'initial.close()\nw.save("output.xlsx")\nw.close()\n')
        # A known coordinate in the declared region; incorrect independent of input/gold values.
        damaged=correct+suffix+f's[{changed[0]!r}]="__NEGATIVE_CONTROL_WRONG__"\nw.save("output.xlsx")\nw.close()\n'
        rows={arm:evaluate(task,code,arm) for arm,code in [
            ('correct',correct),('unchanged',f'import shutil\nshutil.copyfile({input_file!r},"output.xlsx")\n'),
            ('partial',partial),('damaged',damaged)]}
        assert rows['correct']['score']==1 and all(r['gate']==1 for r in rows.values()),tid
        assert all(rows[a]['score']<1 for a in ['unchanged','partial','damaged']),tid
        controls.append({'task_id':tid,**{k:v['score'] for k,v in rows.items()}})
        for alias in ['minimax','glm']:
            ledger=read(PRIOR/alias/'requests.json')
            request=next(r for r in reversed(ledger['requests']) if r['task_id']==tid)
            response_path=PRIOR/alias/request['public_response_file']
            assert sha(response_path)==request['response_sha256']
            response=read(response_path)
            code=extract_code_block(strip_think(response['choices'][0]['message']['content']))
            assert code,tid
            replay=evaluate(task,code,'replay-'+alias)
            old=read(PRIOR/alias/'runs/formula'/f'result_{tid}.json')
            replay.update(model=alias,prior_score=old['score'],prior_gate=old['validity_gate'],
                          response_sha256=request['response_sha256'])
            replays.append(replay)
    source_paths=[*ROOT.joinpath('runners').glob('*.py'),HERE/'offline_checks.py',HERE/'table-preflight.json']
    for task in tasks:
        source_paths.extend([task.yaml_path,task.yaml_path.with_suffix('.md'),
            ROOT/task['input']['assets'][0]['path'],ROOT/task['grader']['golden_workbook'],
            ROOT/task['grader']['oracle_source']])
    summary={'status':'passed','api_requests':0,'controls':controls,'prior_code_replays':replays,
        'source_hashes':{str(p.relative_to(ROOT)):sha(p) for p in sorted(set(source_paths))}}
    write_json_atomic(out/'summary.json',summary)
    print('PASS: 24 controls, 12 prior-code replays, zero API requests')


if __name__=='__main__':main()
