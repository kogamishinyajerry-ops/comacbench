"""Sequential offline calibration, then freeze; does not start live providers."""
from pathlib import Path
import json
import subprocess
import sys

HERE=Path(__file__).resolve().parent
ROOT=HERE.parents[1]


def run(args,log):
    print('start',log,flush=True)
    with (HERE/log).open('x') as output:
        result=subprocess.run([sys.executable,*args],cwd=ROOT,stdout=output,stderr=subprocess.STDOUT)
    if result.returncode:raise SystemExit(f'calibration stopped: {log}')
    print('completed',log,flush=True)


if __name__=='__main__':
    run(['-m','runners.design_artifact','--tasks','tasks/spreadsheetbench.verified_subset',
         '--out',str(HERE/'oracle-suite'),'--provider','oracle','--seed','20260906','--iterate','1'],
        'oracle-suite.log')
    rows=[json.loads(p.read_text()) for p in (HERE/'oracle-suite').glob('result_*.json')]
    assert len(rows)==25 and all(r['validity_gate']==1 and r['score']==1 for r in rows)
    run([str(HERE/'offline_checks.py')],'offline.log')
    run([str(HERE/'run_experiment.py'),'--prepare'],'prepare.log')
    run([str(HERE/'run_experiment.py'),'--execute','oracle'],'oracle.log')
    summary=json.loads((HERE/'oracle/summary.json').read_text())
    rows=[r for g in summary['groups'] for r in g['scores']]
    assert len(rows)==24 and all(r['gate']==1 and r['score']==1 for r in rows)
    assert summary['requests']==0
    print('PASS: 25 canonical oracles, 24 controls, 12 replays, 24 protocol oracles. No API calls.',flush=True)
