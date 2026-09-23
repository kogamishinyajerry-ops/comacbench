"""Task-paired diagnostics over already audited cells; never a new grader.

Only campaign.evaluate supplies trusted, reconciled cells. Diagnostic strings
are recorded observations, not inferred causes. No extra model or solver calls.
"""
from __future__ import annotations

from collections import Counter
import html
from typing import Any

OUTCOMES = ('gained', 'regressed', 'both_pass', 'both_fail', 'unresolved')
LABELS = dict(zip(OUTCOMES, ('新增通过', '新增退步', '保持通过', '仍未全过', '待核验')))


def recorded_diagnostics(raw: dict[str, Any]) -> dict[str, Any]:
    """Optional diagnostic metadata must never silently change a task score."""
    issues, failures = [], []
    mode = raw.get('failure_mode')
    if mode is not None and not isinstance(mode, str):
        mode = None
        issues.append('invalid_failure_mode_metadata')
    if isinstance(mode, str) and len(mode) > 240:
        mode = mode[:240]
        issues.append('failure_mode_truncated')
    gates = raw.get('gate_failures', [])
    if not isinstance(gates, list) or any(not isinstance(g, str) for g in gates):
        issues.append('invalid_gate_failures_metadata')
    else:
        failures = list(dict.fromkeys(g[:240] for g in gates[:32]))
        if len(gates) > 32 or any(len(g) > 240 for g in gates):
            issues.append('gate_failures_truncated')
    return {'failure_mode': mode, 'gate_failures': failures, 'diagnostic_issues': issues}


def paired_outcomes(cases: list[dict[str, Any]], seeds: list[int],
                    cells: dict[tuple[str, str, int], dict[str, Any]], *,
                    baseline: str, candidate: str, blocked: bool = False) -> dict[str, Any]:
    """Pair by case/seed/suite/task, including every predeclared execution.

    A broken cell contributes unresolved pairs, not engineering failures. Global
    archive ambiguity suppresses ALL transitions. Local missing cells leave
    other audited pairs inspectable, but cannot authorize a group conclusion.
    """
    rows = []
    for case in cases:
        for seed in seeds:
            left = cells[(baseline, case['id'], seed)]
            right = cells[(candidate, case['id'], seed)]
            lookups = [{(r['suite'], r['id']): r for r in side['results']}
                       if not side['issues'] else {} for side in (left, right)]
            for task in case['tasks']:
                key = (task['suite'], task['id'])
                a, b = (lookup.get(key) for lookup in lookups)
                outcome = 'unresolved'
                if not blocked and a is not None and b is not None:
                    outcome = ('both_pass' if a['full_pass'] and b['full_pass'] else
                               'gained' if b['full_pass'] else
                               'regressed' if a['full_pass'] else 'both_fail')
                def side_record(cell, result):
                    return {'run': cell['run'], 'run_sha256': cell.get('run_sha256'),
                            'record': f'{cell["run"].removesuffix("run.json")}runs/{key[0]}/result_{key[1]}.json',
                            'issues': list(cell['issues']),
                            'result': {k: result.get(k) for k in (
                                'score', 'full_pass', 'validity_gate', 'evidence_level',
                                'result_sha256', 'failure_mode', 'gate_failures',
                                'diagnostic_issues')} if result is not None else None}
                rows.append({'case': case['id'], 'seed': seed, 'suite': key[0], 'task_id': key[1],
                             'outcome': outcome, 'baseline': side_record(left, a),
                             'candidate': side_record(right, b)})
    counts = Counter(row['outcome'] for row in rows)
    return {'pairing': 'case_seed_suite_task', 'expected_pairs': len(rows),
            'counts': {k: counts[k] for k in OUTCOMES}, 'archive_blocked': blocked,
            'has_observed_regressions': True if counts['regressed'] else
                                        None if counts['unresolved'] else False,
            'tasks': rows}


def render_comparison(pair: dict[str, Any], *, max_rows: int = 100,
                      split_label: str | None = None) -> str:
    """Escaped offline drill-down; cap HTML only, keep all pairs in JSON."""
    escape = lambda value: html.escape(str(value), quote=True)
    change = ('证据不足，不作整组比较' if not pair['comparable'] else
              f'{pair["delta_pass_rate"] * 100:+.1f} 个百分点')
    title = escape(f'{pair["family"]} / {split_label or pair["split"]}: {pair["candidate"]} − {pair["baseline"]}')
    audit = pair['paired_outcomes']
    counts = ' · '.join(f'{LABELS[k]} {audit["counts"][k]}' for k in OUTCOMES)
    warning = ('<p><strong>出现新增退步，请逐项核查；净提升不等于可以替换旧版本。</strong></p>'
               if audit['has_observed_regressions'] else '')
    if not pair['comparable']:
        warning += '<p>以下仅供定位已核验的局部差异；待核验项不是零分，不推断整组效果。</p>'
    if audit['archive_blocked']:
        warning += '<p>归档范围存在歧义，全部配对变化暂不分类。</p>'
    priority = {'regressed': 0, 'unresolved': 1, 'gained': 2, 'both_fail': 3, 'both_pass': 4}
    ordered = sorted(audit['tasks'], key=lambda r: (
        priority[r['outcome']], r['case'], r['seed'], r['suite'], r['task_id']))
    def diagnostic(side):
        result = side['result']
        if result is None:
            return '; '.join(side['issues']) or '待核验'
        parts = list(result.get('gate_failures') or [])
        if result.get('failure_mode') and result['failure_mode'] not in parts:
            parts.append(result['failure_mode'])
        parts += list(result.get('diagnostic_issues') or [])
        return '; '.join(parts) or ('—' if result['full_pass'] else '未记录具体诊断；查看原始结果')
    body = []
    for row in ordered[:max_rows]:
        def score(side):
            return '待核验' if side['result'] is None else f'{side["result"]["score"]:g}'
        values = (f'{row["case"]} / seed-{row["seed"]} / {row["suite"]}/{row["task_id"]}',
                  LABELS[row['outcome']], score(row['baseline']), score(row['candidate']),
                  diagnostic(row['baseline']), diagnostic(row['candidate']))
        body.append('<tr>' + ''.join(f'<td>{escape(value)}</td>' for value in values) + '</tr>')
    shown = min(len(ordered), max_rows)
    return (f'<li><strong>{title}</strong>：{escape(change)}<p>{escape(counts)}</p>{warning}'
            f'<details><summary>展开逐任务对照（展示 {shown}/{len(ordered)} 条）</summary>'
            '<p>按新增退步、待核验、新增通过优先展示；完整配对与原始记录摘要见 campaign.json。'
            '分数沿用原判分器，诊断是原始记录，不是根因推断；分类以是否满分为准。</p>'
            '<div class="scroll"><table><thead><tr><th>任务／种子</th><th>变化</th>'
            '<th>A 基线分数</th><th>B 候选分数</th><th>A 诊断</th><th>B 诊断</th>'
            '</tr></thead><tbody>' + ''.join(body) + '</tbody></table></div></details></li>')
