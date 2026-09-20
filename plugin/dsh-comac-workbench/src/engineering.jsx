import * as React from "react";
const h = React.createElement;
const families = { industrial_simulation: "工业仿真", enterprise_data: "企业数据处理", knowledge_ontology: "知识本体" };
const quote = (s) => "'" + s.replaceAll("'", "'\\''") + "'";

function Command({ value }) {
  const [message, setMessage] = React.useState("复制命令");
  return h("div", { className: "comac-wb-card", style: { margin: "10px 0" } },
    h("pre", { style: { whiteSpace: "pre-wrap", overflowWrap: "anywhere", fontSize: 12 } }, value),
    h("button", { className: "comac-wb-tab", onClick: async () => {
      try { await navigator.clipboard.writeText(value); setMessage("已复制"); }
      catch { setMessage("请选中上方命令复制"); }
    } }, message));
}

export function EngineeringPage({ data, snapshotMode }) {
  const [intent, setIntent] = React.useState("evaluate");
  if (snapshotMode) return h("div", { className: "comac-wb-empty" }, "工程师入口使用当前评测包，请切换到活读模式。旧快照没有贡献质量检查数据。");
  if (!data) return h("div", { className: "comac-wb-load" }, "正在检查本地评测包…");
  return h("section", { style: { maxWidth: 1080, margin: "0 auto", padding: "12px 6px" } },
    h("div", { className: "comac-wb-sub", style: { letterSpacing: 2 } }, "COMACBENCH · 航空工程 AGENT"),
    h("h1", { style: { fontSize: 26, margin: "10px 0" } }, "让你的仿真 agent 接受一次可追溯的检查"),
    h("p", { style: { lineHeight: 1.8 } }, "选择评测包，连接自己的 agent，查看实际求解、数据处理和知识关系的结果。每项分数都有检查范围与证据，材料缺口会单独反馈。"),
    h("div", { style: { display: "flex", gap: 8, margin: "18px 0" } },
      [["evaluate", "我要评测 agent"], ["contribute", "我要贡献评测集"]].map(([id, label]) => h("button", {
        key: id, className: "comac-wb-tab" + (intent === id ? " on" : ""), onClick: () => setIntent(id),
      }, label))),
    !(data.packs?.length) && h("div", { className: "comac-wb-empty" }, "尚无评测包。使用 python -m comacbench.admission init PATH 创建完整示例。"),
    (data.packs || []).map((p) => h("article", { key: p.path, className: "comac-wb-card", style: { margin: "14px 0", padding: 20 } },
      h("h2", { style: { margin: "0 0 8px", fontSize: 20 } }, p.pack.title),
      h("p", { className: "comac-wb-sub", style: { fontSize: 13 } }, `${p.pack.revision} · ${p.task_count} 个基础任务 · ${p.runnable ? "可以本地试跑" : "材料检查未通过"} · 尚未批准发布`),
      h("p", null, p.pack.description),
      h("div", { className: "comac-wb-charts", style: { margin: "18px 0" } },
        Object.entries(families).map(([id, label]) => h("div", { key: id, className: "comac-wb-card", style: { flex: "1 1 190px" } },
          h("strong", null, label), h("div", { style: { fontSize: 26 } }, p.tasks.filter(t => t.family === id).length),
          h("span", { className: "comac-wb-sub" }, id === "industrial_simulation" ? (p.tasks.some(t => t.exec_kind === "cfd_step") ? "OpenFOAM 原生网格、残差、守恒与壁面剪切" : p.issues.some(i => i.code === "partial_engineering_gate") ? "CalculiX 实际求解，建模检查仍有缺口" : "六项结构输入契约 + CalculiX 实际求解") : id === "enterprise_data" ? "单位、标识符、缺失与血缘规则" : "对象类型、关系约束、证据与缺失反馈")))),
      p.validation_evidence?.length > 0 && h("section", { style: { margin: "16px 0" } },
        h("h3", null, "CFD 研究证据 · 48 组网格与域组合"),
        h("p", null, "研究矩阵通过不等于新增评分任务。当前可评测 Re=100，公开容差 10%；下列候选带尚未用于评分。"),
        h("table", { style: { width: "100%", textAlign: "left" } },
          h("thead", null, h("tr", null, ["工况", "研究通过", "候选带", "本次核验"].map(v => h("th", { key: v }, v)))),
          h("tbody", null, p.validation_evidence.map(e => h("tr", { key: e.id },
            h("td", null, `Re=${e.reynolds}`), h("td", null, `${e.matrix_cases}/16 · 四档网格 × 四域`),
            h("td", null, `${(e.candidate_relative_tolerance*100).toFixed(1)}%（非评分）`),
            h("td", null, e.native_evidence_available === false ? "原始场已清理，仅保留历史摘要" : "分析与回执摘要通过"))))),
        h("details", null, h("summary", null, "证据路径与核验边界"),
          p.validation_evidence.map(e => h("p", { key: e.id }, h("code", null, e.analysis), " · ", e.analysis_sha256)),
          h("p", null, "快速预检未重读全部原始场；完整文件核验也不等于重新求解。"),
          h(Command, { value: "python -m comacbench.evidence --full" }))),
      intent === "evaluate" ? h(React.Fragment, null,
        h("h3", null, "三步开始评测"),
        h("p", null, "1. 先核对评测包的材料与检查范围。"),
        h(Command, { value: `python -m comacbench.admission validate ${quote(p.path)}` }),
        h("p", null, p.tasks.some(t => t.exec_kind === "cfd_step") ? "2. 准备 agent.json，将 inputs/ 中八份公开模板交给自己的 agent，返回生成原生 case/ 输入的脚本。平台代跑 OpenFOAM；接口自检配置见 examples/agents/cfd-reference.json。" : "2. 准备 agent.json：命令从 stdin 接收任务 JSON，向 stdout 返回 task_id 和最终答案。参考配置见 examples/agents/model.json；已有 agent 只需接上这层输入输出。"),
        h(Command, { value: `python -m comacbench.admission run ${quote(p.path)} --agent ./agent.json --out ./my-evaluation-01` }),
        h("p", null, "3. 打开输出目录的 report.html，先看未通过任务，再下钻判分数值、证据路径与未覆盖要求。也可在 DSH 调用 comac_agent_run / comac_agent_result。")) : h(React.Fragment, null,
        h("h3", null, "从完整示例开始贡献"),
        h(Command, { value: "python -m comacbench.admission init ./my-benchmark-pack" }),
        h("p", null, "准备题面、公开输入、参考答案及来源、不确定度/容差、输出要求、检查器、需求追踪与错误负例。题面和输入摘要需要随材料修订更新。"),
        h(Command, { value: "python -m comacbench.admission validate ./my-benchmark-pack --out ./contribution-feedback-01" }),
        h("p", null, "预检只读材料；修复阻断项后，在受控环境显式执行正负例校准，再提交工程专家审查。校准通过不会自动发布。"),
        h(Command, { value: "python -m comacbench.admission calibrate ./my-benchmark-pack --out ./contribution-calibration-01" })),
      h("details", { open: !p.runnable || intent === "contribute", style: { marginTop: 18 } },
        h("summary", { style: { cursor: "pointer" } }, `材料质量反馈：${p.summary.blocker} 项阻断 · ${p.summary.review} 项需审查`),
        p.issues.map((i, n) => h("div", { key: n, className: "comac-wb-warn", style: { marginTop: 10, fontSize: 12 } },
          h("strong", null, `${i.severity === "blocker" ? "阻断" : "需审查"}：${i.message}`),
          h("p", null, i.suggested_fix), h("code", { style: { overflowWrap: "anywhere" } }, i.field)))))));
}
