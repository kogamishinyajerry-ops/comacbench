"""gen_tasks_cfdb.py — 从镜像的 GLM-CFD-Benchmark(cfdb) 案例生成任务 YAML + 题面。

上游：github.com/kogamishinyajerry-ops/GLM-CFD-Benchmark（MIT），本地克隆
  /Users/Zhuanz/projects/cfd/runtimes/cfdb，镜像 revision 锁 commit b26799e。
镜像目录：data/cfdb/{case_setup,verification,validation}/<case>/（整目录逐字镜像）。

生成物（全部可重入，--check 校验漂移）：
  tasks/cfdb.case_setup/cfdb_cs_<case>.yaml|.md    17 任务（solver-agnostic 工程任务书）
  tasks/cfdb.verification/cfdb_vf_<case>.yaml|.md  10 任务（解析/程序化参考的 V&V 案例）
  tasks/cfdb.validation/cfdb_vd_<case>.yaml|.md    15 任务（实验/跨代码参考的验证案例）

判分契约（registry 状态 staged 的原因：simulation_agent 的 cfdb_* exec_kind 分支待实现）：
  - case_setup managed 模式：判分侧真实运行提交案例（OpenFOAM v2312 docker：blockMesh →
    controlDict.application），由案例冻结的 reference/compute_qoi.py 提取 QoI 对账 held_out；
  - case_setup evidence 模式：判分不跑求解器，agent 提交证据包（manifest.json + solver.log +
    mesh_report + 样本 CSV），同一冻结脚本在宿主从原始证据降算 QoI —— 内网商业 CFD 兼容；
  - verification/validation：managed 模式同上，参考值见 case.yaml reference/held_out。
  上游 trust 机制（隐藏 checker sha256 锚定、LLM-judge 永不进判分）与本项目九维度判分
  纪律同构，详见上游 docs/architecture/Architecture-v5.0-multi-domain.md。

用法（仓库根）：
  python3 -m runners.gen_tasks_cfdb            # 生成/覆盖
  python3 -m runners.gen_tasks_cfdb --check    # 只校验
"""

from __future__ import annotations

import argparse
import hashlib
from pathlib import Path

import yaml

from .common import sha256_file

BENCH = Path(__file__).resolve().parent.parent
DATA = BENCH / "data/cfdb"
UPSTREAM = {
    "repo": "github.com/kogamishinyajerry-ops/GLM-CFD-Benchmark",
    "revision": "cfdb@b26799e",          # 镜像时上游 HEAD（见 PROVENANCE）
    "license": "MIT",
}
DOMAINS = [
    ("case_setup", "cfdb.case_setup", "cfdb_cs", "cfdb_case_setup"),
    ("verification", "cfdb.verification", "cfdb_vf", "cfdb_verification"),
    ("validation", "cfdb.validation", "cfdb_vd", "cfdb_validation"),
]


def _load_case(d: Path) -> dict:
    return yaml.safe_load((d / "case.yaml").read_text(encoding="utf-8"))


def _qoi_ref(case: dict, cdir: Path) -> dict:
    """从 case.yaml 汇出判分参考段（与上游 trust 语义一致，不复制数值语义）。"""
    ref = {"type": (case.get("reference") or {}).get("type", "unknown")}
    qvals = (case.get("reference") or {}).get("qoi_values")
    if qvals:
        ref["qoi_values_public"] = qvals
        ref["held_out_note"] = "held_out/qoi.json 为判分对账源；上游注明与公开值同源（机制演示）"
    held = cdir / "held_out" / "qoi.json"
    if held.exists():
        ref["held_out"] = {
            "path": str(held.relative_to(BENCH)),
            "digest": sha256_file(held),
        }
    ref["qoi_script"] = (case.get("outputs") or {}).get("qoi_script") or "reference/compute_qoi.py"
    ref["tolerances"] = ((case.get("metrics") or {}).get("qoi_relative_tolerance")
                         or {}).copy()
    ref["uncertainty_note"] = "容差为上游文档化决策（网格/格式耗散），见 case.yaml metrics 注释"
    return ref


def _case_setup_prompt(cid: str, task_md_rel: str) -> str:
    return (
        f"# cfdb case_setup — {cid}\n\n"
        f"请阅读以下工程任务书（附图 data/cfdb/case_setup/{cid}/visible/drawing.png，"
        f"如存在），在允许的求解器环境中完成案例搭建与求解，并按任务书提交产物/证据包。\n\n"
        f"---\n\n"
        f"{{PLACEHOLDER_TASK_MD}}\n"
    ).replace("{PLACEHOLDER_TASK_MD}", "") + f"任务书全文见镜像文件: {task_md_rel}\n"


def _vf_prompt(cid: str, case: dict, dom: str) -> str:
    phys = case.get("physics") or {}
    cond = case.get("conditions") or {}
    qoi = (case.get("outputs") or {}).get("qoi") or []
    ref_type = (case.get("reference") or {}).get("type", "unknown")
    lines = [
        f"# cfdb {dom} — {case.get('name', cid)}",
        "",
        case.get("description", "").strip(),
        "",
        "## 要求",
        f"- 求解器族: OpenFOAM（上游基准使用 ESI v2312 语义）；从零搭建完整可运行案例"
        f"（0/ constant/ system/ + Allrun），真实求解到 case 指定的终止时刻。",
        f"- 物理设定: flow={phys.get('flow')}, turbulence={phys.get('turbulence')}, "
        f"dim={phys.get('dimensionality')}, steady={phys.get('steady')}",
        f"- 工况: " + ", ".join(f"{k}={v}" for k, v in cond.items() if v is not None),
        f"- 输出 QoI: {', '.join(qoi) if qoi else '(见任务 YAML reference)'}",
        f"- 参考类型: {ref_type}（容差见任务 YAML reference.tolerances；判分用冻结 QoI 脚本）",
        "",
        "## 交付",
        "写 result.json，字段为上述 QoI 名（数值，与 QoI 定义单位一致）。",
        "",
    ]
    return "\n".join(lines)


def build_yaml(tid: str, registry_id: str, case: dict, cdir: Path, prompt_rel: str,
               prompt_sha: str, assets: list[dict], mode_note: str) -> dict:
    budget = case.get("budget") or {}
    return {
        "id": tid,
        "registry_id": registry_id,
        "domain": "cfd",
        "task_type": "simulation_agent",
        "model_profile": "code_tool_agent",
        "assets_revision": UPSTREAM["revision"],
        "environment_digest": "computed-at-runtime",
        "hidden": False,
        "allowed_tools": ["shell", "openfoam", "python"],
        "input": {
            "prompt_file": prompt_rel,
            "prompt_sha256": prompt_sha,
            "assets": assets,
        },
        "output_contract": ["result.json"] if "case_setup" not in registry_id
                          else ["case_directory", "result.json"],
        "reference": _qoi_ref(case, cdir),
        "grader": {
            "validity_gate": True,
            "exec_kind": UPSTREAM_EXEC[registry_id],
            "solver_backend": "openfoam-v2312-docker（managed 模式）；evidence 模式判分不跑求解器",
            "mode": case.get("execution", {}).get("setup_mode", "managed")
                    if "case_setup" in registry_id else "managed",
            "convergence_check": "上游 cfdb 冻结 QoI 脚本 + 容差判分（LLM-judge 永不进判分）",
            "qoi_script": (case.get("outputs") or {}).get("qoi_script")
                          or "reference/compute_qoi.py",
            "upstream_note": mode_note,
        },
        "scoring": {
            "weights": {"physics": 0.6, "requirements": 0.4,
                        "objective": 0.0, "robustness": 0.0},
            "note": "physics=QoI 对账（容差内 1.0/超容差 0）；requirements=案例结构/证据包契约完整率；"
                    "objective/robustness N/A（上游基准无目标函数/扰动重算）",
        },
        "limits": {
            "cpu": 2,
            "memory_gb": 4,
            "wall_clock_s": int(budget.get("max_runtime_sec") or 900),
            "attempts": 3,
        },
        "license_provenance": {
            "source": UPSTREAM["repo"],
            "license": "MIT",
            "status": "confirmed-repo",
            "revision": UPSTREAM["revision"],
            "mirror_allowed": True,
        },
    }


UPSTREAM_EXEC = {
    "cfdb.case_setup": "cfdb_case_setup",
    "cfdb.verification": "cfdb_cfd_qoi",
    "cfdb.validation": "cfdb_cfd_qoi",
}



def _read_no_translate(p):
    if not p.exists():
        return ""
    with open(p, encoding="utf-8", newline="") as f:
        return f.read()

def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--check", action="store_true")
    args = ap.parse_args()
    drift = []
    total = 0
    for dom, rid, prefix, _exec in DOMAINS:
        root = DATA / dom
        tdir = BENCH / "tasks" / rid
        tdir.mkdir(parents=True, exist_ok=True)
        for cdir in sorted(root.iterdir()):
            if not (cdir / "case.yaml").exists():
                continue
            case = _load_case(cdir)
            cid = case.get("id") or cdir.name
            tid = f"{prefix}_{cid}"
            if dom == "case_setup":
                src_md = cdir / "visible" / "task.md"
                prompt = src_md.read_text(encoding="utf-8")
            else:
                prompt = _vf_prompt(cid, case, dom)
            prompt_rel = f"tasks/{rid}/{tid}.md"
            sha = hashlib.sha256(prompt.encode("utf-8")).hexdigest()
            assets = [{"path": f"data/cfdb/{dom}/{cid}/case.yaml",
                       "digest": sha256_file(cdir / "case.yaml")}]
            drawing = cdir / "visible" / "drawing.png"
            if drawing.exists():
                assets.append({"path": f"data/cfdb/{dom}/{cid}/visible/drawing.png",
                               "digest": sha256_file(drawing)})
            mode_note = ("上游 evidence 模式：判分验证证据包并由冻结脚本降算 QoI（内网商业 CFD 兼容）"
                         if case.get("execution", {}).get("setup_mode") == "evidence"
                         else "上游 managed 模式：判分侧真实运行提交案例（blockMesh → application）")
            y = build_yaml(tid, rid, case, cdir, prompt_rel, sha, assets, mode_note)
            want_yaml = yaml.safe_dump(y, sort_keys=False, allow_unicode=True)
            ypath = tdir / f"{tid}.yaml"
            ppath = tdir / f"{tid}.md"
            total += 1
            if args.check:
                gy = _read_no_translate(ypath)
                gp = _read_no_translate(ppath)
                if gy != want_yaml or gp != prompt:
                    drift.append(tid)
            else:
                ypath.write_text(want_yaml, encoding="utf-8")
                ppath.write_text(prompt, encoding="utf-8")
    if args.check:
        if drift:
            print(f"[check] 漂移: {drift}")
            return 1
        print(f"[check] OK — {total} 任务一致")
        return 0
    print(f"[gen] 写出 {total} 任务")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
