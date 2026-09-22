"""Archive-only guards for campaigns; never import or execute archive contents.

The local archive and lock author are trusted. These checks detect inconsistent
records, not an administrator able to forge every record and hash together.
"""
from __future__ import annotations

from collections import Counter
import os
from pathlib import Path
import re
import stat
from typing import Any, Callable

from .completion import negative_control_passed

SHA = re.compile(r'^[0-9a-f]{64}$')


def require(condition: Any, message: str) -> None:
    if not condition:
        raise ValueError(message)


def scan_archive(root: Path, *, max_entries: int = 100000,
                 max_depth: int = 64) -> tuple[set[str], list[str]]:
    """Find record paths without silently hiding unreadable/link directories.

    Unlike rglob, a scan failure invalidates the inventory. No link/reparse point
    is followed. Bounds apply to *all* entries, not only matching JSON names.
    Returned paths cover run/manifest/result records; no file bytes are read.
    """
    root = Path(root)
    records: set[str] = set()
    issues: list[str] = []
    pending = [(root, 0)]
    visited = 0
    while pending:
        directory, depth = pending.pop()
        try:
            with os.scandir(directory) as entries:
                for entry in entries:
                    visited += 1
                    if visited > max_entries:
                        return records, issues + ['archive_entry_limit']
                    path = Path(entry.path)
                    relative = path.relative_to(root).as_posix()
                    info = entry.stat(follow_symlinks=False)
                    reparse = getattr(info, 'st_file_attributes', 0) & getattr(
                        stat, 'FILE_ATTRIBUTE_REPARSE_POINT', 0x400)
                    if stat.S_ISLNK(info.st_mode) or reparse:
                        code = 'symlink_forbidden' if stat.S_ISLNK(info.st_mode) else 'archive_reparse_forbidden'
                        issues.append(code + ': ' + relative)
                    elif stat.S_ISDIR(info.st_mode):
                        if depth >= max_depth:
                            issues.append('archive_depth_limit: ' + relative)
                        else:
                            pending.append((path, depth + 1))
                    elif stat.S_ISREG(info.st_mode):
                        if entry.name in ('run.json', 'run_manifest.json') or (
                                entry.name.startswith('result_') and entry.name.endswith('.json')):
                            records.add(relative)
                    else:
                        issues.append('archive_special_file: ' + relative)
                    if len(issues) >= 100:
                        return records, issues + ['archive_issue_limit']
        except OSError as exc:
            issues.append(f'archive_scan_failed: {directory.relative_to(root).as_posix()}: {exc}')
    return records, sorted(issues)


def suite_contract(manifest: dict[str, Any]) -> dict[str, Any]:
    """Stable runner-layer identity; intentionally exclude provider and seed.

    Oracle anchors and candidate runs differ in provider; repeated runs differ
    in seed, generated time, output paths and resume counters. None are runtime
    contracts. Assets and the runner environment digest *are* contracts.
    """
    require(isinstance(manifest, dict), 'invalid_suite_contract')
    for field in ('registry_id', 'adapter'):
        require(isinstance(manifest.get(field), str) and bool(manifest[field]),
                'invalid_suite_contract: ' + field)
    env = manifest.get('environment_digest')
    require(isinstance(env, str) and env.startswith('sha256:')
            and SHA.fullmatch(env[7:]), 'suite_environment_missing')
    assets = manifest.get('assets', {})
    require(isinstance(assets, dict) and all(isinstance(k, str) and isinstance(v, str)
                                           for k, v in assets.items()), 'invalid_suite_assets')
    return {**{k: manifest[k] for k in ('registry_id', 'adapter', 'environment_digest')},
            'assets': assets}


def calibration_record(doc: dict[str, Any], root: Path, tasks: list[dict[str, Any]], *,
                       read_json: Callable, locate: Callable, decode: Callable) -> dict[str, Any]:
    """Recheck recorded negative controls, not merely calibration_passed=True.

    Positive reference runs are still valid preflight anchors, but explicitly
    do not establish calibration. Physical evidence is not re-executed here.
    """
    if doc['mode'] != 'calibrate':
        return {'status': 'not_checked', 'controls': []}
    require(doc.get('calibration_passed') is True, 'calibration_not_passed')
    controls = doc.get('controls')
    require(isinstance(controls, list) and bool(controls), 'calibration_controls_missing')
    by_id = {t['id']: t for t in tasks}
    require(len(by_id) == len(tasks), 'ambiguous_calibration_task_id')
    indices: Counter = Counter()
    seen: set[tuple[str, str]] = set()
    checked = []
    for control in controls:
        require(isinstance(control, dict), 'invalid_calibration_control')
        tid = control.get('task_id')
        require(isinstance(tid, str) and tid in by_id, 'calibration_task_mismatch')
        source = control.get('control')
        require(isinstance(source, str) and bool(source)
                and (tid, source) not in seen, 'invalid_calibration_control_identity')
        seen.add((tid, source))
        require(control.get('passed') is True and not control.get('result_issues'),
                'calibration_control_not_passed')
        prefix = f'controls/{tid}-{indices[tid]}'
        indices[tid] += 1
        raw, raw_sha = read_json(locate(root, f'{prefix}/result_{tid}.json'))
        manifest, manifest_sha = read_json(locate(root, f'{prefix}/run_manifest.json'))
        task = by_id[tid]
        suite_contract(manifest)
        require(manifest.get('provider') == 'oracle'
                and manifest.get('registry_id') == task['suite']
                and type(manifest.get('seed')) is int
                and manifest['seed'] == doc['identity']['seed']
                and type(manifest.get('n_tasks')) is int and manifest['n_tasks'] == 1
                and manifest.get('adapter') == raw.get('adapter') == task['adapter']
                and manifest.get('environment_digest') == raw.get('environment_digest'),
                'calibration_manifest_mismatch')
        artifacts = raw.get('artifacts')
        require(isinstance(artifacts, dict), 'invalid_calibration_artifacts')
        details = decode(artifacts.get('grade_details', '{}'))
        require(isinstance(details, dict), 'invalid_calibration_details')
        audit = details.get('deck_audit') or details.get('cfd_audit') or {}
        require(isinstance(audit, dict) and isinstance(audit.get('issues', []), list),
                'invalid_calibration_diagnostics')
        actual = []
        for issue in audit.get('issues', []):
            require(isinstance(issue, dict) and isinstance(issue.get('code'), str),
                    'invalid_calibration_diagnostics')
            actual.append(issue['code'])
        gates = raw.get('gate_failures', [])
        require(isinstance(gates, list) and all(isinstance(g, str) for g in gates),
                'invalid_calibration_diagnostics')
        actual.extend(gates)
        failure = raw.get('failure_mode')
        require(failure is None or isinstance(failure, str), 'invalid_calibration_diagnostics')
        if failure:
            actual.append(failure)
        require(negative_control_passed(raw, control, task_id=tid, suite=task['suite'],
                                        actual_issues=actual), 'calibration_raw_control_failed')
        require(type(control.get('score')) in (int, float)
                and control['score'] == raw['score'], 'calibration_summary_mismatch')
        checked.append({'task_id': tid, 'control': source, 'result_sha256': raw_sha,
                        'manifest_sha256': manifest_sha})
    require(set(indices) == set(by_id), 'calibration_control_coverage_missing')
    return {'status': 'recorded_pass', 'controls': checked}
