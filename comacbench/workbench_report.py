"""Offline presentation of a re-reviewed workbench trace. No external assets."""
from __future__ import annotations

import html
import hashlib
import json
import shutil
from pathlib import Path
from typing import Any

from .workbench import WorkbenchError, canonical, digest, snapshot
from . import workbench_structures as structures
from . import workbench_ccx as ccx
from .workbench_admission import audit_trial, unknown_admission


LABELS = {"verified": "已验证", "stale": "已失效", "missing": "未提交",
          "unchecked": "待检查", "failed": "内容不合格"}
KINDS = {"reference": "参考策略自检（未调用模型）", "negative_control": "故障负例（非模型成绩）",
         "user_agent": "用户 Agent 会话（身份由操作者声明）"}


def render(data: dict[str, Any]) -> str:
    observation = data["observation"]
    scenario = data["manifest"]["scenario"]
    escape = lambda value: html.escape(str(value), quote=True)
    native = structures.is_native(scenario)
    done = observation["complete"]
    status = "工作包检查完成" if done else "尚未完成工作包"
    admission = {**unknown_admission(observation["subject"]["kind"]),
                 **{key: data[key] for key in ("protocol_conformance", "reference_exposure", "score_admissible", "deviation_reasons") if key in data}}
    established = (observation["subject"]["kind"] == "user_agent"
                   and admission["protocol_conformance"] == "conformant"
                   and admission["reference_exposure"] == "not_observed_in_recorded_run"
                   and admission["score_admissible"] is True
                   and not admission["deviation_reasons"])
    admission["score_admissible"] = established
    if not established and not admission["deviation_reasons"]:
        admission["deviation_reasons"] = ["准入证据缺失或状态冲突；不能确认合规或无参考暴露。"]
    admission_panel = ('<section class="card" id="score-admission"><h2 style="margin-top:0">成绩准入 · 公开开发记录</h2>'
        f'<p>protocol_conformance: <strong>{escape(admission["protocol_conformance"])}</strong> · '
        f'reference_exposure: <strong>{escape(admission["reference_exposure"])}</strong> · '
        f'score_admissible: <strong>{str(admission["score_admissible"]).lower()}</strong></p>'
        f'<p>{escape("；".join(admission["deviation_reasons"]) or "主机控制与工具记录核对通过；准入仅限同题公开开发复测。")}</p>'
        '<p>同题已公开；不代表未见题、隐藏测试、泛化能力或工程批准。未知状态不计为合规；不修改历史分数。</p></section>')
    handoff = "当前报告尚未通过有效版本检查，不能据旧报告作出交接结论。"
    if observation["statuses"].get("review") == "verified":
        reviewed = observation["artifacts"]["review"]["payload"]
        if native:
            failed = [row["point"] for row in reviewed["cases"] if not row["meets_requirement"]]
            handoff = ("固定校准梁的原始数据已复查；当前位移限值未满足：" + ", ".join(failed)
                       if failed else "固定校准梁在本任务的位移限值内；不构成工程设计批准。")
        elif reviewed["claim"] == "needs_review":
            points = ", ".join(f'{row["point"]} ({row["reason_code"]})' for row in reviewed["review_points"])
            handoff = f"工作包记录已核对，仍需澄清或审查：{points}。这些工况未进入运行清单。"
        else:
            handoff = "输入工作包可交给执行环节；尚未执行任何工程计算。"
    scope = ("原生校准桥接：复读 CalculiX 输入、日志与位移/反力数据；本报告不重新求解。"
             "仅限固定线性静力梁；本机执行与校准状态以归档检查项为准。其他平台部署及应力、疲劳、连接、完整支架设计未验证；不构成工程批准。"
             if native else "本报告只检查输入工作包与变更证据。未运行工程求解器，不代表工程性能合格或设计放行。")
    native_summary = (f"<p>本工具受理求解尝试：{observation['counts'].get('solver_calls', 0)} / "
                      f"{scenario['max_solver_calls']}；原生进程启动：{observation['counts'].get('native_processes_started', 0)}；"
                      f"累计进程墙钟：{observation['counts'].get('native_wall_s', 0):.3f} 秒。</p>"
                      if native else "")
    artifact_rows = "".join(
        f'<tr><td>{escape(node)}</td><td>{escape(LABELS[value])}</td><td>'
        + (f'<a href="artifacts/{escape(node)}.json">产物 JSON</a>' if node in observation["artifacts"] else '尚无产物') + '</td></tr>'
        for node, value in observation["statuses"].items())
    native_links = ''.join(f'<li>{escape(job)} · ' + ' · '.join(
        f'<a href="native/{escape(job)}/{escape(name)}">{escape(name)}</a>'
        for name in [*receipt["files"], "receipt.json"]) + '</li>'
        for job, receipt in data.get("native_receipts", {}).items())
    changes = []
    failures = []
    history = []
    for event in data["events"]:
        action, result = event["action"], event["result"]
        name = action.get("op", "invalid") if isinstance(action, dict) else "invalid"
        history.append(f'<tr><td>{event["seq"]}</td><td>{escape(name)}</td>'
                       f'<td>{escape(result["code"])}</td></tr>')
        if result["code"] == "phase_advanced":
            changes.append(f'<article><h3>{escape(result["phase"])}</h3>'
                           f'<p>失效：{escape(", ".join(result["invalidated"]) or "无")}</p>'
                           f'<p>保留：{escape(", ".join(result["retained"]) or "无")}</p></article>')
        if not result["ok"]:
            failures.append(f'<li>行动 {event["seq"]} · {escape(result["code"])} · '
                            f'{escape(result.get("target", ""))}</li>')
    return f'''<!doctype html>
<html lang="zh-CN"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1">
<meta http-equiv="Content-Security-Policy" content="default-src 'none'; style-src 'unsafe-inline'; base-uri 'none'; form-action 'none'">
<title>COMACBench · 变更工作包</title><style>
*{{box-sizing:border-box}}body{{margin:0;background:#f5f7f9;color:#17222f;font:16px/1.65 system-ui,sans-serif}}
main{{max-width:1040px;margin:auto;padding:32px 24px 64px}}h1{{font-size:clamp(1.6rem,4vw,2.5rem);line-height:1.25}}
h2{{margin-top:32px}}h3{{margin:0}}.label{{font-weight:700;color:#355777}}.card,article{{background:white;border:1px solid #dce3e9;border-radius:12px;padding:20px;margin:16px 0}}
.metrics{{display:grid;grid-template-columns:repeat(auto-fit,minmax(170px,1fr));gap:16px}}.metrics .card{{margin:0}}
.number{{font-size:2rem;font-weight:750}}table{{width:100%;border-collapse:collapse;table-layout:fixed}}td,th{{text-align:left;padding:12px 8px;border-bottom:1px solid #dce3e9;overflow-wrap:anywhere}}
p,li,summary{{overflow-wrap:anywhere}}summary{{cursor:pointer;font-weight:650}}a{{color:#225b87}}.muted{{color:#596878}}code{{overflow-wrap:anywhere}}
</style></head><body><main>
<p class="label">COMACBench / 工程变更工作包</p>
<h1>{escape(scenario["title"])}</h1><p>{escape(KINDS[observation["subject"]["kind"]])}</p>
{admission_panel}
<section class="card"><h2 style="margin-top:0">{status}</h2>
<details><summary>冻结场景原始说明（保留原文，不代表当前验收状态）</summary><p>{escape(scenario["description"])}</p></details><p><strong>交接结论：</strong>{escape(handoff)}</p><p><strong>{escape(scope)}</strong></p>{native_summary}</section>
<div class="metrics"><div class="card"><div class="number">{observation["actions_used"]} / {scenario["max_actions"]}</div>已消耗 / 总行动预算</div>
<div class="card"><div class="number">{sum(v == "verified" for v in observation["statuses"].values())} / {len(observation["statuses"])}</div>当前已验证 / 必需交付物</div>
<div class="card"><div class="number">{observation["counts"].get("rejected", 0)}</div>被拒绝的行动（仍计入预算）</div></div>
<h2>变更影响：重验什么，保留什么</h2>{''.join(changes) or '<p>尚未推进到变更阶段。</p>'}
<h2>当前交付状态</h2><table><thead><tr><th>交付物</th><th>状态</th><th>原始产物</th></tr></thead><tbody>{artifact_rows}</tbody></table>
{'<details class="card"><summary>原生求解原始文件</summary><ul>' + native_links + '</ul></details>' if native_links else ''}
<h2>失败与恢复记录</h2>{'<ul>' + ''.join(failures) + '</ul>' if failures else '<p>没有已记录的拒绝行动；这不证明会话外没有失败或人工介入。</p>'}
<details class="card"><summary>展开全部行动（成功与失败均保留）</summary><table><thead><tr><th>序号</th><th>行动</th><th>反馈</th></tr></thead><tbody>{''.join(history)}</tbody></table></details>
<h2>复查范围</h2><p class="muted">此报告从冻结场景和原始行动重新执行状态推进与内容检查。摘要链用于可信本地归档核对，不是签名、可信执行或对抗管理员的防篡改证明。身份为声明信息；预算仅统计本工具受理的行动，不统计模型 token、人工时间或会话外工具调用。</p>
<p class="muted">公开回归 · 未验证隔离迁移 · 未批准发布。既有 pack 与 Campaign 分数保持独立，不将阶段、重复尝试或参考策略记为新增模型能力。</p>
<p><a href="report.json">完整机器可读记录</a> · <a href="artifacts/manifest.json">交付物与状态清单</a></p></main></body></html>'''


def export_report(session: Path, out: Path, *, admission_evidence: Path | None = None) -> dict[str, Any]:
    source = session.resolve()
    destination = out.resolve()
    if destination == source or source in destination.parents or destination in source.parents:
        raise WorkbenchError("report_must_be_outside_session")
    data = snapshot(session)
    data.update(audit_trial(data, admission_evidence, session=session) if admission_evidence is not None
                else unknown_admission(data["manifest"]["subject"]["kind"]))
    out.mkdir(parents=True, exist_ok=False)
    artifact_dir = out / "artifacts"
    artifact_dir.mkdir()
    roster = []
    observation = data["observation"]
    for target, artifact in observation["artifacts"].items():
        # Target IDs come from the frozen, validated graph, never arbitrary paths.
        raw = canonical(artifact["payload"])
        name = f"{target}.json"
        (artifact_dir / name).write_bytes(raw)
        roster.append({"target": target, "path": name, "sha256": hashlib.sha256(raw).hexdigest(),
                       "artifact_sha256": digest(artifact), "basis": artifact["basis"],
                       "status": observation["statuses"][target]})
    manifest = {"protocol": "comacbench.workbench.artifacts.v1",
                "session_manifest_sha256": data["manifest"]["manifest_sha256"],
                "scenario_sha256": data["manifest"]["scenario_sha256"],
                "phase": observation["phase"], "complete": observation["complete"],
                "artifacts": roster, "solver_execution": observation["limitations"]["solver_execution"]}
    if "native_receipts" in data:
        native_dir = out / "native"
        native_dir.mkdir()
        for job_id, receipt in data["native_receipts"].items():
            src, dst = session / "native" / job_id, native_dir / job_id
            if ccx._inventory(src) != receipt["files"]:
                raise WorkbenchError("native_archive_changed_during_export")
            dst.mkdir()
            for name in receipt["files"]:
                shutil.copyfile(src / name, dst / name)
            (dst / "receipt.json").write_bytes(canonical(receipt))
            if ccx._inventory(dst) != receipt["files"]:
                raise WorkbenchError("native_copy_changed")
        manifest["native_receipts"] = data["native_receipts"]
    (artifact_dir / "manifest.json").write_bytes(canonical(manifest))
    (out / "report.json").write_text(json.dumps(data, ensure_ascii=False, indent=2, allow_nan=False) + "\n", encoding="utf-8")
    (out / "report.html").write_text(render(data), encoding="utf-8")
    return {"report": str(out / "report.html"), "complete": data["observation"]["complete"],
            "publishable": False, "solver_execution": observation["limitations"]["solver_execution"]}
