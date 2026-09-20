"""Read-only repository inventory. JSON on stdout; no runners/providers are invoked.
Run from the repository root: .venv/bin/python report/2026-09-05-takeover/inventory.py
Exit 0 means inventory completed, NOT that all assets/runs are valid.
"""
from pathlib import Path
from collections import Counter
from functools import lru_cache
import hashlib
import json
import math
import subprocess
import yaml

ROOT = Path(__file__).resolve().parents[2]

def git(*args):
    return subprocess.check_output(['git', *args], cwd=ROOT, text=True).strip()

@lru_cache(maxsize=None)
def digest(rel):
    p = ROOT / rel
    if not p.is_file():
        return None
    h = hashlib.sha256()
    with p.open('rb') as f:
        for block in iter(lambda: f.read(1048576), b''):
            h.update(block)
    return h.hexdigest()

def counts(values):
    return dict(sorted(Counter(values).items()))

def read_json(p):
    return json.loads(p.read_text())

reg = yaml.safe_load((ROOT / 'registry/registry.yaml').read_text())['entries']
entries = {e['id']: e for e in reg}
tasks = {}
issues = []
noncanonical = []
required = ['id', 'registry_id', 'domain', 'task_type', 'model_profile',
            'assets_revision', 'allowed_tools', 'input', 'output_contract',
            'grader', 'scoring', 'limits', 'license_provenance']
for folder in sorted((ROOT / 'tasks').iterdir()):
    if not folder.is_dir():
        continue
    files = sorted(folder.glob('*.yaml'))
    if folder.name not in entries:
        noncanonical.append({'directory': str(folder.relative_to(ROOT)), 'yaml_count': len(files)})
        continue
    for p in files:
        t = yaml.safe_load(p.read_text())
        rel = str(p.relative_to(ROOT))
        if any(k not in t for k in required):
            issues.append({'kind': 'required_field_missing', 'file': rel})
        if t.get('id') != p.stem or t.get('registry_id') != folder.name:
            issues.append({'kind': 'task_identity_mismatch', 'file': rel})
        if t.get('task_type') != entries[folder.name].get('adapter'):
            issues.append({'kind': 'adapter_mismatch', 'file': rel})
        if t['id'] in tasks:
            issues.append({'kind': 'duplicate_id', 'file': rel})
        tasks[t['id']] = t
        inp = t.get('input') or {}
        pf, expected = inp.get('prompt_file'), inp.get('prompt_sha256')
        if not pf or digest(pf) is None:
            issues.append({'kind': 'prompt_missing', 'file': rel})
        elif not expected:
            issues.append({'kind': 'prompt_digest_absent', 'file': rel})
        elif digest(pf) != expected.removeprefix('sha256:'):
            issues.append({'kind': 'prompt_digest_mismatch', 'file': rel})
        refs = list(inp.get('assets') or [])
        held = (t.get('reference') or {}).get('held_out')
        if isinstance(held, dict) and 'path' in held and 'digest' in held:
            refs.append(held)
        for asset in refs:
            actual = digest(asset['path'])
            if actual is None:
                issues.append({'kind': 'asset_missing', 'file': rel, 'asset': asset['path']})
            elif actual != asset['digest'].removeprefix('sha256:'):
                issues.append({'kind': 'asset_digest_mismatch', 'file': rel, 'asset': asset['path']})
        oracle = (t.get('grader') or {}).get('oracle_source')
        if oracle and not (ROOT / oracle).is_file():
            issues.append({'kind': 'oracle_source_missing', 'file': rel, 'asset': oracle})

runs = []
result_issue_counts = Counter()
result_issue_examples = []
for rd in sorted((ROOT / 'results').glob('*/*/*')):
    if not rd.is_dir():
        continue
    fs = sorted(rd.glob('result_*.json'))
    mf = rd / 'run_manifest.json'
    if not fs and not mf.exists():
        continue
    rows = []
    for f in fs:
        try:
            r = read_json(f)
        except (ValueError, OSError):
            result_issue_counts['unreadable_json'] += 1
            continue
        rows.append(r)
        problems = []
        s = r.get('score')
        if not isinstance(s, (int, float)) or not math.isfinite(s) or not 0 <= s <= 1:
            problems.append('invalid_score')
        if r.get('validity_gate') == 0 and s != 0:
            problems.append('gate_zero_nonzero_score')
        if r.get('task_id') != f.stem.removeprefix('result_'):
            problems.append('result_identity_mismatch')
        if r.get('registry_id') != rd.parent.parent.name:
            problems.append('result_registry_mismatch')
        for kind in problems:
            result_issue_counts[kind] += 1
            if len(result_issue_examples) < 25:
                result_issue_examples.append({'kind': kind, 'path': str(f.relative_to(ROOT))})
    m = read_json(mf) if mf.exists() else {}
    extra = m.get('extra') or {}
    rid, date, label = rd.relative_to(ROOT / 'results').parts
    control = m.get('provider') in ('oracle', 'stub') or label in ('oracle', 'stub', 'oracle-hidden')
    hidden = bool(extra.get('hidden_mode')) or label.endswith('-hidden')
    experiment = any(x in label for x in ('-H', '-iter', 'sub10')) or extra.get('harness_arm') not in (None, 'H0')
    kind = 'hidden' if hidden else 'control' if control else 'experiment' if experiment else 'ml' if label.startswith('ml-') else 'model'
    valid = [r for r in rows if r.get('failure_mode') not in ('crash', 'env_mismatch')]
    scores = [r['score'] for r in valid if isinstance(r.get('score'), (int, float)) and math.isfinite(r['score'])]
    ids = {r.get('task_id') for r in rows}
    current = {k for k, t in tasks.items() if t['registry_id'] == rid}
    envs = sorted({str(r.get('environment_digest')) for r in rows})
    mismatches = sum(r.get('environment_digest') != m.get('environment_digest') for r in rows) if m else None
    runs.append({
        'path': str(rd.relative_to(ROOT)), 'registry_id': rid, 'date': date, 'label': label,
        'kind_heuristic': kind, 'provider': m.get('provider'), 'model': extra.get('model'),
        'n_results': len(rows), 'manifest_exists': bool(m), 'manifest_n_tasks': m.get('n_tasks'),
        'hidden_n': extra.get('hidden_n'), 'harness_arm': extra.get('harness_arm'),
        'git_commit': m.get('git_commit'), 'rerun_command': m.get('rerun_command'),
        'manifest_tasks_dir_exists_now': (ROOT / m['tasks_dir']).exists() if m.get('tasks_dir') else None,
        'extra_keys': sorted(extra), 'distinct_result_environments': len(envs),
        'result_manifest_environment_mismatches': mismatches,
        'voided': len(rows) - len(valid), 'gate_passed': sum(r.get('validity_gate') == 1 for r in rows),
        'mean_nonvoid': round(sum(scores)/len(scores), 6) if scores else None,
        'failure_modes': counts(str(r.get('failure_mode')) for r in rows),
        'current_task_count': len(current), 'missing_current_ids': sorted(current-ids),
        'noncurrent_ids': sorted(ids-current),
        'hidden_rerun_flag_present': '--hidden ' in (m.get('rerun_command') or '') if hidden else None,
    })

suites = []
for rid, e in entries.items():
    ts = [t for t in tasks.values() if t['registry_id'] == rid]
    rs = [r for r in runs if r['registry_id'] == rid]
    if not ts and not rs:
        continue
    complete_models = [r for r in rs if r['kind_heuristic'] == 'model' and not r['missing_current_ids'] and not r['noncurrent_ids']]
    suites.append({'id': rid, 'status': e['status'], 'adapter': e.get('adapter'),
                   'tasks': len(ts), 'domains': counts(t['domain'] for t in ts),
                   'runs': len(rs), 'result_rows': sum(r['n_results'] for r in rs),
                   'full_current_model_runs': [r['path'] for r in complete_models],
                   'hidden_declaration': e.get('hidden_dynamic', False)})

out = {
    'method': 'Current canonical YAML and all disk result directories. Filename kind classification is heuristic; no provider or solver invoked. Full-current describes ID coverage only, not validity or comparability.',
    'commit': git('rev-parse', 'HEAD'), 'branch': git('branch', '--show-current'),
    'working_changes': git('status', '--short'), 'remote_names': git('remote').splitlines(),
    'registry_entries': len(reg), 'registry_status_counts': counts(e['status'] for e in reg),
    'nonexcluded_registry_entries': sum(e['status'] != 'excluded' for e in reg),
    'canonical_tasks': len(tasks), 'task_types': counts(t['task_type'] for t in tasks.values()),
    'domains': counts(t['domain'] for t in tasks.values()), 'static_hidden_tasks': sum(bool(t.get('hidden')) for t in tasks.values()),
    'noncanonical_task_directories': noncanonical,
    'task_issue_counts': counts(i['kind'] for i in issues), 'task_issues': issues,
    'run_count': len(runs), 'result_count': sum(r['n_results'] for r in runs),
    'run_kinds_heuristic': counts(r['kind_heuristic'] for r in runs),
    'unknown_commit_manifests': sum(r['manifest_exists'] and (not r['git_commit'] or str(r['git_commit']).startswith('unknown')) for r in runs),
    'missing_manifests': sum(not r['manifest_exists'] for r in runs),
    'mixed_environment_runs': sum(r['distinct_result_environments'] > 1 for r in runs),
    'manifest_environment_mismatch_runs': sum(bool(r['result_manifest_environment_mismatches']) for r in runs),
    'result_issue_counts': dict(result_issue_counts), 'result_issue_examples': result_issue_examples,
    'suites': suites, 'runs': runs,
}
print(json.dumps(out, ensure_ascii=False, indent=2))
