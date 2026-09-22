"""report.html 首屏 completion 透传的回归测试。

背景（2026-09-22，推进方案工作项 E）：PR #1 给 run.json 加了 `completion` 字段，
但报告首屏分母仍是 `rows.length`（已记录结果数），计划任务数与基础设施作废
没有展示——「2 个计划任务只收到 1 个结果」会被显示成 1/1 而非 1/2。

本测试不启动浏览器：提取 report.html 的 <script> 段，在最小 DOM stub 下执行，
断言首屏完整性行的三种形态。这覆盖了「JS 改了但没人跑过」的坑（方案 §3 明确
指出此前只有源码审查没有浏览器验证）。
"""
import json
import re
import shutil
import unittest
from pathlib import Path

TEMPLATE = Path(__file__).resolve().parents[1] / 'comacbench' / 'report.html'


def _node():
    node = shutil.which('node')
    if not node:
        raise unittest.SkipTest('node 不在 PATH，无法验证报告 JS')
    return node


_RUNNER_JS = """\
// 最小 DOM stub：执行 report.html 的首屏渲染前缀，打印插到 #stats 之后的行。
const fs = require('fs');
const doc = JSON.parse(fs.readFileSync(process.argv[2], 'utf8'));
const prefix = fs.readFileSync(process.argv[3], 'utf8');
let captured = null;
const mkEl = () => ({ textContent: '', className: '', style: { cssText: '' },
  children: [], onclick: null, onchange: null,
  append(...c) { this.children.push(...c); }, replaceChildren() {},
  setAttribute() {}, classList: { add() {}, remove() {} },
  querySelectorAll: () => [], after(n) { captured = n; } });
const elements = {};
global.document = { createElement: mkEl, createElementNS: mkEl,
  getElementById: id => elements[id] || (elements[id] = mkEl()) };
global.navigator = { clipboard: { writeText: async () => {} } };
const js = prefix.replace(
  "const d=JSON.parse(document.getElementById('data').textContent)",
  'const d=' + JSON.stringify(doc));
eval(js);
console.log(JSON.stringify(captured
  ? { text: captured.textContent, cls: captured.className } : null));
"""

BASE_DOC = {
    'pack': {'title': 'T', 'id': 'p', 'revision': '1'},
    'mode': 'calibrate', 'status': 'complete',
    'validation': {'runnable': True, 'summary': {'blocker': 0, 'review': 0},
                   'tasks': [{'family': 'enterprise_data'},
                             {'family': 'knowledge_ontology'}],
                   'issues': []},
    'results': [
        {'id': 'a', 'family': 'enterprise_data', 'full_pass': True,
         'result_issues': [], 'scope': 's', 'requirements': []},
        {'id': 'b', 'family': 'knowledge_ontology', 'full_pass': False,
         'result_issues': ['voided_result'], 'score': 0.4,
         'scope': 's', 'requirements': []},
    ],
    'controls': [{'task_id': 't', 'score': 0, 'max_score': 0, 'passed': True}],
}


def _script_prefix():
    """模板 script 段，截断到 renderTasks 的绑定循环之前（那里有 TDZ 依赖）。"""
    tpl = TEMPLATE.read_text(encoding='utf-8')
    m = re.search(r'<script>([\s\S]*?)</script>', tpl)
    assert m, 'report.html 缺少 <script> 段'
    js = m.group(1)
    cut = js.find('for(const [value,label]')
    assert cut > 0, '渲染绑定循环的锚点不存在，模板结构已变'
    return js[:cut]


def _run(doc):
    """在 node 的最小 DOM stub 下执行首屏渲染前缀，返回提示行 {text, cls}。"""
    import subprocess
    runner = Path(__file__).with_name('_report_js_runner.js')
    runner.write_text(_RUNNER_JS, encoding='utf-8')
    env_doc = Path(__file__).with_name('_report_doc.json')
    env_doc.write_text(json.dumps(doc, ensure_ascii=False), encoding='utf-8')
    prefix_file = Path(__file__).with_name('_report_prefix.js')
    prefix_file.write_text(_script_prefix(), encoding='utf-8')
    cleanup = lambda: [f.unlink(missing_ok=True) for f in
                       (runner, env_doc, prefix_file)]
    try:
        out = subprocess.run([_node(), runner.name, env_doc.name, prefix_file.name],
                             cwd=str(runner.parent), capture_output=True,
                             text=True, timeout=30)
        if out.returncode != 0:
            raise AssertionError(f'JS 执行失败: {out.stderr[-500:]}')
        return json.loads(out.stdout) if out.stdout.strip() else None
    finally:
        cleanup()


class CompletionFirstScreenTests(unittest.TestCase):

    def test_incomplete_run_shows_plan_and_gap(self):
        """缺任务 + 有作废结果：计划数、已记录、可计分、差异、作废计数都要出现。"""
        doc = dict(BASE_DOC, completion={
            'expected_tasks': 3, 'recorded_results': 2, 'scorable_results': 2,
            'missing_tasks': ['x/y'], 'unexpected_tasks': [],
            'duplicate_results': [], 'complete': False})
        line = _run(doc)
        self.assertIsNotNone(line)
        s = line['text']
        self.assertIn('计划 3 项', s)
        self.assertIn('已记录 2', s)
        self.assertIn('可计分 2', s)
        self.assertIn('未通过', s)
        self.assertIn('x/y', s)
        self.assertIn('基础设施作废 1', s)
        self.assertEqual(line['cls'], 'warn')

    def test_legacy_archive_is_labelled(self):
        """历史档案（无 completion 字段）：标注未知，而不是假装分母正确。"""
        line = _run(dict(BASE_DOC))
        self.assertIsNotNone(line)
        self.assertIn('历史档案', line['text'])
        self.assertIn('未验证计划任务数', line['text'])

    def test_complete_run_shows_pass_without_gap_list(self):
        doc = dict(BASE_DOC, completion={
            'expected_tasks': 2, 'recorded_results': 2, 'scorable_results': 2,
            'missing_tasks': [], 'unexpected_tasks': [],
            'duplicate_results': [], 'complete': True})
        line = _run(doc)
        s = line['text']
        self.assertIn('计划 2 项', s)
        self.assertIn('通过', s)
        self.assertNotIn('差异', s)
        self.assertNotEqual(line['cls'], 'warn')

    def test_first_screen_no_longer_claims_completed_tasks(self):
        """旧标签「已完成任务」必须消失：它是把分母当任务的措辞。"""
        tpl = TEMPLATE.read_text(encoding='utf-8')
        self.assertNotIn('已完成任务', tpl)


if __name__ == '__main__':
    unittest.main()
