"""Completion and calibration guards; never turn harness faults into model scores.

This module uses only the standard library. It does not change any task grader,
reference, tolerance, or weight. Failure modes follow runners/common.py.
"""
from __future__ import annotations

from collections import Counter
import math
from typing import Any, Mapping, Sequence

VOIDED_FAILURE_MODES = ('env_mismatch', 'crash')


def result_issues(result: Any, *, task_id: str, suite: str) -> list[str]:
    """Validate the result envelope before accepting its score or diagnosis."""
    if not isinstance(result, dict):
        return ['result_not_object']
    issues: list[str] = []
    if result.get('task_id') != task_id:
        issues.append('result_task_id_mismatch')
    if result.get('registry_id') != suite:
        issues.append('result_suite_mismatch')
    score = result.get('score')
    score_valid = (type(score) in (int, float) and 0 <= score <= 1
                   and math.isfinite(score))
    if not score_valid:
        issues.append('invalid_score')
    gate = result.get('validity_gate')
    if type(gate) is not int or gate not in (0, 1):
        issues.append('invalid_validity_gate')
    elif gate == 0 and score_valid and score != 0:
        issues.append('gate_score_contradiction')
    # build_result() communicates infrastructure faults via failure_mode; it
    # does not require a separate `voided` boolean to be present.
    if result.get('voided') or result.get('failure_mode') in VOIDED_FAILURE_MODES:
        issues.append('voided_result')
    return issues


def completion_summary(
    tasks: Sequence[Mapping[str, Any]], rows: Sequence[Mapping[str, Any]],
) -> dict[str, Any]:
    """Reconcile the declared roster, including zero-score but valid results.

    Missing/duplicate/unexpected/invalid results block completion. A task that
    legitimately fails its engineering checks remains a completed scored task.
    """
    expected = [(t['suite'], t['id']) for t in tasks]
    actual = [(r['suite'], r['id']) for r in rows]
    expected_counts, actual_counts = Counter(expected), Counter(actual)
    label = lambda key: f'{key[0]}/{key[1]}'
    missing = sorted(label(k) for k in expected_counts.keys() - actual_counts.keys())
    unexpected = sorted(label(k) for k in actual_counts.keys() - expected_counts.keys())
    duplicates = sorted(label(k) for k, n in actual_counts.items() if n != 1)
    invalid = [{'task': label((r['suite'], r['id'])), 'issues': r['result_issues']}
               for r in rows if r.get('result_issues')]
    declared_duplicates = sorted(label(k) for k, n in expected_counts.items() if n != 1)
    return {
        'expected_tasks': len(expected), 'recorded_results': len(actual),
        'scorable_results': sum(not r.get('result_issues') for r in rows),
        'missing_tasks': missing, 'unexpected_tasks': unexpected,
        'duplicate_results': duplicates, 'invalid_results': invalid,
        'duplicate_declared_tasks': declared_duplicates,
        'complete': bool(expected) and not (
            missing or unexpected or duplicates or invalid or declared_duplicates),
    }


# ---------------------------------------------------------------------------
# 证据等级（PR-C）：描述「结果背后是什么证据」，不是分数。
# 等级不把作废行升级成任何已完成证据；file_artifacts_checked 仅当
# deliverable_review 真的归档了 engineering_evidence 时授予。
# ---------------------------------------------------------------------------
SOLVER_EXECUTED = 'solver_executed'
EXECUTABLE_CHECKS = 'executable_checks'
INPUT_AUDIT = 'input_audit'
FILE_ARTIFACTS_CHECKED = 'file_artifacts_checked'
NO_COMPLETED_EXECUTION = 'no_completed_execution'
KNOWN_EVIDENCE_LEVELS = (SOLVER_EXECUTED, EXECUTABLE_CHECKS, INPUT_AUDIT,
                         FILE_ARTIFACTS_CHECKED)


def classify_evidence_level(result: Any) -> str:
    """Classify what kind of evidence backs a result row.

    Rules (acceptance B03 + P1 evidence_level):
    - A row with result_issues (including voided) has no completed execution
      to show; it keeps NO_COMPLETED_EXECUTION regardless of adapter kind.
    - A row that already carries a known evidence_level and has no issues is
      respected (pass-through: producers like __main__ computed it from the
      run facts; we do not downgrade verified evidence).
    - solver_executed: the run actually executed a solver (ccx_fea with
      measured runtime, or an explicit solver_executed flag).
    - file_artifacts_checked: deliverable_review runs whose artifacts include
      engineering_evidence (real deliverable bytes archived for review).
    - executable_checks: unit-test style checks ran.
    - input_audit: deck/cfd audit only.
    """
    if not isinstance(result, dict):
        return NO_COMPLETED_EXECUTION
    issues = result.get('result_issues') or []
    if issues:
        return NO_COMPLETED_EXECUTION
    declared = result.get('evidence_level')
    if declared in KNOWN_EVIDENCE_LEVELS:
        return declared
    details = result.get('details') or {}
    artifacts = result.get('artifacts') or {}
    if details.get('solver_executed') or (
            details.get('kind') == 'ccx_fea' and details.get('ccx_s') is not None):
        return SOLVER_EXECUTED
    if details.get('kind') == 'deliverable_review' and artifacts.get('engineering_evidence'):
        return FILE_ARTIFACTS_CHECKED
    if details.get('kind') == 'unit_tests':
        return EXECUTABLE_CHECKS
    if details.get('deck_audit') or details.get('cfd_audit'):
        return INPUT_AUDIT
    return NO_COMPLETED_EXECUTION


def negative_control_passed(
    result: Any, control: Mapping[str, Any], *, task_id: str, suite: str,
    actual_issues: Sequence[str],
) -> bool:
    """A low score caused by a grader/environment fault is not calibration."""
    if result_issues(result, task_id=task_id, suite=suite):
        return False
    maximum = control.get('max_score')
    if type(maximum) not in (int, float) or not 0 <= maximum <= 1 or not math.isfinite(maximum):
        return False
    expected = control.get('expected_issue')
    return (result['score'] <= maximum
            and (expected is None or expected in actual_issues))
