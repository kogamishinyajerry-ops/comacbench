"""Offline post-run diagnostic: submit unchanged input to the production grader."""
from pathlib import Path
import hashlib
import json
import sys
import time
import urllib.request

HERE=Path(__file__).resolve().parent
ROOT=HERE.parents[1]
sys.path.insert(0,str(ROOT))
from runners.common import load_tasks,write_json_atomic
from runners.design_artifact import _run_formula_task


def no_http(*args,**kwargs):
    raise AssertionError('offline negative control must not call providers')


def main():
    protocol=json.loads((HERE/'protocol.json').read_text())
    for name,digest in protocol['frozen_files'].items():
        assert hashlib.sha256((ROOT/name).read_bytes()).hexdigest()==digest,name
    target=HERE/'negative-control'
    if target.exists():raise SystemExit('preserve existing negative-control evidence')
    target.mkdir()
    urllib.request.urlopen=no_http
    rows=[]
    for task in load_tasks(HERE/'workspace/tasks/spreadsheetbench.verified_subset'):
        filename=Path(task['input']['assets'][0]['path']).name
        code=f'import shutil\nshutil.copyfile({filename!r}, "output.xlsx")\n'
        row=_run_formula_task(task,code,{'provider':'offline-negative-control','model':'unchanged-input'},
            time.time(),'sha256:'+hashlib.sha256(b'offline-negative-control').hexdigest(),[],ROOT)
        write_json_atomic(target/f'result_{task.id}.json',row)
        rows.append({'task_id':task.id,'gate':row['validity_gate'],'score':row['score'],
            'subscores':row['subscores'],'grade_details':json.loads(row['artifacts']['grade_details'])})
    assert len(rows)==6 and all(r['gate']==1 for r in rows)
    deletion=next(r for r in rows if r['task_id']=='ssb_455_35')
    assert deletion['score']==1,'negative control no longer reproduces the deletion scoring defect'
    summary={'kind':'offline unchanged-input negative control, not real model evidence',
        'timing':'post-run diagnostic; did not select samples or alter frozen model scores',
        'api_requests':0,'protocol_sha256':hashlib.sha256((HERE/'protocol.json').read_bytes()).hexdigest(),
        'status':'reproduced_scoring_defect','results':rows}
    write_json_atomic(target/'summary.json',summary)
    print(json.dumps({'status':summary['status'],'api_requests':0,
        'scores':{r['task_id']:r['score'] for r in rows}},indent=2))


if __name__=='__main__':main()
