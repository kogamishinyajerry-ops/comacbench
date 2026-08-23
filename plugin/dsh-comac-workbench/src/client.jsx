// dsh-comac-workbench client 入口 — 注册进 conversation.view ViewMap（T1/T9 先例形态）。
// 数据：/comac/* 路由（活读）或 results/_snapshots/<tag>.json（快照模式，只读）。
import * as React from "react";
import { api, watchTheme } from "./api.js";
import { css } from "./styles.js";
import { OverviewPage, MatrixPage, BenchPage, DrillPanel, MonitorPage } from "./pages.jsx";

const h = React.createElement;

// ---------- 全局一次性：CSS 注入 ----------
let styleInjected = false;
function injectStyle() {
  if (styleInjected || typeof document === "undefined") return;
  styleInjected = true;
  const el = document.createElement("style");
  el.id = "comac-wb-style";
  el.textContent = css;
  document.head.appendChild(el);
}

// ---------- 页面路由状态（URL hash 可恢复，验收 7） ----------
function parseHash() {
  // #page=matrix&date=2026-08-24 / #page=bench&rid=...&date=...&provider=... / #page=drill&...
  const h6 = (location.hash || "").replace(/^#/, "");
  const q = new URLSearchParams(h6);
  return {
    page: q.get("page") || "overview",
    date: q.get("date"), rid: q.get("rid"), provider: q.get("provider"), task: q.get("task"),
  };
}

export function Workbench() {
  const [nav, setNav] = React.useState(parseHash);
  const [mode, setMode] = React.useState("live");           // live | snapshot
  const [snapTag, setSnapTag] = React.useState(null);
  const [snapshots, setSnapshots] = React.useState([]);
  const [data, setData] = React.useState(null);             // 各页数据缓存 {overview, matrix, bench, drill, monitor}
  const [err, setErr] = React.useState(null);
  const [themeTick, setThemeTick] = React.useState(0);

  injectStyle();
  React.useEffect(() => watchTheme(() => setThemeTick((t) => t + 1)), []);
  React.useEffect(() => {
    const on = () => setNav(parseHash());
    window.addEventListener("hashchange", on);
    return () => window.removeEventListener("hashchange", on);
  }, []);

  const go = React.useCallback((next) => {
    const merged = { ...nav, ...next };
    const q = new URLSearchParams();
    for (const [k, v] of Object.entries(merged)) if (v && k !== "page") q.set(k, v);
    q.set("page", merged.page);
    location.hash = q.toString();
    setNav(merged);
  }, [nav]);

  // 活读模式数据装载
  React.useEffect(() => {
    if (mode !== "live") return;
    let dead = false;
    setErr(null);
    const load = async () => {
      try {
        if (nav.page === "overview") {
          const o = await api("overview");
          if (!dead) { setData((d) => ({ ...d, overview: o })); setSnapshots(o.snapshots ?? []); }
        } else if (nav.page === "matrix") {
          const m = await api("matrix" + (nav.date ? `?date=${encodeURIComponent(nav.date)}` : ""));
          if (!dead) setData((d) => ({ ...d, matrix: m }));
        } else if (nav.page === "bench") {
          const p = new URLSearchParams();
          if (nav.date) p.set("date", nav.date);
          if (nav.provider) p.set("provider", nav.provider);
          const b = await api(`bench/${encodeURIComponent(nav.rid)}?${p}`);
          if (!dead) setData((d) => ({ ...d, bench: b }));
        } else if (nav.page === "drill") {
          const r = await api(`task/${encodeURIComponent(nav.rid)}/${nav.date}/${nav.provider}/${nav.task}`);
          if (!dead) setData((d) => ({ ...d, drill: r.result }));
        }
      } catch (e) { if (!dead) setErr(String(e.message || e)); }
    };
    load();
    return () => { dead = true; };
  }, [nav.page, nav.date, nav.rid, nav.provider, nav.task, mode]);

  // 监控页轮询（仅活读 + 页可见）
  React.useEffect(() => {
    if (mode !== "live" || nav.page !== "monitor") return;
    let dead = false;
    const tick = async () => {
      try {
        const m = await api("runstatus");
        if (!dead) setData((d) => ({ ...d, monitor: m }));
      } catch (e) { if (!dead) setErr(String(e.message || e)); }
    };
    tick();
    const iv = setInterval(() => document.visibilityState === "visible" && tick(), 5000);
    return () => { dead = true; clearInterval(iv); };
  }, [mode, nav.page]);

  // 快照模式：一次拉全量 ViewJSON，本地派生全部页面
  React.useEffect(() => {
    if (mode !== "snapshot" || !snapTag) return;
    let dead = false;
    setErr(null);
    api(`snapshot/${encodeURIComponent(snapTag)}`).then((v) => {
      if (dead) return;
      setData({ snapshot: v });
    }).catch((e) => setErr(String(e.message || e)));
    return () => { dead = true; };
  }, [mode, snapTag]);

  // 快照派生视图矩阵
  const snapDerived = React.useMemo(() => {
    if (mode !== "snapshot" || !data?.snapshot) return null;
    const v = data.snapshot;
    const latest = [...new Set(v.runs.map((r) => r.date))].sort().pop();
    const runsOf = (date) => v.runs.filter((r) => r.date === date);
    const cellOf = (rid, prov) => {
      const r = v.runs.find((x) => x.registry_id === rid && x.provider === prov);
      if (!r) return null;
      return { score_mean: r.score_mean, gate_passed: r.gate_passed, n_tasks: r.n_tasks, failure_modes: r.failure_modes };
    };
    const dates = [...new Set(v.runs.map((r) => r.date))].sort();
    const theDate = nav.date ?? latest;
    const sel = runsOf(theDate);
    return {
      latest, dates, theDate,
      overview: {
        total: v.registry.length,
        status_counts: v.registry.reduce((a, e) => ((a[e.status] ??= 0), (a[e.status] += 1), a), {}),
        latest_date: latest, recent_runs: v.runs.slice(-10).reverse(),
        radar: v.header.mode ? [] : [],
      },
      matrix: {
        date: theDate, dates,
        rows: v.registry.filter((e) => sel.some((r) => r.registry_id === e.id)).sort((a, b) => (a.order ?? 99) - (b.order ?? 99)),
        cols: [...new Set(sel.map((r) => r.provider))],
        cells: Object.fromEntries(sel.map((r) => [r.registry_id, {
          [r.provider]: cellOf(r.registry_id, r.provider),
        }])),
      },
      benchTasks: (rid, date, provider) => {
        const i = v.runs.findIndex((r) => r.registry_id === rid && r.date === date && r.provider === provider);
        return i < 0 ? [] : v.tasks.filter((t) => t.run === i);
      },
    };
  }, [data, mode, nav.date]);

  // ---------- 渲染 ----------
  const page = nav.page;
  const tabs = [["overview", "总览"], ["matrix", "对比矩阵"], ["monitor", "运行监控"]];
  const body = () => {
    if (err) return h("div", { className: "comac-wb-err" },
      h("div", null, `加载失败：${err}`),
      h("button", { onClick: () => setErr(null) }, "重试"));
    const loading = h("div", { className: "comac-wb-load" }, "读取中…");

    if (page === "overview") {
      const d = mode === "snapshot" ? snapDerived?.overview : data?.overview;
      return d ? h(OverviewPage, { data: d, go }) : loading;
    }
    if (page === "matrix") {
      if (mode === "snapshot") {
        const sd = snapDerived;
        if (!sd) return loading;
        // 快照矩阵 cells 结构对齐：{rid: {prov: cell}}
        const cells = {};
        for (const r of data.snapshot.runs.filter((r) => r.date === sd.theDate))
          (cells[r.registry_id] ??= {})[r.provider] = {
            score_mean: r.score_mean, gate_passed: r.gate_passed, n_tasks: r.n_tasks, failure_modes: r.failure_modes,
          };
        return h(MatrixPage, {
          data: { ...sd.matrix, cells },
          date: sd.theDate, setDate: (d) => go({ page: "matrix", date: d }), go,
        });
      }
      return data?.matrix ? h(MatrixPage, { data: data.matrix, date: data.matrix.date, setDate: (d) => go({ page: "matrix", date: d }), go }) : loading;
    }
    if (page === "bench") {
      if (mode === "snapshot") {
        const v = data?.snapshot;
        if (!v) return loading;
        const i = v.runs.findIndex((r) => r.registry_id === nav.rid && r.date === nav.date && r.provider === nav.provider);
        const entry = v.registry.find((e) => e.id === nav.rid);
        const runs = v.runs.filter((r) => r.registry_id === nav.rid);
        return h(BenchPage, {
          data: { entry, runs, selected: i >= 0 ? { date: nav.date, provider: nav.provider, tasks: v.tasks.filter((t) => t.run === i) } : null },
          go, drill: (t) => go({ page: "drill", rid: nav.rid, date: nav.date, provider: nav.provider, task: t.task_id }),
        });
      }
      return data?.bench ? h(BenchPage, {
        data: data.bench, go,
        drill: (t) => go({ page: "drill", rid: nav.rid, date: t._date ?? data.bench.selected?.date, provider: t._prov ?? data.bench.selected?.provider, task: t.task_id }),
      }) : loading;
    }
    if (page === "drill") {
      const d = mode === "snapshot" ? data?.snapshot : data?.drill;
      if (!d && mode === "live") return loading;
      if (mode === "snapshot") {
        // 快照模式：钻取回源活读（时点差警示）
        return h(DrillLiveInSnap, { nav, setErr });
      }
      return data?.drill ? h(DrillPanel, {
        result: data.drill, meta: nav, back: () => go({ page: "bench", task: null }), snapshotMode: false,
      }) : loading;
    }
    if (page === "monitor") {
      return h(MonitorPage, { data: data?.monitor, live: mode === "live", snapshotMode: mode !== "live" });
    }
    return h("div", { className: "comac-wb-empty" }, `未知页: ${page}`);
  };

  return h("div", { className: "comac-wb-root", key: themeTick },
    h("div", { className: "comac-wb-topbar" },
      tabs.map(([id, label]) => h("button", {
        key: id, className: `comac-wb-tab${page === id || (id === "matrix" && (page === "bench" || page === "drill")) ? " on" : ""}`,
        onClick: () => go({ page: id, rid: null, date: null, provider: null, task: null }),
      }, label)),
      h("div", { className: "comac-wb-mode" },
        h("label", null,
          h("input", { type: "radio", checked: mode === "live", onChange: () => setMode("live"), name: "wb-mode" }),
          h("span", { className: "comac-wb-dot live", style: { margin: "0 3px 0 4px" } }), "活读"),
        mode === "live" && snapshots.length ? h("label", null,
          h("input", { type: "radio", checked: mode === "snapshot", onChange: () => setMode("snapshot"), name: "wb-mode" }),
          h("span", { className: "comac-wb-dot snap", style: { margin: "0 3px 0 4px" } }),
          h("select", {
            className: "comac-wb-snapselect", value: snapTag ?? snapshots[0],
            onChange: (e) => { setSnapTag(e.target.value); setMode("snapshot"); },
          }, snapshots.map((s) => h("option", { key: s, value: s }, s)))) : null)),
    h("div", { className: "comac-wb-body" }, body()));
}

/** 快照模式下的单题钻取：回源活读当前盘（规格书 §2.4 时点差警示） */
function DrillLiveInSnap({ nav, setErr }) {
  const [r, setR] = React.useState(null);
  const [err, setErrL] = React.useState(null);
  React.useEffect(() => {
    let dead = false;
    api(`task/${nav.rid}/${nav.date}/${nav.provider}/${nav.task}`)
      .then((v) => !dead && setR(v.result))
      .catch((e) => !dead && setErrL(String(e.message || e)));
    return () => { dead = true; };
  }, [nav.rid, nav.date, nav.provider, nav.task]);
  if (err) return h("div", { className: "comac-wb-empty" }, `读取失败：${err}`);
  if (!r) return h("div", { className: "comac-wb-load" }, "回源活读中…");
  return h(DrillPanel, {
    result: r, meta: nav, back: () => history.back(), snapshotMode: true,
  });
}

// ---------- 浏览器端 cordis 插件面（官方 bundle 同款：exports.apply + exports.inject） ----------
// inject = 客户端服务名列表（fiber 等这些服务就绪后调 apply(ctx)）。
export const inject = ["slots"];

export function apply(ctx) {
  ctx.slots.inject("conversation.view", () => ctx.slots.register({
    name: "conversation.view", id: "comac-workbench", order: 98, label: () => "工作台",
  }, Workbench));
}
