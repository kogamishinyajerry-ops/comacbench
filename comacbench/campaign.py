"""Read-only, solver-free campaigns over the existing comacbench.run.v1 format.

This is a recorded-outcome auditor, not a new grader, simulator, scheduler, or
hidden-test service. JSON digests detect accidental drift, not a hostile author
who can rewrite the entire archive and lock. Never execute archive contents.
"""
from __future__ import annotations

import argparse
from collections import Counter
import hashlib
import html
import json
import math
from pathlib import Path, PurePosixPath
import re
import sys
from typing import Any

from .completion import classify_evidence_level, result_issues

PLAN = 'comacbench.campaign.plan.v1'
LOCK = 'comacbench.campaign.lock.v1'
REPORT = 'comacbench.campaign.report.v1'
ID = re.compile(r'^[A-Za-z0-9][A-Za-z0-9._-]{0,100}$')
SHA = re.compile(r'^[0-9a-f]{64}$')
SPLITS = ('development', 'transfer', 'stress')
SPLIT_NAMES = {'development': '开发集', 'transfer': '公开迁移回归', 'stress': '压力集'}
MAX_BYTES = 16 * 1024 * 1024
MAX_CELLS = 10000
EVIDENCE_FOR_KIND = {'unit_tests_problem': 'executable_checks',
                     'file_package': 'file_artifacts_checked',
                     'ccx_fea': 'solver_executed', 'cfd_step': 'solver_executed'}


def require(condition: Any, message: str) -> None:
    if not condition:
        raise ValueError(message)


def canonical(value: Any) -> bytes:
    return json.dumps(value, sort_keys=True, ensure_ascii=False,
                      separators=(',', ':'), allow_nan=False).encode('utf-8')


def sha(value: Any) -> str:
    return hashlib.sha256(canonical(value)).hexdigest()


def _pairs(pairs: list[tuple[str, Any]]) -> dict[str, Any]:
    result: dict[str, Any] = {}
    for key, value in pairs:
        require(key not in result, 'duplicate_json_key: ' + key)
        result[key] = value
    return result


def _constant(value: str) -> Any:
    raise ValueError('nonfinite_json: ' + value)


def _float(value: str) -> float:
    number = float(value)
    require(math.isfinite(number), 'nonfinite_json: ' + value)
    return number


def decode(text: str) -> Any:
    return json.loads(text, object_pairs_hook=_pairs, parse_constant=_constant, parse_float=_float)


def read_json(path: Path) -> tuple[dict[str, Any], str]:
    # Bounded read also handles files growing between stat and read.
    with path.open('rb') as stream:
        raw = stream.read(MAX_BYTES + 1)
    require(len(raw) <= MAX_BYTES, 'json_too_large')
    obj = decode(raw.decode('utf-8'))
    require(isinstance(obj, dict), 'json_not_object')
    return obj, hashlib.sha256(raw).hexdigest()


def identifier(value: Any) -> str:
    require(isinstance(value, str) and ID.fullmatch(value), 'invalid_id')
    # Win32 reserved basenames are not portable directory components.
    require(value.split('.')[0].upper() not in {
        'CON', 'PRN', 'AUX', 'NUL', *(f'COM{i}' for i in range(1, 10)),
        *(f'LPT{i}' for i in range(1, 10))}, 'reserved_id')
    require(not value.endswith('.'), 'invalid_id')
    return value


def contained_file(root: Path, relative: str) -> Path:
    require(isinstance(relative, str) and bool(relative), 'invalid_path')
    p = PurePosixPath(relative)
    require(not p.is_absolute() and '\\' not in relative and ':' not in relative
            and all(part not in ('', '.', '..') for part in relative.split('/')),
            'path_escape')
    root = root.resolve()
    target = root
    for part in p.parts:
        target = target / part
        require(not target.is_symlink(), 'symlink_forbidden')
    require(target.resolve().is_relative_to(root), 'path_escape')
    require(target.is_file(), 'missing_file: ' + relative)
    return target


def roster(tasks: Any) -> list[dict[str, Any]]:
    require(isinstance(tasks, list) and 0 < len(tasks) <= 1000, 'invalid_roster')
    keys = []
    for task in tasks:
        require(isinstance(task, dict), 'invalid_task')
        keys.append((identifier(task.get('suite')).casefold(), identifier(task.get('id')).casefold()))
        require(isinstance(task.get('exec_kind'), str) and task['exec_kind'] in EVIDENCE_FOR_KIND,
                'unsupported_task_kind')
    require(len(set(keys)) == len(keys), 'duplicate_task')
    return tasks


def user_agent(agent: Any) -> None:
    require(isinstance(agent, dict) and agent.get('name') == 'external'
            and agent.get('protocol') == 'comacbench.agent.v1'
            and agent.get('agent_kind') == 'user_agent', 'not_user_agent')
    require(all(isinstance(agent.get(k), str) and agent[k].strip() for k in ('model', 'revision')),
            'agent_identity_missing')
    require(isinstance(agent.get('config_sha256'), str)
            and SHA.fullmatch(agent['config_sha256']), 'agent_identity_missing')
    for field in ('revision_files', 'command_files'):
        require(isinstance(agent.get(field), dict) and bool(agent[field]),
                'agent_identity_missing: ' + field)
        require(all(isinstance(v, str) and SHA.fullmatch(v) for v in agent[field].values()),
                'agent_identity_invalid: ' + field)
    require(isinstance(agent.get('executable_sha256'), str)
            and SHA.fullmatch(agent['executable_sha256']), 'agent_identity_missing')
    require(isinstance(agent.get('identity_env'), dict), 'agent_identity_missing')
    require(all(isinstance(v, str) and SHA.fullmatch(v) for v in agent['identity_env'].values()),
            'agent_identity_invalid: identity_env')


def runtime_contract(identity: Any) -> dict[str, Any]:
    require(isinstance(identity, dict) and identity.get('protocol') == 'comacbench.run.v1',
            'run_protocol_mismatch')
    require(isinstance(identity.get('pack_sha256'), str)
            and SHA.fullmatch(identity['pack_sha256']), 'pack_identity_missing')
    require(isinstance(identity.get('engine'), dict) and bool(identity['engine']),
            'engine_identity_missing')
    require(all(isinstance(v, str) and SHA.fullmatch(v) for v in identity['engine'].values()),
            'engine_identity_invalid')
    require(isinstance(identity.get('execution_environment'), dict)
            and bool(identity['execution_environment']), 'environment_identity_missing')
    env = identity['execution_environment']
    require(all(isinstance(env.get(k), dict) for k in ('python', 'dependencies', 'solvers'))
            and isinstance(env['python'].get('path'), str)
            and isinstance(env['python'].get('sha256'), str)
            and SHA.fullmatch(env['python']['sha256']) and bool(env['dependencies']),
            'environment_identity_missing')
    # Preserve future identity fields rather than silently discarding them.
    return {k: v for k, v in identity.items() if k not in ('agent', 'seed', 'mode')}


def inspect_run(path: Path, *, scoring: bool) -> dict[str, Any]:
    """Reconcile the roster and raw result JSON; ignore advisory full_pass fields.

    Raw paths are derived from suite/task IDs, never from archived absolute
    result_file paths. This supports copying a run folder without path rewrites.
    Engineering artifacts referenced *inside* raw results are NOT revalidated.
    """
    doc, doc_sha = read_json(path)
    require(doc.get('status') == 'complete', 'run_incomplete')
    identity = doc.get('identity')
    contract = runtime_contract(identity)
    require(doc.get('mode') in ('run', 'calibrate')
            and doc['mode'] == identity.get('mode'), 'run_mode_mismatch')
    require(type(identity.get('seed')) is int, 'invalid_run_seed')
    require(isinstance(identity.get('agent'), dict)
            and doc.get('agent') == identity['agent'], 'agent_summary_mismatch')
    if scoring:
        require(doc['mode'] == 'run', 'calibration_not_score')
        user_agent(identity['agent'])
    validation = doc.get('validation')
    require(isinstance(validation, dict) and validation.get('runnable') is True,
            'invalid_validation')
    tasks = roster(validation.get('tasks'))
    manifests, manifest_hashes = {}, {}
    for suite in sorted({t['suite'] for t in tasks}):
        manifest, digest = read_json(contained_file(path.parent, f'runs/{suite}/run_manifest.json'))
        expected_provider = 'oracle' if doc['mode'] == 'calibrate' else 'external'
        require(manifest.get('registry_id') == suite and manifest.get('provider') == expected_provider
                and type(manifest.get('seed')) is int and manifest['seed'] == identity['seed']
                and type(manifest.get('n_tasks')) is int
                and manifest['n_tasks'] == sum(t['suite'] == suite for t in tasks),
                'suite_manifest_mismatch: ' + suite)
        require(isinstance(manifest.get('environment_digest'), str)
                and manifest['environment_digest'].startswith('sha256:')
                and SHA.fullmatch(manifest['environment_digest'][7:]), 'suite_environment_missing')
        manifests[suite], manifest_hashes[suite] = manifest, digest
    rows = doc.get('results')
    require(isinstance(rows, list) and all(isinstance(r, dict) for r in rows),
            'invalid_result_rows')
    expected = [(t['suite'], t['id']) for t in tasks]
    actual = [(r.get('suite'), r.get('id')) for r in rows]
    require(all(isinstance(a, str) and isinstance(b, str) for a, b in actual),
            'invalid_result_ids')
    require(Counter(expected) == Counter(actual), 'result_roster_mismatch')
    by_key = dict(zip(actual, rows))
    checked = []
    for suite, tid in expected:
        row = by_key[(suite, tid)]
        require(not row.get('result_issues'), 'recorded_result_issues')
        relative = f'runs/{suite}/result_{tid}.json'
        raw, raw_sha = read_json(contained_file(path.parent, relative))
        require(row.get('result_sha256') == raw_sha, 'result_digest_mismatch: ' + tid)
        task = next(t for t in tasks if (t['suite'], t['id']) == (suite, tid))
        require(raw.get('adapter') == task.get('adapter') == manifests[suite].get('adapter')
                and raw.get('environment_digest') == manifests[suite]['environment_digest'],
                'raw_manifest_mismatch: ' + tid)
        issues = result_issues(raw, task_id=tid, suite=suite)
        require(not issues, 'invalid_result: ' + tid + ': ' + ','.join(issues))
        require(type(row.get('score')) in (int, float)
                and row['score'] == raw['score']
                and type(row.get('validity_gate')) is int
                and row['validity_gate'] == raw['validity_gate'], 'result_summary_mismatch')
        artifacts = raw.get('artifacts', {})
        require(isinstance(artifacts, dict), 'invalid_artifacts')
        details = decode(artifacts.get('grade_details', '{}'))
        require(isinstance(details, dict), 'invalid_grade_details')
        # Do not pass the row's self-declared evidence_level into the classifier.
        evidence = classify_evidence_level({'details': details, 'artifacts': artifacts})
        checked.append({'suite': suite, 'id': tid, 'score': raw['score'],
                        'full_pass': raw['validity_gate'] == 1 and raw['score'] == 1,
                        'evidence_level': evidence, 'result_sha256': raw_sha})
    return {'contract': contract, 'tasks': tasks, 'results': checked,
            'agent': identity['agent'], 'seed': identity['seed'],
            'mode': doc['mode'], 'run_sha256': doc_sha, 'manifest_sha256': manifest_hashes}


def validate_body(body: Any) -> None:
    require(isinstance(body, dict) and body.get('protocol') == LOCK, 'lock_protocol_mismatch')
    require(body.get('scope') == 'public_regression', 'unsupported_scope')
    identifier(body.get('id'))
    seeds = body.get('seeds')
    require(isinstance(seeds, list) and 0 < len(seeds) <= 100
            and all(type(s) is int and 0 <= s < 2**31 for s in seeds)
            and len(set(seeds)) == len(seeds), 'invalid_seeds')
    subjects, cases = body.get('subjects'), body.get('cases')
    require(isinstance(subjects, list) and 0 < len(subjects) <= 100, 'invalid_subjects')
    require(isinstance(cases, list) and 0 < len(cases) <= 1000, 'invalid_cases')
    require(len(subjects) * len(cases) * len(seeds) <= MAX_CELLS, 'campaign_too_large')
    subject_ids, subject_hashes, case_ids, case_keys = set(), set(), set(), set()
    for subject in subjects:
        require(isinstance(subject, dict), 'invalid_subject')
        sid = identifier(subject.get('id'))
        user_agent(subject.get('identity'))
        digest = sha(subject['identity'])
        require(sid.casefold() not in {i.casefold() for i in subject_ids}
                and digest not in subject_hashes, 'duplicate_subject')
        subject_ids.add(sid)
        subject_hashes.add(digest)
    families: dict[str, set[str]] = {}
    engines = set()
    for case in cases:
        require(isinstance(case, dict), 'invalid_case')
        cid, family = identifier(case.get('id')), identifier(case.get('family'))
        require(cid.casefold() not in case_ids, 'duplicate_case')
        case_ids.add(cid.casefold())
        require(case.get('split') in SPLITS, 'invalid_split')
        families.setdefault(family, set()).add(case['split'])
        require(isinstance(case.get('scope_note'), str) and case['scope_note'].strip(),
                'missing_scope_note')
        tasks = roster(case.get('tasks'))
        contract = runtime_contract(case.get('contract'))
        key = (contract['pack_sha256'], sha(tasks))
        require(key not in case_keys, 'duplicate_case_contract')
        case_keys.add(key)
        engines.add(sha(contract['engine']))
        evidence = case.get('required_evidence')
        require(isinstance(evidence, dict) and set(evidence) == {
            t['suite'] + '/' + t['id'] for t in tasks}, 'invalid_evidence_roster')
        require(evidence == {t['suite'] + '/' + t['id']: EVIDENCE_FOR_KIND[t['exec_kind']]
                             for t in tasks}, 'invalid_evidence_level')
    require(len(engines) == 1, 'cross_case_engine_drift')
    require(all('transfer' not in splits or 'development' in splits for splits in families.values()),
            'transfer_without_development')
    comparisons = body.get('comparisons', [])
    require(isinstance(comparisons, list), 'invalid_comparisons')
    pairs = set()
    for pair in comparisons:
        require(isinstance(pair, dict), 'invalid_comparison')
        baseline, candidate = pair.get('baseline'), pair.get('candidate')
        require(isinstance(baseline, str) and isinstance(candidate, str)
                and baseline in subject_ids and candidate in subject_ids and baseline != candidate,
                'invalid_comparison')
        require((baseline, candidate) not in pairs, 'duplicate_comparison')
        pairs.add((baseline, candidate))


def freeze_plan(plan: dict[str, Any], anchors: Path) -> dict[str, Any]:
    """Use completed preflight runs to pin runtime contracts, not to earn credit.

    Cases may use calibration/reference anchors; subject identities must come
    from user-agent runs. This is deliberately NOT a blind preregistration.
    """
    require(isinstance(plan, dict) and plan.get('protocol') == PLAN, 'plan_protocol_mismatch')
    require(plan.get('scope') == 'public_regression', 'unsupported_scope')
    body = {k: plan[k] for k in ('id', 'scope', 'seeds')}
    body.update(protocol=LOCK, subjects=[], cases=[], comparisons=plan.get('comparisons', []))
    for entry in plan['subjects']:
        run = inspect_run(contained_file(anchors, entry['anchor']), scoring=True)
        body['subjects'].append({'id': entry['id'], 'identity': run['agent'],
                                 'anchor_sha256': run['run_sha256']})
    for entry in plan['cases']:
        run = inspect_run(contained_file(anchors, entry['anchor']), scoring=False)
        required = {t['suite'] + '/' + t['id']: EVIDENCE_FOR_KIND[t['exec_kind']] for t in run['tasks']}
        require(all(r['full_pass'] and r['evidence_level'] == required[r['suite'] + '/' + r['id']]
                    for r in run['results']), 'case_anchor_not_full_pass')
        body['cases'].append({k: entry[k] for k in ('id', 'family', 'split', 'scope_note')})
        body['cases'][-1].update(contract=run['contract'], tasks=run['tasks'],
                                anchor_sha256=run['run_sha256'], anchor_manifests=run['manifest_sha256'],
                                required_evidence=required)
    validate_body(body)
    return {'body': body, 'sha256': sha(body)}


def evaluate(lock: dict[str, Any], runs: Path) -> dict[str, Any]:
    body = lock.get('body')
    validate_body(body)
    require(lock.get('sha256') == sha(body), 'lock_digest_mismatch')
    cells, expected_paths = [], set()
    for subject in body['subjects']:
        for case in body['cases']:
            for seed in body['seeds']:
                relative = f'{subject["id"]}/{case["id"]}/seed-{seed}/run.json'
                expected_paths.add(relative)
                cell = {'subject': subject['id'], 'case': case['id'], 'family': case['family'],
                        'split': case['split'], 'seed': seed, 'run': relative,
                        'expected': len(case['tasks']), 'passed': 0, 'failed': 0,
                        'unresolved': len(case['tasks']), 'issues': [], 'results': []}
                try:
                    run = inspect_run(contained_file(runs, relative), scoring=True)
                    require(run['agent'] == subject['identity'], 'agent_identity_drift')
                    require(run['seed'] == seed, 'seed_mismatch')
                    require(run['contract'] == case['contract'], 'runtime_contract_drift')
                    require(run['tasks'] == case['tasks'], 'task_contract_drift')
                    for result in run['results']:
                        key = result['suite'] + '/' + result['id']
                        # Legitimate engineering failures can stop before the solver.
                        if result['full_pass']:
                            require(result['evidence_level'] == case['required_evidence'][key],
                                    'passing_evidence_mismatch: ' + key)
                    cell.update(results=run['results'], run_sha256=run['run_sha256'],
                                manifest_sha256=run['manifest_sha256'],
                                passed=sum(r['full_pass'] for r in run['results']), unresolved=0)
                    cell['failed'] = cell['expected'] - cell['passed']
                except (OSError, ValueError, TypeError, KeyError, RecursionError) as exc:
                    cell['issues'] = [str(exc)]
                cells.append(cell)
    # Unexpected run directories include unregistered retries; never select best-of-N.
    discovered = {p.relative_to(runs).as_posix() for p in runs.rglob('run.json')}
    unexpected = sorted(discovered - expected_paths)
    groups = []
    for subject in body['subjects']:
        for family in sorted({case['family'] for case in body['cases']}):
            for split in SPLITS:
                subset = [c for c in cells if (c['subject'], c['family'], c['split']) ==
                          (subject['id'], family, split)]
                if not subset:
                    continue
                group = {'subject': subject['id'], 'family': family, 'split': split,
                         **{k: sum(c[k] for c in subset)
                            for k in ('expected', 'passed', 'failed', 'unresolved')}}
                group['pass_rate'] = (group['passed'] / group['expected']
                                      if group['unresolved'] == 0 and not unexpected else None)
                groups.append(group)
    comparisons = []
    index = {(g['subject'], g['family'], g['split']): g for g in groups}
    for pair in body['comparisons']:
        for group in groups:
            if group['subject'] != pair['candidate']:
                continue
            base = index[(pair['baseline'], group['family'], group['split'])]
            ready = group['pass_rate'] is not None and base['pass_rate'] is not None
            comparisons.append({**pair, 'family': group['family'], 'split': group['split'],
                                'paired_task_executions': group['expected'], 'comparable': ready,
                                'delta_pass_rate': group['pass_rate'] - base['pass_rate'] if ready else None})
    return {'protocol': REPORT, 'id': body['id'], 'scope': 'public_regression',
            'lock_sha256': lock['sha256'], 'complete': not unexpected and all(not c['issues'] for c in cells),
            'publishable': False, 'isolated_transfer_verified': False,
            'engineering_artifacts_reverified': False,
            'integrity_scope': 'run_manifest_and_result_json_only',
            'limits': ['Public regression is not held-out or aircraft-design validation.',
                       'Anchors and locks are trusted local records, not signed attestations.',
                       'Different pack hashes do not prove semantic novelty or physical similarity.',
                       'Task limits/configurations are pinned indirectly; resource enforcement and cost are not audited.',
                       'Only declared Agent identity is pinned; unregistered prompts, Skills, knowledge and human interventions are not audited.',
                       'No statistical independence or confidence is inferred from repeated seeds.'],
            'seeds': body['seeds'], 'case_count': len(body['cases']),
            'family_count': len({c['family'] for c in body['cases']}),
            'groups': groups, 'comparisons': comparisons, 'cells': cells, 'unexpected_runs': unexpected}


def render_html(report: dict[str, Any]) -> str:
    escape = lambda value: html.escape(str(value), quote=True)
    table = ''.join('<tr>' + ''.join(f'<td>{escape(value)}</td>' for value in (
        g['subject'], g['family'], SPLIT_NAMES[g['split']],
        g['passed'], g['failed'], g['unresolved'], g['expected'],
        '证据不足' if g['pass_rate'] is None else f'{g["pass_rate"]:.1%}')) + '</tr>' for g in report['groups'])
    diagnostics = ''.join(f'<li>{escape(c["run"])}: {escape("; ".join(c["issues"]))}</li>'
                          for c in report['cells'] if c['issues'])
    diagnostics += ''.join(f'<li>未登记运行：{escape(p)}</li>' for p in report['unexpected_runs'])
    comparisons = ''.join('<li>' + escape(f'{p["family"]} / {SPLIT_NAMES[p["split"]]}: {p["candidate"]} − {p["baseline"]}: ')
                          + ('证据不足，不作比较' if not p['comparable'] else
                             escape(f'{p["delta_pass_rate"] * 100:+.1f} 个百分点')) + '</li>'
                          for p in report['comparisons'])
    return f'''<!doctype html><html lang="zh-CN"><meta charset="utf-8">
<meta name="viewport" content="width=device-width,initial-scale=1">
<title>COMACBench · {escape(report['id'])}</title>
<style>body{{font:16px/1.65 system-ui,sans-serif;max-width:1120px;margin:40px auto;padding:0 24px;color:#182230}}
h1{{font-size:30px;overflow-wrap:anywhere}}.note{{background:#f4f6f8;padding:18px;border-radius:8px}}
table{{border-collapse:collapse;width:100%;min-width:800px;font-size:14px}}td,th{{text-align:left;padding:10px;border-bottom:1px solid #ddd}}
.scroll{{overflow:auto}}code{{overflow-wrap:anywhere}}li{{overflow-wrap:anywhere}}</style>
<h1>{escape(report['id'])}</h1>
<p class="note"><strong>{'计划内结果齐全' if report['complete'] else '证据不齐，不能下完整结论'}</strong> · 公开回归<br>
未验证隔离迁移；不是飞机设计放行依据。参考实现只用于冻结契约，不计入模型成绩。</p>
<h2>哪里通过，哪里失败，哪里还没有证据</h2>
<p>{report['family_count']} 个声明任务族，{report['case_count']} 个算例配置；随机种子 {escape(report['seeds'])}。
分母为预先登记的任务执行次数，未完成项不会被删除。无跨任务族总分。窄屏可横向滚动表格。</p>
<div class="scroll"><table><thead><tr><th>Agent</th><th>任务族</th><th>分集</th><th>通过</th><th>任务未全过</th><th>待核验</th><th>计划</th><th>通过率</th></tr></thead><tbody>{table}</tbody></table></div>
<h2>配对比较</h2><ul>{comparisons or '<li>未登记对照，不计算提升。</li>'}</ul>
<h2>需要处理的证据问题</h2><ul>{diagnostics or '<li>未发现本工具覆盖范围内的 JSON 完整性问题。</li>'}</ul>
<h2>结论边界</h2><p>检查了 run.json、运行清单与原始 result JSON 的摘要、身份和判分结果。
未重新执行求解器，也未重新核验全部工程产物字节。不同包摘要不能证明任务语义不同；
相同随机种子不能证明试验独立。未登记的提示词、Skill、知识库和人工干预不在审计范围。预算配置受身份约束，实际限额执行与费用尚未审计。</p>
<p>冻结摘要：<code>{escape(report['lock_sha256'])}</code>。摘要可检测漂移，不是防伪签名。
详细证据见同目录 <a href="campaign.json">campaign.json</a>。</p></html>'''


def write_new(path: Path, value: Any) -> None:
    with path.open('x', encoding='utf-8', newline='\n') as stream:
        stream.write(json.dumps(value, ensure_ascii=False, indent=2, allow_nan=False) + '\n')


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description='只读任务族实验：冻结公开回归矩阵，核查记录，对照报告')
    sub = parser.add_subparsers(dest='command', required=True)
    freeze = sub.add_parser('freeze', help='从已完成的预检运行冻结契约；不执行 Agent 或求解器')
    freeze.add_argument('plan', type=Path)
    freeze.add_argument('--anchors', type=Path, required=True)
    freeze.add_argument('--out', type=Path, required=True)
    report = sub.add_parser('report', help='固定分母，检查原始结果，生成离线报告')
    report.add_argument('lock', type=Path)
    report.add_argument('--runs', type=Path, required=True)
    report.add_argument('--out', type=Path, required=True)
    args = parser.parse_args(argv)
    try:
        if args.command == 'freeze':
            plan, _ = read_json(args.plan)
            lock = freeze_plan(plan, args.anchors)
            write_new(args.out, lock)
            print(json.dumps({'lock': str(args.out), 'sha256': lock['sha256'], 'scope': 'public_regression'}))
            return 0
        lock, _ = read_json(args.lock)
        runs, out = args.runs.resolve(), args.out.resolve()
        require(not out.is_relative_to(runs), 'output_must_be_outside_runs')
        result = evaluate(lock, runs)
        out.mkdir(parents=True, exist_ok=False)
        write_new(out / 'campaign.json', result)
        (out / 'report.html').write_text(render_html(result), encoding='utf-8')
        print(json.dumps({'complete': result['complete'], 'report': str(out / 'report.html'),
                          'isolated_transfer_verified': False}, ensure_ascii=False))
        return 0 if result['complete'] else 2
    except (OSError, ValueError, TypeError, KeyError, RecursionError) as exc:
        print(json.dumps({'error': str(exc)}, ensure_ascii=False), file=sys.stderr)
        return 2


if __name__ == '__main__':
    raise SystemExit(main())
