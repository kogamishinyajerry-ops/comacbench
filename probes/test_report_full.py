# -*- coding: utf-8 -*-
"""test_report_full.py — PR-C 报告异常路径完整执行测试（fix3 修复版）。

层次：
  a) Node 层：抽出 report.html 的 <script>，在最小 DOM stub（node_report_harness.js）
     上执行全路径，8 个情景断言：无异常、任务卡数正确、作废原因文本非空、
     校准/复跑区域存在、筛选切换无异常。
  b) 静态层：文本位置比较，断言 const body 定义先于首次 body 使用（TDZ 回归）。
  c) 浏览器层：如 Playwright+Chromium 可用则真实浏览器跑 8 情景；不可用如实
     标注 NOT_RUN。本机 playwright wheel 缺 driver/node.exe，需指向系统 node
     （脚本自动探测处理）；此为模板级验证，不是 DSH host/UI 集成验收。

运行：python test_report_full.py（退出码 0=全部通过）
"""
import copy
import json
import os
import subprocess
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
NODE = r"C:\Program Files\nodejs\node.exe"
PY = sys.executable

# ---------------------------------------------------------------- 情景构造
# 与 evidence/browser 合成档案（probe_report_browser.py）同构，另加零结果与
# 校准失败两个情景，共 8 个。
BASE = {
    'pack': {'id': 'acceptance-fixture', 'title': '报告验收测试（合成档案）',
             'revision': 'audit',
             'description': '以下数据仅用于报告显示测试，不是真实模型或工程成绩。'},
    'mode': 'calibrate', 'status': 'complete', 'agent': {'name': 'audit fixture'},
    'validation': {'runnable': True, 'summary': {'blocker': 0, 'review': 0},
                   'tasks': [{'id': 'a', 'family': 'enterprise_data'}], 'issues': []},
    'completion': {'expected_tasks': 1, 'recorded_results': 1,
                   'scorable_results': 1, 'missing_tasks': [],
                   'unexpected_tasks': [], 'duplicate_results': [],
                   'complete': True},
    'results': [{'id': 'a', 'family': 'enterprise_data', 'full_pass': True,
                 'validity_gate': 1, 'score': 1, 'result_issues': [],
                 'scope': '合成报告验收行', 'requirements': [], 'gate_failures': [],
                 'details': {'kind': 'unit_tests'},
                 'evidence_level': 'executable_checks'}],
    'controls': [], 'calibration_passed': True,
    'rerun': 'python -m comacbench calibrate FIXTURE --out TEST --resume',
}


def make_scenarios():
    s = {}
    s['healthy'] = copy.deepcopy(BASE)

    d = copy.deepcopy(BASE)
    d['status'] = 'interrupted'
    d['error'] = 'audit fixture infrastructure failure'
    d['calibration_passed'] = False
    d['results'][0].update(full_pass=False, validity_gate=0, score=0,
                           result_issues=['voided_result'])
    d['completion'].update(complete=False, scorable_results=0)
    s['voided_first'] = d  # 第一题作废：历史上 renderTasks TDZ 崩溃点

    d = copy.deepcopy(BASE)
    r = copy.deepcopy(s['voided_first']['results'][0])
    r['id'] = 'b'
    d['results'].append(r)
    d['validation']['tasks'].append({'id': 'b', 'family': 'enterprise_data'})
    d['completion'].update(expected_tasks=2, recorded_results=2,
                           scorable_results=1, complete=False)
    d['status'] = 'interrupted'
    d['error'] = 'second fixture row is voided'
    d['calibration_passed'] = False
    s['voided_second'] = d  # 第二题作废

    d = copy.deepcopy(BASE)
    d.pop('completion')
    s['legacy'] = d  # 历史档案（无 completion 字段）

    d = copy.deepcopy(BASE)
    d['status'] = 'interrupted'
    d['error'] = 'missing expected result'
    d['validation']['tasks'].append({'id': 'b', 'family': 'enterprise_data'})
    d['completion'].update(expected_tasks=2, complete=False,
                           missing_tasks=['enterprise.data/b'])
    s['missing_result'] = d  # 任务缺失

    d = copy.deepcopy(BASE)
    d['results'] = []
    d['completion'].update(recorded_results=0, scorable_results=0,
                           complete=False)
    d.pop('controls')   # 空数组的 controls 在 JS 中为真值，会渲染校准区
    d.pop('rerun')      # 零结果情景同样移除复跑区，断言两区域均不出现
    s['zero_results'] = d  # 零结果

    d = copy.deepcopy(BASE)
    d['calibration_passed'] = False
    s['calibration_failed'] = d  # 校准失败：校准区域必须渲染“禁止发布”

    d = copy.deepcopy(BASE)
    d['results'][0].update(
        id='workload_baseline_01',
        evidence_level='file_artifacts_checked',
        details={'kind': 'deliverable_review',
                 'evaluator': {'checks': [
                     {'name': 'normalized_present', 'passed': True}]}})
    s['file_artifacts_checked'] = d  # 新证据类别：文件制品核验标签
    return s


# 期望：情景 -> (任务卡数, 校准区可见, 复跑区可见)
NODE_EXPECT = {
    'healthy': (1, True, True),
    'voided_first': (1, True, True),   # 修复后：作废行也渲染出任务卡
    'voided_second': (2, True, True),
    'legacy': (1, True, True),
    'missing_result': (1, True, True),
    'zero_results': (0, False, False),  # 零结果：无卡片（有占位文案）
    'calibration_failed': (1, True, True),
    'file_artifacts_checked': (1, True, True),
}


def extract_script(html: str) -> str:
    start = html.index('<script>', html.index('id="data"'))
    end = html.index('</script>', start)
    return html[start + len('<script>'):end]


def run_node_layer() -> bool:
    scenarios = make_scenarios()
    tmp = HERE / '.tmp_node'
    tmp.mkdir(exist_ok=True)
    script_js = tmp / 'report_script.js'
    script_js.write_text(extract_script(
        (Path(__file__).resolve().parents[1] / 'comacbench' / 'report.html').read_text(encoding='utf-8')), encoding='utf-8')
    harness = HERE / 'node_report_harness.js'
    ok = True
    print('== Node 层（vm + 最小 DOM stub，renderTasks 全路径）==')
    for name, doc in scenarios.items():
        f = tmp / f'{name}.json'
        f.write_text(json.dumps(doc, ensure_ascii=False), encoding='utf-8')
        r = subprocess.run([NODE, str(harness), str(script_js), str(f)],
                           capture_output=True, text=True, timeout=60)
        if r.returncode != 0:
            print(f'  {name:22s} HARNESS_FAIL rc={r.returncode} '
                  f'{r.stderr.strip()[:200]}')
            ok = False
            continue
        out = json.loads(r.stdout)
        exp_cards, exp_cal, exp_rep = NODE_EXPECT[name]
        errs = []
        if out['page_errors']:
            errs.append(f"page_errors={out['page_errors']}")
        if out['task_cards'] != exp_cards:
            errs.append(f"cards {out['task_cards']}!={exp_cards}")
        if bool(out['calibration_text']) != exp_cal:
            errs.append('calibration_text 可见性不符')
        if bool(out['reproduce_text']) != exp_rep:
            errs.append('reproduce_text 可见性不符')
        if out['errors_after_filter']:
            errs.append(f"filter_errors={out['errors_after_filter']}")
        # 作废情景：作废原因文本必须非空（任务卡内可见）
        if name in ('voided_first', 'voided_second') and \
                '结果信封异常' not in out['tasks_text']:
            errs.append('作废原因文本缺失')
        if name == 'calibration_failed' and '禁止发布' not in out['calibration_text']:
            errs.append('校准失败文案缺失')
        if name == 'file_artifacts_checked' and '文件制品核验' not in out['tasks_text']:
            errs.append('file_artifacts_checked 标签缺失')
        if name == 'zero_results' and '尚未执行任务' not in out['tasks_text']:
            errs.append('零结果占位文案缺失')
        status = 'PASS' if not errs else 'FAIL'
        if errs:
            ok = False
        print(f'  {name:22s} {status} errors={out["page_errors"]} '
              f'cards={out["task_cards"]}'
              + (f' | {errs}' if errs else ''))
    return ok


def run_static_layer() -> bool:
    print('== 静态层（const body 先于首次使用，文本位置比较）==')
    html = (Path(__file__).resolve().parents[1] / 'comacbench' / 'report.html').read_text(encoding='utf-8')
    script = extract_script(html)
    ok = True
    for i, line in enumerate(script.split('\n'), 1):
        decl = line.find('const body=')
        if decl < 0:
            continue
        first_use = line.find('body.append')
        first_use2 = line.find('body,')
        uses = [u for u in (first_use, first_use2) if u >= 0]
        if not uses:
            print(f'  line {i}: FAIL 未找到 body 使用点')
            ok = False
            continue
        first = min(uses)
        verdict = 'PASS' if decl < first else 'FAIL'
        if verdict == 'FAIL':
            ok = False
        print(f'  line {i}: {verdict} decl@{decl} < first_use@{first}')
    return ok


def run_browser_layer() -> str:
    """返回 'RUN+n/n' 或 'NOT_RUN(原因)'。"""
    print('== 浏览器层（Playwright + Chromium，8 情景）==')
    try:
        import playwright._impl._transport as t  # noqa: F401
        import playwright._impl._driver as drv
    except ImportError:
        print('  NOT_RUN: playwright 未安装')
        return 'NOT_RUN(playwright 未安装)'
    node_ok = Path(NODE).is_file()
    bundled = Path(drv.compute_driver_executable()[0])
    if not bundled.is_file():
        if not node_ok:
            print('  NOT_RUN: playwright driver 缺 node.exe 且系统 node 不可用')
            return 'NOT_RUN(driver 缺 node 且系统 node 不可用)'
        orig = drv.compute_driver_executable
        drv.compute_driver_executable = lambda: (NODE, orig()[1])
        t.compute_driver_executable = drv.compute_driver_executable
        note = 'driver/node.exe 缺失，已指向系统 node'
    else:
        note = 'bundled driver'
    try:
        from playwright.sync_api import sync_playwright
    except ImportError:
        return 'NOT_RUN(sync_api 导入失败)'

    scenarios = make_scenarios()
    html = (Path(__file__).resolve().parents[1] / 'comacbench' / 'report.html').read_text(encoding='utf-8')
    outdir = HERE / 'evidence-browser'
    outdir.mkdir(exist_ok=True)
    results = []
    passed = 0
    try:
        with sync_playwright() as p:
            browser = p.chromium.launch(headless=True)
            for name, doc in scenarios.items():
                page = browser.new_page()
                errors = []
                page.on('pageerror', lambda e, _l=errors: _l.append(str(e)))
                page.set_content(html.replace(
                    '/*__DATA__*/',
                    json.dumps(doc, ensure_ascii=False).replace('<', '\\u003c')),
                    wait_until='load')
                cards = page.locator('#tasks > details').count()
                # textContent 而非 inner_text：作废原因在默认闭合的 <details>
                # 内，inner_text 会跳过不可见内容
                tasks_text = page.locator('#tasks').evaluate(
                    'e => e.textContent')
                cal = page.locator('#calibration').inner_text()
                rep = page.locator('#reproduce').inner_text()
                exp_cards, exp_cal, exp_rep = NODE_EXPECT[name]
                errs = []
                if errors:
                    errs.append(f'pageerror={errors}')
                if cards != exp_cards:
                    errs.append(f'cards {cards}!={exp_cards}')
                if bool(cal) != exp_cal or bool(rep) != exp_rep:
                    errs.append('cal/rep 可见性不符')
                if name in ('voided_first', 'voided_second') and \
                        '结果信封异常' not in tasks_text:
                    errs.append('作废原因文本缺失')
                page.get_by_role('button', name='有缺口', exact=True).click()
                if len(errors) > len(errs) or any('pageerror' in e for e in errs):
                    pass
                if name in ('voided_first', 'voided_second') and errors:
                    errs.append(f'post_filter_errors={errors}')
                status = 'PASS' if not errs else 'FAIL'
                if not errs:
                    passed += 1
                print(f'  {name:22s} {status} errors={errors} cards={cards}'
                      + (f' | {errs}' if errs else ''))
                results.append({'scenario': name, 'page_errors': errors,
                                'task_cards': cards, 'status': status})
                page.close()
            browser.close()
    except Exception as e:
        msg = f'NOT_RUN(浏览器启动失败: {str(e)[:120]})'
        print(' ', msg)
        return msg
    (outdir / 'browser-results-fix3.json').write_text(
        json.dumps(results, ensure_ascii=False, indent=2) + '\n',
        encoding='utf-8')
    tag = f'RUN {passed}/{len(scenarios)} ({note})'
    print(f'  汇总: {tag}')
    return tag


def run_evidence_level_unit() -> bool:
    print('== completion.py classify_evidence_level 单元断言 ==')
    sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "comacbench"))
    import completion as C
    cases = [
        ({'result_issues': [], 'evidence_level': 'solver_executed'},
         'solver_executed'),
        ({'result_issues': [], 'evidence_level': 'executable_checks'},
         'executable_checks'),
        ({'result_issues': ['voided_result'],
          'details': {'kind': 'deliverable_review'},
          'artifacts': {'engineering_evidence': '{}'}},
         'no_completed_execution'),  # 作废行绝不给已核验证据
        ({'result_issues': [], 'details': {'kind': 'deliverable_review'},
          'artifacts': {'engineering_evidence':
                        '{"complete":true,"files":{}}'}},
         'file_artifacts_checked'),
        ({'result_issues': [], 'details': {'kind': 'deliverable_review'}},
         'no_completed_execution'),  # 无归档事实 → 不升级
        ({'result_issues': [], 'details': {'kind': 'unit_tests'}},
         'executable_checks'),  # unit_tests 详情 → 可执行检查（与 __main__ 分级一致）
        ({'result_issues': [], 'evidence_level': 'file_artifacts_checked'},
         'file_artifacts_checked'),
        ('not-a-dict', 'no_completed_execution'),
    ]
    ok = True
    for row, want in cases:
        got = C.classify_evidence_level(row)
        good = got == want
        ok = ok and good
        print(f'  {"PASS" if good else "FAIL"} '
              f'{json.dumps(row, ensure_ascii=False)[:70]} -> {got}'
              + ('' if good else f' (期望 {want})'))
    return ok


def main() -> int:
    ok1 = run_evidence_level_unit()
    ok2 = run_node_layer()
    ok3 = run_static_layer()
    browser_tag = run_browser_layer()
    all_ok = ok1 and ok2 and ok3
    print('== 汇总 ==')
    print(f'  evidence_level 单元: {"PASS" if ok1 else "FAIL"}')
    print(f'  Node 层 8 情景:      {"PASS" if ok2 else "FAIL"}')
    print(f'  静态层 TDZ:          {"PASS" if ok3 else "FAIL"}')
    print(f'  浏览器层:            {browser_tag}')
    print('RESULT:', 'ALL_PASS' if all_ok else 'FAILED',
          '(浏览器层结果见上方标注)')
    return 0 if all_ok else 1


if __name__ == '__main__':
    sys.exit(main())
