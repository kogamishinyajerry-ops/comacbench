// 五页视图组件（规格书 §2.1–2.5）。
import * as React from "react";
import { api, Chart, buildTheme, fmtPct, FM_COLOR, FM_LABEL } from "./api.js";
import { css } from "./styles.js";

const h = React.createElement;

// ---------- 总览（§2.1） ----------
export function OverviewPage({ data, go }) {
  const { status_counts = {}, total = 0, latest_date, radar = [], recent_runs = [], dates = [] } = data ?? {};
  const sc = status_counts;
  const segColors = { integrated: "#2f9e44", active: "#1971c2", staged: "#3bc9db", proposed: "#e8590c", deferred: "#868e96", excluded: "#495057", "paused-env": "#c92a2a" };
  const segTotal = Object.values(sc).reduce((a, b) => a + b, 0) || 1;
  const nineDims = ["知识", "编程", "CAD", "CFD", "结构", "动力", "飞控", "总体MDO", "鲁棒审计"];

  const radarOption = React.useMemo(() => {
    const t = buildTheme();
    return {
      backgroundColor: "transparent",
      tooltip: {},
      legend: { bottom: 0, textStyle: { color: t.labelDim, fontSize: 10, fontFamily: t.font }, itemWidth: 12, itemHeight: 8 },
      radar: {
        indicator: nineDims.map((n) => ({ name: n, max: 1 })),
        axisName: { color: t.label, fontSize: 10, fontFamily: t.font },
        splitLine: { lineStyle: { color: t.border } },
        splitArea: { areaStyle: { color: ["transparent"] } },
        axisLine: { lineStyle: { color: t.border } },
      },
      series: [{
        type: "radar", symbolSize: 3,
        data: (radar || []).map((s, i) => ({
          name: s.name, value: s.values,
          lineStyle: { width: 1.6 }, areaStyle: { opacity: 0.08 },
          itemStyle: { color: t.palette[i % t.palette.length] },
          lineStyle_color: undefined,
        })),
      }],
      color: buildTheme().palette,
    };
  }, [radar]);

  return h("div", null,
    h("div", { className: "comac-wb-h" }, `家底 · ${total} 项基准`),
    h("div", { className: "comac-wb-seg" },
      Object.entries(segColors).filter(([k]) => sc[k]).map(([k, c]) =>
        h("div", { key: k, style: { background: c, flex: sc[k] }, title: `${k}: ${sc[k]}` },
          `${FM_LABEL[k] ? k : k} ${sc[k]}`))),
    h("div", { className: "comac-wb-sub" },
      Object.entries(sc).map(([k, v]) => `${k}=${v}`).join(" · ") + ` · 最新数据日 ${latest_date ?? "—"}`),

    h("div", { className: "comac-wb-h" }, `九维度雷达（${latest_date ?? "—"}，点图例切换 provider）`),
    h("div", { className: "comac-wb-card comac-wb-flex1" },
      h(Chart, { option: radarOption, height: 300, deps: [radar] })),

    h("div", { className: "comac-wb-h" }, "最近运行"),
    h("table", { className: "comac-wb-table" },
      h("thead", null, h("tr", null, ["基准", "日期", "provider", "gate", "均分"].map((x) => h("th", { key: x }, x)))),
      h("tbody", null, (recent_runs || []).map((r, i) =>
        h("tr", { key: i, className: "clickable", onClick: () => go({ page: "bench", rid: r.registry_id, date: r.date, provider: r.provider }) },
          h("td", null, r.registry_id), h("td", null, r.date), h("td", null, r.provider),
          h("td", { className: "comac-wb-num" }, `${r.gate_passed}/${r.n_tasks}`),
          h("td", { className: "comac-wb-num" }, r.score_mean ?? "—"))))),
  );
}

// ---------- 对比矩阵（§2.2） ----------
export function MatrixPage({ data, date, setDate, go }) {
  const { rows = [], cols = [], cells = {}, dates = [] } = data ?? {};
  const t = buildTheme();

  const heatOption = React.useMemo(() => {
    const ys = rows.map((r) => r.id);
    const hm = [];
    for (const [ri, r] of rows.entries()) {
      for (const [ci, c] of cols.entries()) {
        const cell = cells[r.id]?.[c];
        hm.push([ci, ri, cell ? (cell.score_mean ?? 0) : -1,
          cell ? `${r.gate_passed ?? "?"}/${cell.gate_passed ?? "?"}` : ""]);
      }
    }
    return {
      backgroundColor: "transparent",
      tooltip: {
        formatter: (p) => {
          const r = rows[p.value[1]], c = cols[p.value[0]];
          const cell = cells[r.id]?.[c];
          if (!cell) return `${r.id} × ${c}<br/>无数据`;
          const fm = Object.entries(cell.failure_modes || {}).filter(([k]) => k !== "PASS")
            .map(([k, n]) => `${FM_LABEL[k] || k}×${n}`).join("、");
          return `<b>${r.id}</b> × ${c}<br/>均分 ${cell.score_mean ?? "—"} · gate ${cell.gate_passed}/${cell.n_tasks}` +
            (fm ? `<br/>${fm}` : "") + (cell.rerun_command ? `<br/><span style="color:#868e96">点击行查看 · 重跑命令在 tooltip 外（详情页）</span>` : "");
        },
      },
      grid: { left: 220, right: 20, top: 24, bottom: 44 },
      xAxis: { type: "category", data: cols, axisLabel: { color: t.label, fontSize: 10, fontFamily: t.fontCode, rotate: 24 }, splitLine: { show: false } },
      yAxis: { type: "category", data: ys, axisLabel: { color: t.label, fontSize: 10, fontFamily: t.fontCode }, splitLine: { show: false } },
      visualMap: {
        min: 0, max: 1, calculable: false, orient: "horizontal", left: "center", bottom: 0,
        textStyle: { color: t.labelDim, fontSize: 10 },
        inRange: { color: ["#c92a2a", "#e8590c", "#fab005", "#69db7c"] },
      },
      series: [{
        type: "heatmap",
        data: hm,
        label: { show: false },
        itemStyle: { borderColor: t.bgLayer1, borderWidth: 2, borderRadius: 3 },
      }],
    };
  }, [data]);

  return h("div", null,
    h("div", { className: "comac-wb-crumb" },
      "日期：",
      h("select", {
        className: "comac-wb-snapselect", value: date ?? dates[dates.length - 1] ?? "",
        onChange: (e) => setDate(e.target.value),
      }, dates.map((d) => h("option", { key: d, value: d }, d))),
      h("span", { style: { marginLeft: "12px" } }, `行=基准(${rows.length}) 列=provider(${cols.length}) · 格=均分 · 斜纹/-1=缺数据`)),
    h("div", { className: "comac-wb-card" },
      h(Chart, { option: heatOption, height: Math.max(220, 28 + rows.length * 34), deps: [data] })),
    h("div", { className: "comac-wb-sub" }, "点击热力图下方数字表格行进基准详情；表头排序；缺数据格显 -1（灰）"),
    h("table", { className: "comac-wb-table" },
      h("thead", null, h("tr", null, h("th", null, "基准"), cols.map((c) => h("th", { key: c, className: "comac-wb-num" }, c)))),
      h("tbody", null, rows.map((r) =>
        h("tr", { key: r.id, className: "clickable", onClick: () => go({ page: "bench", rid: r.id, date: data.date }) },
          h("td", { title: r.name }, r.id),
          cols.map((c) => {
            const cell = cells[r.id]?.[c];
            return h("td", { key: c, className: "comac-wb-num" },
              cell ? `${(cell.score_mean ?? 0).toFixed(3)} (${fmtPct(cell.gate_passed, cell.n_tasks)}%)` : "—");
          }))))),
  );
}

// ---------- 基准详情（§2.3） ----------
export function BenchPage({ data, go, drill }) {
  const { entry, runs = [], selected, providers_of_date } = data ?? {};
  if (!entry) return h("div", { className: "comac-wb-empty" }, "未知基准");
  const t = buildTheme();

  const trajOption = React.useMemo(() => {
    const byProv = {};
    for (const r of runs) (byProv[r.provider] ??= []).push(r);
    const series = Object.entries(byProv).map(([p, rs], i) => ({
      name: p, type: "scatter",
      data: rs.map((r) => [r.date, r.score_mean ?? 0, r.n_tasks, r.registry_id]),
      symbolSize: (v) => Math.max(6, Math.min(22, Math.sqrt(v[2] || 1) / 2)),
      itemStyle: { color: t.palette[i % t.palette.length], opacity: 0.85 },
    }));
    return {
      backgroundColor: "transparent",
      tooltip: { formatter: (p) => `${p.seriesName}<br/>${p.value[3]} @ ${p.value[0]}<br/>均分 ${p.value[1]} · ${p.value[2]} 题` },
      legend: { bottom: 0, textStyle: { color: t.labelDim, fontSize: 10 }, itemWidth: 12, itemHeight: 8 },
      grid: { left: 40, right: 16, top: 16, bottom: 40 },
      xAxis: { type: "category", data: [...new Set(runs.map((r) => r.date))].sort(), axisLabel: { color: t.labelDim, fontSize: 10, fontFamily: t.fontCode } },
      yAxis: { type: "value", min: 0, max: 1, axisLabel: { color: t.labelDim, fontSize: 10 }, splitLine: { lineStyle: { color: t.border } } },
      series,
    };
  }, [runs]);

  const fmCounts = {};
  for (const r of runs) for (const [k, n] of Object.entries(r.failure_modes || {})) if (k !== "PASS") fmCounts[k] = (fmCounts[k] ?? 0) + n;
  const fmOption = React.useMemo(() => {
    const entries = Object.entries(fmCounts).sort((a, b) => b[1] - a[1]);
    return {
      backgroundColor: "transparent",
      tooltip: {},
      grid: { left: 110, right: 30, top: 8, bottom: 24 },
      xAxis: { type: "value", axisLabel: { color: t.labelDim, fontSize: 10 }, splitLine: { lineStyle: { color: t.border } } },
      yAxis: { type: "category", data: entries.map(([k]) => FM_LABEL[k] || k), axisLabel: { color: t.label, fontSize: 10 } },
      series: [{ type: "bar", data: entries.map(([k, n]) => ({ value: n, itemStyle: { color: FM_COLOR[k] || "#868e96" } })), barMaxWidth: 16 }],
    };
  }, [runs]);

  const subMeans = {};
  for (const r of runs) for (const [k, v] of Object.entries(r.subscore_means || {})) if (typeof v === "number") (subMeans[k] ??= []).push(v);
  const subAvg = Object.fromEntries(Object.entries(subMeans).map(([k, vs]) => [k, Math.round((vs.reduce((a, b) => a + b, 0) / vs.length) * 1000) / 1000]));

  return h("div", null,
    h("div", { className: "comac-wb-h" }, `${entry.id} `, h("span", { className: `comac-wb-badge ${entry.status}` }, entry.status)),
    h("div", { className: "comac-wb-card", style: { marginBottom: 12 } },
      h("dl", { className: "comac-wb-kv" },
        h("dt", null, "名称"), h("dd", null, entry.name ?? "—"),
        h("dt", null, "tier/batch"), h("dd", null, `${entry.tier ?? "—"} · ${entry.batch ?? "—"}`),
        h("dt", null, "adapter/env"), h("dd", null, `${entry.adapter ?? "—"} · ${entry.env_class ?? "—"}`),
        h("dt", null, "license"), h("dd", null, `${entry.license ?? "—"}（${entry.license_status ?? "?"}）`),
        h("dt", null, "assets"), h("dd", { className: "comac-wb-num" }, entry.assets_revision ?? "—"),
        entry.risks?.length ? h("dt", null, "风险") : null,
        entry.risks?.length ? h("dd", null, entry.risks.join("；")) : null)),
    h("div", { className: "comac-wb-charts", style: { marginBottom: 12 } },
      h("div", { className: "comac-wb-card comac-wb-flex2" },
        h("div", { className: "comac-wb-sub" }, "历次运行轨迹（x=日期 y=均分 点大小=题数；点图例过滤；点hover 看明细，任务表在下方按 selected）"),
        h(Chart, { option: trajOption, height: 220, deps: [runs] })),
      h("div", { className: "comac-wb-card comac-wb-flex1" },
        h("div", { className: "comac-wb-sub" }, "gate 失败模式累计（全部 runs）"),
        Object.keys(fmCounts).length ? h(Chart, { option: fmOption, height: 220, deps: [runs] }) : h("div", { className: "comac-wb-empty" }, "零 gate 失败 🎉"),
        h("div", { className: "comac-wb-sub", style: { marginTop: 8 } },
          "子分均值：", Object.entries(subAvg).length
            ? Object.entries(subAvg).map(([k, v]) => h("span", { key: k, className: "comac-wb-chip" }, `${k} ${v}`))
            : "—"))),
    providers_of_date && providers_of_date.length
      ? h("div", { className: "comac-wb-sub" }, "该日期 providers：",
          providers_of_date.map((pv) =>
            h("span", {
              key: pv,
              className: "comac-wb-chip",
              style: selected && selected.provider === pv ? { color: "#74c0fc", borderColor: "#74c0fc" } : {},
              onClick: () => go({ page: "bench", rid: entry.id, date: selected?.date, provider: pv }),
            }, pv)))
      : null,
    selected ? TaskTable({ tasks: selected.tasks, meta: selected, drill }) : h("div", { className: "comac-wb-empty" }, "从总览/矩阵点入或传 date+provider 查看任务表"),
  );
}

export function TaskTable({ tasks, meta, drill, filterGateFail = false }) {
  const [failOnly, setFailOnly] = React.useState(filterGateFail);
  const rows = failOnly ? tasks.filter((t) => t.gate === 0) : tasks;
  return h("div", null,
    h("div", { className: "comac-wb-sub" },
      `任务明细 ${meta ? `${meta.date} / ${meta.provider}` : ""} · ${tasks.length} 题`,
      h("label", { style: { marginLeft: 12, cursor: "pointer" } },
        h("input", { type: "checkbox", checked: failOnly, onChange: (e) => setFailOnly(e.target.checked) }), " 只看 gate 失败")),
    h("table", { className: "comac-wb-table" },
      h("thead", null, h("tr", null, ["task", "gate", "failure_mode", "score", "physics", "requirements", "objective", "robustness", "agent_s"].map((x) => h("th", { key: x }, x)))),
      h("tbody", null, rows.map((t) =>
        h("tr", { key: t.task_id, className: "clickable", onClick: () => drill(t) },
          h("td", { className: "comac-wb-num" }, t.task_id),
          h("td", { className: t.gate ? "comac-wb-g1" : "comac-wb-g0" }, t.gate),
          h("td", null, t.failure_mode ? h("span", { className: "comac-wb-fm", style: { color: FM_COLOR[t.failure_mode] } }, FM_LABEL[t.failure_mode] || t.failure_mode) : "—"),
          h("td", { className: "comac-wb-num" }, t.score),
          ["physics", "requirements", "objective", "robustness"].map((k) =>
            h("td", { key: k, className: "comac-wb-num" }, t.subscores ? (t.subscores[k] ?? "—") : "—")),
          h("td", { className: "comac-wb-num" }, t.agent_s ?? "—"))))));
}

// ---------- 单题下钻（§2.4） ----------
export function DrillPanel({ result, meta, back, snapshotMode }) {
  if (!result) return h("div", { className: "comac-wb-empty" }, "无该题数据");
  const r = result;
  let mm = {};
  try { mm = JSON.parse(r.artifacts?.model_meta || "{}"); } catch {}
  return h("div", null,
    h("div", { className: "comac-wb-crumb" },
      h("b", { onClick: back }, "← 返回"), " · ", `${meta.rid} / ${meta.date} / ${meta.provider} / ${r.task_id}`),
    snapshotMode ? h("div", { className: "comac-wb-warn" }, "⚠ 快照模式：单题下钻读当前盘，可能与快照时点有差异") : null,
    h("div", { className: "comac-wb-drill" },
      h("div", { className: "comac-wb-card comac-wb-flex1" },
        h("span", { className: `comac-wb-gatebadge ${r.validity_gate ? "pass" : "fail"}` },
          r.validity_gate ? "GATE PASS" : `GATE FAIL · ${r.failure_mode || "unknown"}`),
        h("dl", { className: "comac-wb-kv" },
          h("dt", null, "score"), h("dd", { className: "comac-wb-num" }, String(r.score)),
          ["physics", "requirements", "objective", "robustness"].map((k) => [
            h("dt", { key: k }, k),
            h("dd", { key: k + "v", className: "comac-wb-num" },
              r.subscores?.[k] != null ? String(r.subscores[k]) : `N/A（${r.subscore_applicability?.[k] ?? "不适用"}）`),
          ]),
          h("dt", null, "model"), h("dd", null, `${mm.provider ?? "—"} / ${mm.model ?? "—"}${mm.escalated ? "（升级重试）" : ""}`),
          h("dt", null, "timings"), h("dd", { className: "comac-wb-num" }, `agent ${r.timings?.agent_s ?? "—"}s · setup ${r.timings?.setup_s ?? "—"}s · grade ${r.timings?.grade_s ?? "—"}s`),
          h("dt", null, "assets"), h("dd", { className: "comac-wb-num", style: { fontSize: 10 } }, r.assets_revision ?? "—"))),
      h("div", { className: "comac-wb-card comac-wb-flex2" },
        h("div", { className: "comac-wb-sub" }, `adapter 载荷（${r.adapter}）`),
        ArtifactBlock(r))),
    r.logs?.length ? h("div", { style: { marginTop: 10 } },
      h("div", { className: "comac-wb-sub" }, "logs"),
      h("pre", { className: "comac-wb-pre" }, r.logs.join("\n"))) : null,
  );
}

function ArtifactBlock(r) {
  const a = r.artifacts ?? {};
  const blocks = [];
  if (a.answer != null) blocks.push(["答案", String(a.answer)]);
  if (a.prediction != null) {
    try {
      const p = typeof a.prediction === "string" ? JSON.parse(a.prediction) : a.prediction;
      const gd = a.grade_details ? (typeof a.grade_details === "string" ? JSON.parse(a.grade_details) : a.grade_details) : {};
      const hits = gd.hits ? Object.entries(gd.hits).map(([k, v]) =>
        `${k}: pred=${v.pred} true=${v.true?.toPrecision(4)} rel_err=${Math.round(v.rel_err * 10) / 10}%`).join("\n") : "";
      blocks.push(["预测 vs 真值", JSON.stringify(p, null, 1) + (hits ? "\n\n" + hits : "")]);
    } catch { blocks.push(["prediction", String(a.prediction)]); }
  }
  if (a.code) blocks.push(["代码", typeof a.code === "string" && a.code.startsWith('"') ? JSON.parse(a.code) : a.code]);
  if (a.grade_details && !a.prediction) {
    try { blocks.push(["判分明细", JSON.stringify(typeof a.grade_details === "string" ? JSON.parse(a.grade_details) : a.grade_details, null, 1)]); }
    catch { blocks.push(["判分明细", String(a.grade_details)]); }
  }
  if (!blocks.length) blocks.push(["artifacts", JSON.stringify(a, null, 1).slice(0, 2000)]);
  return h("div", null, blocks.map(([t, body]) =>
    h("div", { key: t, style: { marginBottom: 8 } },
      h("div", { className: "comac-wb-sub" }, t),
      h("pre", { className: "comac-wb-pre" }, String(body).slice(0, 4000)))));
}

// ---------- 运行监控（§2.5） ----------
export function MonitorPage({ data, live, snapshotMode }) {
  if (snapshotMode) return h("div", { className: "comac-wb-empty" }, "监控页只有活读模式（快照模式下禁用——快照是冻结视图）");
  const running = data?.running ?? [];
  if (!running.length) return h("div", { className: "comac-wb-empty" },
    "当前无在跑批。起跑请在会话里用 comac_run（UI 纯只读）。",
    h("div", { style: { marginTop: 8, fontSize: 11 } }, `自动轮询中（5s）· live=${String(live)}`));
  return h("div", null,
    h("div", { className: "comac-wb-h" }, `在跑 ${running.length} 批（5s 自动轮询）`),
    running.map((r, i) => h("div", { key: i, className: "comac-wb-card comac-wb-moncard", style: { marginBottom: 10 } },
      h("div", null,
        h("b", null, r.registry_id), ` · ${r.provider} · ${r.date} · pid ${r.pid ?? "?"}`,
        h("span", { style: { float: "right", color: "#868e96", fontSize: 11 } }, `${r.results_done}${r.n_tasks ? "/" + r.n_tasks : ""} 题`)),
      h("div", { className: "comac-wb-bar" },
        h("div", { style: { width: r.n_tasks ? Math.min(100, (r.results_done / r.n_tasks) * 100) + "%" : "0%" } })),
      r.log_tail ? h("pre", { className: "comac-wb-pre", style: { maxHeight: 90 } }, r.log_tail) : null)),
  );
}
