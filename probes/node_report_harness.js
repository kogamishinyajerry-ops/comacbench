// node_report_harness.js — 在最小 DOM stub 上执行 report.html 的完整 <script>，
// 覆盖 renderTasks 全路径（PR-C）。用法：
//   node node_report_harness.js <script.js> <scenario.json>
// 输出一行 JSON：{page_errors, task_cards, tasks_text, calibration_text,
//                reproduce_text, stats_text, errors_after_filter}
// 这是模板级验证，不是 DSH host/UI 集成或真实模型运行。
'use strict';
const fs = require('fs');
const vm = require('vm');

const scriptSrc = fs.readFileSync(process.argv[2], 'utf8');
const doc = JSON.parse(fs.readFileSync(process.argv[3], 'utf8'));

// ---- 最小 DOM stub：按 report.html 实际用到的 DOM 面实现 ----
// 使用面（来自浏览器探针与源码通读）：getElementById / createElement /
// createElementNS / append / replaceChildren / after / textContent /
// className / classList / style / value / onclick / onchange /
// setAttribute / querySelectorAll('button')
function makeStyle() {
  return new Proxy({}, {get: (t, k) => (k in t ? t[k] : ''),
                        set: (t, k, v) => { t[k] = v; return true; }});
}
function makeElement(tag) {
  const el = {
    tagName: String(tag).toUpperCase(),
    children: [],
    parent: null,
    textContent: '',
    className: '',
    value: '',
    attrs: {},
    style: makeStyle(),
    classList: {
      add(...c) { el.className = (el.className + ' ' + c.join(' ')).trim(); },
      remove(...c) { el.className = el.className.split(/\s+/)
        .filter(x => x && !c.includes(x)).join(' '); },
      contains(c) { return el.className.split(/\s+/).includes(c); },
    },
    append(...nodes) { for (const n of nodes) {
      if (n == null) continue; if (typeof n === 'object' && n.parent) continue;
      if (typeof n === 'object') n.parent = el; el.children.push(n); } },
    replaceChildren(...nodes) { el.children = []; el.append(...nodes); },
    after(...nodes) { if (el.parent) {
      const i = el.parent.children.indexOf(el);
      el.parent.children.splice(i + 1, 0, ...nodes);
    } },
    setAttribute(k, v) { el.attrs[k] = v; },
    querySelectorAll(sel) {
      // 最小实现：仅支持 report.html 用到的 'button' 标签选择器
      if (String(sel).toLowerCase() !== 'button') return [];
      const out = [];
      walk(el, n => { if (n.tagName === 'BUTTON') out.push(n); });
      return out;
    },
  };
  return el;
}
function walk(el, fn) { fn(el); for (const c of el.children)
  if (c && typeof c === 'object') walk(c, fn); }
function collectText(el) {
  let out = typeof el.textContent === 'string' ? el.textContent : '';
  for (const c of el.children) if (c && typeof c === 'object') out += collectText(c);
  return out;
}

const registry = {};
const ensure = id => (registry[id] || (registry[id] = makeElement('div')));
const dataEl = makeElement('script');
dataEl.textContent = JSON.stringify(doc);

const documentStub = {
  getElementById: id => (id === 'data' ? dataEl : ensure(id)),
  createElement: tag => makeElement(tag),
  createElementNS: (_ns, tag) => makeElement(tag),
};
ensure('severity').value = 'all'; // 真实 <select> 默认选中首个 option（全部问题）

const sandbox = {
  document: documentStub,
  navigator: {clipboard: {writeText: async () => {}}},
  JSON, Math, Number, Array, Object, String, Boolean, isNaN, isFinite,
  setTimeout, clearTimeout,
};
vm.createContext(sandbox);

const pageErrors = [];
try {
  vm.runInContext(scriptSrc, sandbox, {timeout: 10000});
} catch (e) {
  pageErrors.push(String(e && e.stack ? e.message : e));
}

// 采集“全部”筛选下的初始状态（等价浏览器加载完成后的断言时点）
const tasks = ensure('tasks');
const taskCards = tasks.children.filter(
  c => c && c.tagName === 'DETAILS' && /(^|\s)task(\s|$)/.test(c.className)).length;
const tasksTextAll = collectText(tasks);

// 模拟点击“有缺口”筛选按钮（等价浏览器探针的 filter 点击步骤）
let errorsAfterFilter = [];
try {
  const filters = ensure('filters');
  const buttons = [];
  walk(filters, n => { if (n.tagName === 'BUTTON') buttons.push(n); });
  const failed = buttons.find(b => collectText(b).includes('有缺口'));
  if (failed && typeof failed.onclick === 'function') failed.onclick();
} catch (e) {
  errorsAfterFilter = [String(e && e.message ? e.message : e)];
}

const out = {
  page_errors: pageErrors,
  task_cards: taskCards,
  tasks_text: tasksTextAll,
  calibration_text: collectText(ensure('calibration')),
  reproduce_text: collectText(ensure('reproduce')),
  stats_text: collectText(ensure('stats')),
  errors_after_filter: errorsAfterFilter,
};
process.stdout.write(JSON.stringify(out));
