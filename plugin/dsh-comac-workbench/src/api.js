// 数据获取 + 宿主令牌 → ECharts 主题（T5 决议：getComputedStyle 读 --dsw-static-* 色阶，
// canvas 不吃 CSS 变量的缺口由启动时映射补；明暗切换时重建）。
import * as React from "react";

export function api(path) {
  return fetch("/comac/" + path.replace(/^\/+/, "")).then((r) => {
    if (!r.ok) return r.json().catch(() => ({})).then((b) => { throw new Error(b.error || ("HTTP " + r.status)); });
    return r.json();
  });
}

/** 读一个 CSS 变量的计算值（挂载在 DOM 里才能读到——工作台根节点已挂载后调用） */
function cssVar(name, fallback) {
  const v = getComputedStyle(document.documentElement).getPropertyValue(name).trim();
  return v || fallback;
}

const LEVELS = [50, 100, 300, 400, 500, 600, 800, 900];

/** 从宿主 --dsw-static-* 色阶构造 ECharts 主题（规格书 §4.3） */
export function buildTheme() {
  const pick = (hue, lv, fb) => cssVar(`--dsw-static-${hue}-${lv}`, fb);
  const palette = [
    pick("blue", 400, "#4dabf7"), pick("green", 400, "#69db7c"), pick("amber", 400, "#ffa94d"),
    pick("red", 400, "#ff8787"), pick("blue", 600, "#1c7ed6"), pick("green", 600, "#2f9e44"),
    pick("amber", 600, "#e8590c"), pick("red", 600, "#d6336c"),
  ];
  const label = cssVar("--dsw-alias-label-primary", "#ced4da");
  const labelDim = cssVar("--dsw-alias-label-dimmed", "#868e96");
  const border = cssVar("--dsw-alias-border-l2", "#2b3038");
  return {
    palette, label, labelDim, border,
    bgLayer1: cssVar("--dsw-alias-bg-layer-1", "#15191f"),
    font: cssVar("--dsw-font-family", "sans-serif"),
    fontCode: cssVar("--dsw-font-family-code", "Menlo, monospace"),
  };
}

/** 监听宿主明暗切换（html 或根容器的 class 变化）→ 回调重建主题 */
export function watchTheme(onChange) {
  const target = document.documentElement;
  let last = target.className;
  const mo = new MutationObserver(() => {
    if (target.className !== last) { last = target.className; onChange(); }
  });
  mo.observe(target, { attributes: true, attributeFilter: ["class"] });
  return () => mo.disconnect();
}

/** ECharts 按需注册（一次）+ 响应式尺寸容器 */
let echartsCore = null;
export async function ensureECharts() {
  if (echartsCore) return echartsCore;
  const [{ init, use }, charts, comps, rends] = await Promise.all([
    import("echarts/core"),
    import("echarts/charts"),
    import("echarts/components"),
    import("echarts/renderers"),
  ]);
  use([charts.RadarChart, charts.HeatmapChart, charts.BarChart, charts.ScatterChart,
    charts.LineChart,
    comps.GridComponent, comps.TooltipComponent, comps.LegendComponent, comps.TitleComponent,
    comps.VisualMapComponent,
    rends.CanvasRenderer]);
  echartsCore = { init };
  return echartsCore;
}

/** React 图表容器：init → setOption → resize 监听 → dispose（theme 从 props 读） */
export function Chart({ option, height = 240, deps = [] }) {
  const ref = React.useRef(null);
  const inst = React.useRef(null);
  const optRef = React.useRef(option);
  optRef.current = option;

  React.useEffect(() => {
    let dead = false;
    let ro = null;
    (async () => {
      const { init } = await ensureECharts();
      if (dead || !ref.current) return;
      inst.current = init(ref.current, undefined, { renderer: "canvas" });
      inst.current.setOption(optRef.current);
      ro = new ResizeObserver(() => inst.current?.resize());
      ro.observe(ref.current);
    })();
    return () => {
      dead = true;
      ro?.disconnect();
      inst.current?.dispose();
      inst.current = null;
    };
  }, []);

  React.useEffect(() => {
    if (inst.current) inst.current.setOption(option, { notMerge: true });
  }, [option, ...deps]);

  return React.createElement("div", { ref, style: { width: "100%", height } });
}

export const fmtPct = (a, b) => (b ? Math.round((a / b) * 1000) / 10 : "—");

/** failure_mode 固定配色（词表见规格书 §3.1） */
export const FM_COLOR = {
  missing_output: "#868e96", code_not_executable: "#ffa94d", simulation_failed: "#4dabf7",
  non_physical_values: "#ff8787", sandbox_escape_attempt: "#d6336c", timeout: "#fab005",
  invalid_geometry: "#b197fc", unknown: "#495057", PASS: "#69db7c",
};
export const FM_LABEL = {
  missing_output: "输出缺失", code_not_executable: "代码不可执行", simulation_failed: "仿真失败",
  non_physical_values: "非物理值", sandbox_escape_attempt: "沙箱逃逸尝试", timeout: "超时",
  invalid_geometry: "无效几何", unknown: "未知", PASS: "通过",
};
