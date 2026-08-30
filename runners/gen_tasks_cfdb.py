"""gen_tasks_cfdb.py — 从镜像的 GLM-CFD-Benchmark(cfdb) 案例生成任务 YAML + 题面。

上游：github.com/kogamishinyajerry-ops/GLM-CFD-Benchmark（MIT），本地克隆
  /Users/Zhuanz/projects/cfd/runtimes/cfdb，镜像 revision 锁 commit b26799e。
镜像目录：data/cfdb/{case_setup,verification,validation}/<case>/（整目录逐字镜像）。

生成物（全部可重入，--check 校验漂移）：
  tasks/cfdb.case_setup/cfdb_cs_<case>.yaml|.md    17 任务（14 evidence 休眠 + 3 managed 就绪）
  tasks/cfdb.verification/cfdb_vf_<case>.yaml|.md   9 任务（managed，判分侧真跑 v2312）
  tasks/cfdb.validation/cfdb_vd_<case>.yaml|.md    10 任务（managed，判分侧真跑 v2312）
  data/cfdb/oracle_scripts/<dom>__<case>.py        managed 案例的 oracle（复制镜像参考算例）
  data/cfdb/exclusions.json                        排除案例与原因（先例：cfdcode 9 排除）

判分契约（2026-08-28 与 simulation_agent._run_cfdb_task 对齐）：
  managed 模式：模型输出单个 ```python 脚本，在沙箱 cwd 创建 case/ 完整算例
  （0/ constant/ system/）；判分侧 docker opencfd v2312 按案例冻结 steps 真实求解，
  宿主执行案例冻结 compute_qoi.py 降算 QoI，与 held_out/qoi.json 逐键容差对账——
  自报 QoI 永不进入判分（上游 trust 机制，LLM-judge 同样永不进判分）。
  evidence 模式（exec_kind=cfdb_case_setup_evidence）：休眠——需工具执行通道，
  纯 LLM provider 无法诚实产出 solver log，runner 到达即按 evidence_channel_missing 作废。

用法（仓库根）：
  python3 -m runners.gen_tasks_cfdb            # 生成/覆盖
  python3 -m runners.gen_tasks_cfdb --check    # 只校验
"""

from __future__ import annotations

import argparse
import hashlib
import json
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
    ("case_setup", "cfdb.case_setup", "cfdb_cs"),
    ("verification", "cfdb.verification", "cfdb_vf"),
    ("validation", "cfdb.validation", "cfdb_vd"),
]

# 排除案例（不生成任务；原因进 exclusions.json 与 PROVENANCE；先例 cfdcode 9 排除）
EXCLUDE = {
    ("verification", "flat_plate_su2"):
        "SU2 求解器案例：dev 终端无 SU2 后端镜像（仅 OpenFOAM v10/v2312），待 SU2 后端后纳入",
    ("validation", "lid_driven_cavity"):
        "参考算例不完整（0/ 与 system/ 未镜像；该族由 re400/re1000 完整变体覆盖）",
    ("validation", "naca0012"):
        "参考算例未镜像（snappyHexMesh 链需 gen_geometry.py 构建几何，无现成 0/constant/system）",
    ("validation", "naca0012_a5"):
        "同 naca0012：参考算例未镜像（snappy 链）",
    ("validation", "naca0012_a10"):
        "同 naca0012：参考算例未镜像（snappy 链）",
    ("validation", "naca0012_a15"):
        "同 naca0012：参考算例未镜像（snappy 链）",
    ("validation", "dam_break"):
        "瞬态前锋位置 QoI 取\"最近写出时间\"场（跨运行 FP/时间步漂移敏感）：oracle 复现 "
        "front_z_tau 前沿 15.5% vs 上游 15% 容差边界，违反 oracle 满分纪律，留档复核后再纳入",
    ("validation", "naca0012_sa_tmr"):
        "上游冻结 solve timeout 600s 在本机 arm64 原生不足（endTime=2000 步实测 55%@600s，"
        "QoI 在收敛中途无定义）；上游上调预算后重新纳入（NACA0012 SA-TMR 为最高民机相关案例，优先）",
}


# evidence 工具通道：brief 与镜像参考算例的参数匹配表（2026-08-30 逐对核验，
# 见 report/2026-08-28-cfd-agent-survey.md）——steps 从参考算例 case.yaml 继承
#（step 超时 ×2 作为本机执行缓冲：预算是执行资源，非判据；QoI/容差/参考不动）
CASE_REFS = {
    # managed case_setup 的参数匹配参考（cavity_from_brief 为 Re=100，oracle 内改 nu）
    "backward_step_from_brief": "validation/backward_facing_step_laminar",
    "cavity_re400_from_brief": "validation/lid_driven_cavity_re400",
    "couette_from_brief": "verification/couette_shear",
    "heat_conduction_from_brief": "verification/heat_conduction_1d",
    "naca0012_force_from_brief": "validation/naca0012_sa_tmr",
    "natural_convection_from_brief": "validation/natural_convection_cavity",
    "oblique_shock_from_brief": "verification/oblique_shock",
    "pipe_from_brief": "verification/pipe_poiseuille",
    "sod_shock_from_brief": "verification/sod_shock_tube",
    "taylor_couette_from_brief": "verification/taylor_couette",
    "taylor_green_from_brief": "verification/taylor_green_vortex",
    "turbulent_channel_from_brief": "validation/turbulent_channel_retau180",
    "turbulent_plate_from_brief": "validation/turbulent_flat_plate",
}

# evidence 工具通道的 dev 侧执行步骤（agent 侧工具 = harness 代跑 OpenFOAM v2312；
# 逐案例声明，与通道实装同批：2026-08-30 blasius 样例先行）
CASE_REFS["poiseuille_from_brief"] = "verification/channel_poiseuille"
CASE_REFS["cavity_from_brief"] = "validation/lid_driven_cavity_re400"
EVIDENCE_STEPS = {
    ("case_setup", "blasius_plate_from_brief"): [
        {"name": "block_mesh", "command": "blockMesh -case {{ case_dir }}",
         "timeout_sec": 120, "critical": True},
        {"name": "solve", "command": "simpleFoam -case {{ case_dir }}",
         "timeout_sec": 900, "critical": True},
    ],
}


def _read_no_translate(p: Path) -> str:
    if not p.exists():
        return ""
    with open(p, encoding="utf-8", newline="") as f:
        return f.read()


def _load_case(d: Path) -> dict:
    return yaml.safe_load((d / "case.yaml").read_text(encoding="utf-8"))


def _managed_prompt(cid: str, case: dict, dom: str) -> str:
    """managed 模式题面：与 simulation_agent._run_cfdb_task 的判分契约逐条对应。"""
    phys = case.get("physics") or {}
    cond = case.get("conditions") or {}
    qoi = (case.get("outputs") or {}).get("qoi") or []
    ref_type = (case.get("reference") or {}).get("type", "unknown")
    lines = [
        f"# cfdb {dom} — {case.get('name', cid)}",
        "",
        case.get("description", "").strip(),
        "",
        "## 交付形式（严格遵守）",
        "输出**单个 ```python 代码块**：脚本在当前工作目录创建 `case/` 子目录，",
        "写入完整可运行的 OpenFOAM 算例（至少 `0/`、`constant/`、`system/`，含",
        "`system/controlDict` 且其 `application` 条目声明所用求解器；需要 blockMesh",
        "的算例写 `system/blockMeshDict`）。不要自行运行求解器——判分侧会在",
        "OpenFOAM v2312 环境按案例声明的步骤（blockMesh → 求解器 → 后处理）真实执行，",
        "然后用案例冻结的 QoI 脚本从算例产物提取指标并与留出参考值对账。",
        "",
        "## 物理与工况",
        f"- flow={phys.get('flow')}, turbulence={phys.get('turbulence')}, "
        f"dim={phys.get('dimensionality')}, steady={phys.get('steady')}",
        "- 工况: " + (", ".join(f"{k}={v}" for k, v in cond.items() if v is not None) or "(见上)"),
        f"- 评测 QoI（判分脚本从你的算例产物提取）: {', '.join(qoi) if qoi else '(见任务 YAML reference)'}",
        f"- 参考类型: {ref_type}；容差为上游文档化决策（网格/格式耗散），不自报数值。",
        "",
        "注意：采样/后处理 functionObject（probes、forces 等）必须按上方描述正确配置，",
        "否则判分脚本将因找不到产物而判 0 分（它不会编造数值）。",
        "",
    ]
    return "\n".join(lines)


def _evidence_prompt(cid: str, case: dict, cid_dir_name: str) -> str:
    required = (case.get("execution", {}).get("evidence", {}).get("required_files") or [])
    task_md = DATA / "case_setup" / cid_dir_name / "visible" / "task.md"
    brief = task_md.read_text(encoding="utf-8") if task_md.exists() else ""
    lines = [
        f"# cfdb case_setup（evidence 工具通道）— {case.get('name', cid_dir_name)}",
        "",
        "## 两阶段交付协议（严格遵守）",
        "你的脚本会被判分环境执行**两次**，以工作目录下的标记文件 `.cfdb_assemble` 区分：",
        "",
        "**阶段 1（首次执行，无标记）**：在当前目录创建 `case/` 子目录，写入完整可运行的",
        "OpenFOAM 算例（`0/` `constant/` `system/`，`system/controlDict` 的 `application`",
        "声明求解器，并按任务书配置采样/监测 functionObject）。判分环境会在 OpenFOAM",
        "v2312 真实执行该算例（blockMesh → 求解器）：`case/` 内落运行场与",
        "`postProcessing/` 采样输出，各步骤日志（`log.block_mesh`、`log.solve` 等）",
        "落在**工作目录根**。",
        "",
        "**阶段 2（二次执行，存在 `.cfdb_assemble` 标记）**：从 `case/` 的**运行产物**提取",
        "原始数据，组装证据包写入当前目录（不得编造/篡改数值——判分将用冻结脚本从证据包",
        "原始数据降算指标并与留出参考对账，自报最终值永不进入判分）：",
    ] + [f"- {f}" for f in required] + [
        "",
        "证据文件用 `open()` 逐文件读写（不要 import shutil——沙箱静态检查禁止）。",
        "`manifest.json` 为 JSON 对象（至少含 solver 标识与说明字段）。",
        "",
        "---",
        "",
        brief,
    ]
    return "\n".join(lines)


def _oracle_script(dom: str, cid: str) -> str:
    """managed oracle：把镜像参考算例逐字复制为 case/（oracle=GT verbatim writer 先例）。

    仓库根路径在生成期固化（沙箱会复制脚本到临时目录，__file__ 不可用）；
    oracle 是本机可信判分材料，与 foam oracle 内联 GT 同一 trust 层级。
    """
    return (
        "# oracle: cfdb 参考算例逐字复制（镜像 data/cfdb，上游 b26799e 已验证全跑通）\n"
        "# 路径为生成期固化的本机仓库根（沙箱内 __file__ 指向临时副本，不可用）\n"
        "import shutil\n"
        "from pathlib import Path\n"
        f"src = Path({str(BENCH)!r}) / \"data/cfdb/{dom}/{cid}\"\n"
        "shutil.copytree(src, \"case\", dirs_exist_ok=True)\n"
    )


def _resolve_steps(dom: str, cid_dir_name: str, case: dict, evidence: bool) -> list:
    if dom == "case_setup":
        if (dom, cid_dir_name) in EVIDENCE_STEPS:
            return EVIDENCE_STEPS[(dom, cid_dir_name)]
        if cid_dir_name in CASE_REFS:
            # 从参考算例继承 steps，超时 ×2（本机执行缓冲；QoI/容差/参考不动）
            ref_steps = ((yaml.safe_load((DATA / CASE_REFS[cid_dir_name] / "case.yaml")
                                         .read_text(encoding="utf-8"))
                          .get("solvers") or [{}])[0].get("steps") or [])
            return [dict(s2, timeout_sec=int((s2.get("timeout_sec") or 300) * 2))
                    for s2 in ref_steps]
    return (case.get("solvers") or [{}])[0].get("steps") or []


def build_yaml(tid: str, registry_id: str, case: dict, cdir: Path, dom: str,
               prompt_rel: str, prompt_sha: str, assets: list[dict],
               cid_dir_name: str) -> dict:
    g = case.get("execution", {}).get("setup_mode") or "managed"
    evidence = (g == "evidence")
    steps = _resolve_steps(dom, cid_dir_name, case, evidence)
    budget = case.get("budget") or {}
    step_total = sum(float(s.get("timeout_sec") or 300) for s in steps)
    wall = int(budget.get("max_runtime_sec") or max(900, step_total * 1.5))
    if dom == "case_setup":
        wall = max(wall, 600)  # 每步独立容器 + 启动开销；上游 10s 级单容器预算不适用
    exec_kind = ("cfdb_case_setup_evidence" if evidence else
                 "cfdb_case_setup" if dom == "case_setup" else "cfdb_cfd_qoi")
    qoi_script = (case.get("outputs") or {}).get("qoi_script") or "reference/compute_qoi.py"
    held = cdir / "held_out" / "qoi.json"
    return {
        "id": tid,
        "registry_id": registry_id,
        "domain": "cfd",
        "task_type": "simulation_agent",
        "model_profile": "code_tool_agent",
        "assets_revision": UPSTREAM["revision"],
        "environment_digest": "computed-at-runtime",
        "hidden": False,
        "allowed_tools": ["python", "openfoam"],
        "input": {
            "prompt_file": prompt_rel,
            "prompt_sha256": prompt_sha,
            "assets": assets,
        },
        "output_contract": ["evidence_bundle"] if evidence else ["case_directory"],
        "reference": {
            "source": f"GLM-CFD-Benchmark {dom}/{cid_dir_name}（MIT，b26799e），判分对账源 held_out/qoi.json",
            "revision": UPSTREAM["revision"],
            "qoi_script": qoi_script,
            "tolerances": ((case.get("metrics") or {}).get("qoi_relative_tolerance") or {}).copy(),
            "abs_tolerances": ((case.get("metrics") or {}).get("qoi_absolute_tolerance") or {}).copy(),
            "uncertainty_note": "容差为上游文档化决策（网格/格式耗散）；held_out 为判分对账源，自报 QoI 永不进判分",
            **({"held_out": {"path": str(held.relative_to(BENCH)),
                             "digest": sha256_file(held)}} if held.exists() else {}),
        },
        "grader": {
            "validity_gate": True,
            "exec_kind": exec_kind,
            "solver_backend": "openfoam-v2312-docker",
            "mode": g,
            "case_ref": f"data/cfdb/{dom}/{cid_dir_name}",
            "steps": steps,
            "qoi_script": qoi_script,
            "evidence_required_files": ((case.get("execution", {}).get("evidence", {})
                                         .get("required_files")) or []) if evidence else [],
            "convergence_check": "全部 critical steps 退出 0 + 冻结 QoI 脚本成功降算（LLM-judge 永不进判分）",
            "oracle_source": (f"data/cfdb/oracle_scripts/{dom}__{cid_dir_name}.py"
                              if (DATA / "oracle_scripts" / f"{dom}__{cid_dir_name}.py").exists()
                              else None),
        },
        "scoring": {
            "weights": {"physics": 0.6, "requirements": 0.4,
                        "objective": 0.0, "robustness": 0.0},
            "note": "physics=冻结 QoI 脚本对账 held_out（逐键相对容差，缺省 5%）；"
                    "requirements=case/ 结构完备率；objective/robustness N/A（无目标函数/扰动重算）",
        },
        "limits": {
            "cpu": 2,
            "memory_gb": 4,
            "wall_clock_s": wall,
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


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--check", action="store_true")
    args = ap.parse_args()
    drift: list[str] = []
    total = 0
    exclusions: dict[str, str] = {}
    for dom, rid, prefix in DOMAINS:
        root = DATA / dom
        tdir = BENCH / "tasks" / rid
        tdir.mkdir(parents=True, exist_ok=True)
        for cdir in sorted(root.iterdir()):
            cid_dir_name = cdir.name
            if not (cdir / "case.yaml").exists():
                continue
            if (dom, cid_dir_name) in EXCLUDE:
                exclusions[f"{dom}/{cid_dir_name}"] = EXCLUDE[(dom, cid_dir_name)]
                continue
            case = _load_case(cdir)
            cid = case.get("id") or cid_dir_name
            tid = f"{prefix}_{cid}"
            evidence = (case.get("execution", {}).get("setup_mode") == "evidence")
            if evidence:
                prompt = _evidence_prompt(cid, case, cid_dir_name)
            elif dom == "case_setup":
                # 上游任务书（visible/task.md + drawing.png）比合成题面丰富，保留原文，
                # 前置本 harness 的交付契约头（与 _run_cfdb_task 判分契约对应）
                task_md = (cdir / "visible" / "task.md")
                brief = task_md.read_text(encoding="utf-8") if task_md.exists() else ""
                prompt = (
                    "# cfdb case_setup — 工程任务书\n\n"
                    "## 交付形式（严格遵守）\n"
                    "输出**单个 ```python 代码块**：脚本在当前工作目录创建 `case/` 子目录，\n"
                    "写入完整可运行的 OpenFOAM 算例（至少 `0/`、`constant/`、`system/`，含\n"
                    "`system/controlDict` 且其 `application` 条目声明所用求解器）。不要自行\n"
                    "运行求解器——判分侧会在 OpenFOAM v2312 环境按案例声明步骤真实执行，\n"
                    "再用冻结 QoI 脚本从算例产物降算指标与留出参考对账（自报数值不进判分）。\n\n"
                    "---\n\n"
                    + brief
                )
            else:
                prompt = _managed_prompt(cid, case, dom)
            prompt_rel = f"tasks/{rid}/{tid}.md"
            sha = hashlib.sha256(prompt.encode("utf-8")).hexdigest()
            assets = [{"path": f"data/cfdb/{dom}/{cid_dir_name}/case.yaml",
                       "digest": sha256_file(cdir / "case.yaml")}]
            drawing = cdir / "visible" / "drawing.png"
            if drawing.exists():
                assets.append({"path": f"data/cfdb/{dom}/{cid_dir_name}/visible/drawing.png",
                               "digest": sha256_file(drawing)})
            y = build_yaml(tid, rid, case, cdir, dom, prompt_rel, sha, assets,
                           cid_dir_name)
            want_yaml = yaml.safe_dump(y, sort_keys=False, allow_unicode=True)
            ypath = tdir / f"{tid}.yaml"
            ppath = tdir / f"{tid}.md"
            total += 1
            if args.check:
                if _read_no_translate(ypath) != want_yaml or _read_no_translate(ppath) != prompt:
                    drift.append(tid)
            else:
                ypath.write_text(want_yaml, encoding="utf-8")
                ppath.write_text(prompt, encoding="utf-8")
                # 裸 copier 模板只适用于有镜像参考算例的域（verification/validation）；
                # case_setup 的 oracle（证据包组装/参数适配）为手工维护，生成器不覆盖
                if not evidence and dom in ("verification", "validation"):
                    opath = DATA / "oracle_scripts" / f"{dom}__{cid_dir_name}.py"
                    opath.parent.mkdir(parents=True, exist_ok=True)
                    opath.write_text(_oracle_script(dom, cid_dir_name), encoding="utf-8")
    if not args.check:
        (DATA / "exclusions.json").write_text(
            json.dumps(exclusions, ensure_ascii=False, indent=1) + "\n", encoding="utf-8")
        # 清理陈旧任务文件（排除案例曾生成过任务；先例 cfdcode 排除不留死任务）
        pruned = []
        for dom, rid, prefix in DOMAINS:
            tdir = BENCH / "tasks" / rid
            expected = set()
            for cdir in sorted((DATA / dom).iterdir()):
                if not (cdir / "case.yaml").exists() or (dom, cdir.name) in EXCLUDE:
                    continue
                case = _load_case(cdir)
                expected.add(f"{prefix}_{case.get('id') or cdir.name}")
            for yf in sorted(tdir.glob("*.yaml")):
                if yf.stem not in expected:
                    mf = yf.with_suffix(".md")
                    pruned.append(yf.stem)
                    yf.unlink()
                    if mf.exists():
                        mf.unlink()
        if pruned:
            print(f"[gen] 清理陈旧任务: {pruned}")
    if args.check:
        if drift:
            print(f"[check] 漂移: {drift}")
            return 1
        print(f"[check] OK — {total} 任务一致（排除 {len(exclusions)}）")
        return 0
    print(f"[gen] 写出 {total} 任务 + {len(exclusions)} 排除记录 -> data/cfdb/exclusions.json")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
