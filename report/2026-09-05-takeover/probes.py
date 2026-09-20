"""Bounded offline behavioral probes; all runner output goes to new temp directories.
No live model calls. Exit 0 means probes completed; inspect observations for defects.
"""
from pathlib import Path
import ast
import copy
import json
import subprocess
import sys
import tempfile
import time
import yaml

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))
from runners.common import TaskSpec
from runners.qa_grounded import grade_json_extract
from runners.sandbox import IsolatedRun, static_check

observations = {}
out = Path(tempfile.mkdtemp(prefix='comacbench-takeover-probes-'))

# Invalid inputs first: strict discrete values must not receive partial tolerance.
s, _ = grade_json_extract({'amendment_year': 2022, 'cycles': 1000},
                          {'amendment_year': 1990, 'cycles': 990},
                          exact_keys=['amendment_year', 'cycles'])
assert s == 0
observations['discrete_wrong_values_rejected'] = True

p = sorted((ROOT / 'tasks/awext.clause_extract').glob('*.yaml'))[0]
spec = yaml.safe_load(p.read_text())
bad = copy.deepcopy(spec)
bad['limits']['wall_clock_s'] = -1
bad['scoring']['weights']['requirements'] = -1
try:
    TaskSpec(bad, p)
    observations['invalid_limits_and_weights_accepted_at_load'] = True
except (ValueError, TypeError):
    observations['invalid_limits_and_weights_accepted_at_load'] = False

# Benign, self-created canary only. This checks filesystem scope, not OS exploitation.
canary = out / 'outside-sandbox-canary.txt'
canary.write_text('COMACBENCH_CANARY')
code = f'print(open({str(canary)!r}).read() == "COMACBENCH_CANARY")'
violations, syntax_ok = static_check(code)
iso = IsolatedRun()
r = iso.run(iso.write('read_canary.py', code), 5)
observations['outside_cwd_read'] = {
    'static_violations': violations, 'syntax_ok': syntax_ok,
    'child_exit': r['exit'], 'read_own_canary_successfully': r['stdout'].strip() == 'True',
}

# A real spreadsheet conversion on a tiny fictional fixture, never user documents.
import openpyxl
from runners.design_artifact import _run_formula_task
formula_file = sorted((ROOT / 'tasks/spreadsheetbench.verified_subset').glob('*.yaml'))[0]
formula_spec = yaml.safe_load(formula_file.read_text())
gold = out / 'golden.xlsx'
wb = openpyxl.Workbook()
wb.active.title = 'RequiredSheet'
wb.active['A1'] = 42
wb.save(gold)
wb.close()
formula_spec['input']['assets'] = []
formula_spec['grader'].update(answer_sheet='RequiredSheet', answer_position='A1:A1', golden_workbook=str(gold))
formula_spec['scoring']['weights'] = {'physics': 0.5, 'requirements': 0.5, 'objective': 0.0, 'robustness': 0.0}
candidate = 'import openpyxl\nw=openpyxl.Workbook()\nw.active.title="WrongSheet"\nw.active["A1"]=42\nw.save("output.xlsx")\nw.close()\n'
fr = _run_formula_task(TaskSpec(formula_spec, formula_file), candidate, {}, time.time(),
                       'takeover-fixture', [], ROOT)
observations['formula_wrong_sheet'] = {'gate': fr['validity_gate'], 'score': fr['score'],
                                      'gate_failures': fr['gate_failures'],
                                      'required_sheet': 'RequiredSheet', 'candidate_sheet': 'WrongSheet'}

def qa_run(tasks, dest, *flags):
    cmd = [sys.executable, '-m', 'runners.qa_grounded', '--tasks', tasks,
           '--out', str(dest), '--provider', 'oracle', *flags]
    r = subprocess.run(cmd, cwd=ROOT, capture_output=True, text=True, timeout=60)
    if r.returncode:
        raise RuntimeError(r.stderr[-1000:])
    rows = [json.loads(f.read_text()) for f in sorted(dest.glob('result_*.json'))]
    return {'command': cmd, 'exit': r.returncode, 'count': len(rows),
            'gate_passed': sum(x['validity_gate'] == 1 for x in rows),
            'mean': sum(x['score'] for x in rows) / len(rows)}

# Bad cached identity/environment must not be silently trusted by --resume.
resume = out / 'invalid-resume'
resume.mkdir()
source = next((ROOT / 'results/awext.clause_extract').glob('*/*/result_' + spec['id'] + '.json'))
cached = json.loads(source.read_text())
cached['task_id'] = 'takeover-wrong-task-id'
cached['environment_digest'] = 'sha256:takeover-sentinel'
target = resume / ('result_' + spec['id'] + '.json')
target.write_text(json.dumps(cached))
resume_stats = qa_run('tasks/awext.clause_extract', resume, '--resume')
observations['resume'] = {**resume_stats,
    'wrong_cached_identity_preserved': json.loads(target.read_text())['task_id'] == 'takeover-wrong-task-id',
    'wrong_cached_environment_preserved': json.loads(target.read_text())['environment_digest'] == 'sha256:takeover-sentinel'}

observations['awext_oracle'] = qa_run('tasks/awext.clause_extract', out / 'awext-oracle')
observations['awcom_hidden_oracle'] = qa_run('tasks/awcom.compliance', out / 'awcom-oracle-hidden', '--hidden', '8')
m = json.loads((out / 'awcom-oracle-hidden/run_manifest.json').read_text())
observations['hidden_manifest'] = {'recorded_n_tasks': m['n_tasks'],
    'requested_hidden_n': m['extra']['hidden_n'],
    'rerun_contains_hidden': '--hidden ' in m['rerun_command']}

files = list((ROOT / 'runners').rglob('*.py'))
for f in files:
    ast.parse(f.read_text(), filename=str(f))
observations['runner_python_syntax_pass'] = len(files)
print(json.dumps({'note': 'Observed behavior, not a global PASS verdict.',
                  'temporary_output': str(out), 'observations': observations},
                 ensure_ascii=False, indent=2))
