"""gen_tasks_cfdcode.py — 从镜像 CFDCodeBench 生成任务 YAML + 题面 + gold 输出锁定。

生成物（幂等，--check 校验）：
  tasks/cfdllm.cfdcode/cfdcode_<slug>.yaml   24 个任务契约
  tasks/cfdllm.cfdcode/cfdcode_<slug>.md     24 个题面（prompts.json 官方成品提示，逐字）
  data/cfdllm/cfdcode/gold_outputs/*.npy     gold 参考输出（跑 solution/ 生成，逐文件 sha256 锁定）

协议（code_exec / cfdcode_problem）：
  gate     = 脚本跑通 + 全部 save_values npy 产出 + 无 NaN/Inf
  physics  = 逐变量 mean(clamp01(Cosine), clamp01(R²))，官方插值对齐语义
  requirements = npy 交付契约
  robustness = 两次执行 npy allclose（确定性）
  objective = N/A（数据集无边界输入测试，权重 0）

用法（benchmarks/ 下）：python3 -m runners.gen_tasks_cfdcode [--check]
"""

from __future__ import annotations

import argparse
import hashlib
import json
import re
import shutil
import subprocess
import sys
import tempfile
import time
from pathlib import Path

import numpy as np
import yaml

from .common import sha256_file

BENCH = Path(__file__).resolve().parent.parent
DATA = BENCH / "data/cfdllm/cfdcode"
TASKS_DIR = BENCH / "tasks/cfdllm.cfdcode"
GOLD_OUT = DATA / "gold_outputs"
ASSETS_REVISION = "cfdcode@3b46d30+kaggle_v1"

# prompt 名 -> solution 脚本名（不齐的对显式映射；多余解文件不用）
NAME_MAP_OVERRIDES = {"2D_Poisson_Equation": "2D_Possion"}

# 2026-08-19 gold 预计算不可用任务（如实排除，原因见 PROVENANCE.md）：
#   dedalus 依赖构建失败（FFTW 系统依赖不可得）* 5；Cavity gold 在本环境不收敛（>2e6 迭代仍发散）；
#   Unsteady_Heat gold 1800s 超时；2D_Diffusion 与 Fully_Developed 为上游 prompt/gold 命名不一致。
EXCLUDED_WITH_REASON = {
    "1D_KdV_Burgers_Equation": "gold 依赖 dedalus（本机不可构建）",
    "2D_Rayleigh_Benard_Convection": "gold 依赖 dedalus",
    "2D_Shear_Flow_With_Tracer": "gold 依赖 dedalus",
    "Lane_Emden_Equation": "gold 依赖 dedalus",
    "Pipe_Flow_Disk_EVP": "gold 依赖 dedalus",
    "2D_Navier_Stokes_Cavity": "gold 在本环境压力泊松不收敛（官方 gold 缺陷）",
    "2D_Unsteady_Heat_Equation": "gold 运行 >1800s 超时",
    "2D_Diffusion": "上游不一致：prompt 要求存 p，gold 只存 u",
    "Fully_Developed_Turbulent_Channel_Flow": "上游不一致：prompt 要求存 u，gold 存 u1..u5（各湍流模型）",
}


def _slug(name: str) -> str:
    s = re.sub(r"[^A-Za-z0-9]+", "_", name).strip("_").lower()
    return re.sub(r"_+", "_", s)


def build_prompt_md(official_prompt: str) -> str:
    return official_prompt.rstrip() + "\n"


def task_yaml(pname: str, sname: str, save_values: list[str],
              prompts_digest: str, gold_digests: dict[str, str],
              prompt_sha: str) -> dict:
    tid = f"cfdcode_{_slug(pname)}"
    return {
        "id": tid,
        "registry_id": "cfdllm.cfdcode",
        "domain": "coding",
        "task_type": "code_exec",
        "model_profile": "plain_llm",
        "assets_revision": ASSETS_REVISION,
        "environment_digest": "computed-at-runtime",
        "hidden": False,
        "allowed_tools": ["python"],
        "input": {
            "prompt_file": f"tasks/cfdllm.cfdcode/{tid}.md",
            "prompt_sha256": prompt_sha,
            "assets": (
                [{"path": "data/cfdllm/cfdcode/prompt/PDE_TASK_QUESTION_ONLY.json",
                  "digest": prompts_digest}]
                + [{"path": f"data/cfdllm/cfdcode/gold_outputs/{v}_{sname}.npy",
                    "digest": d} for v, d in gold_digests.items()]
            ),
        },
        "output_contract": [f"{v}.npy" for v in save_values],
        "reference": {
            "source": "CFDCodeBench gold solution 预计算输出（本 harness 离线锁定）",
            "revision": ASSETS_REVISION,
            "solution_script": f"solution/{sname}.py",
            "metrics": ["MSE", "MAE", "RMSE", "Cosine", "R2", "NMSE"],
            "uncertainty_note": "参考场为单一确定性数值解，无比对不确定度；"
                                "形状不一致时按官方 scipy.zoom 一阶插值对齐",
        },
        "grader": {
            "answer_format": "code",
            "exec_kind": "cfdcode_problem",
            "validity_gate": True,
            "save_values": save_values,
            "gold_dir": "data/cfdllm/cfdcode/gold_outputs",
            "gold_prefix": sname,
            "field_compare": "official_interpolate+cos_r2",
            "stability_layer": False,
            "determinism_runs": 2,
            "sandbox": {"banned": "network/process/ctypes/sys.path", "isolated_interpreter": True},
            "oracle_source": f"data/cfdllm/cfdcode/solution/{sname}.py",
        },
        "scoring": {
            "weights": {"physics": 0.5, "requirements": 0.2, "objective": 0.0,
                        "robustness": 0.3},
            "note": "objective=N/A（数据集无边界输入测试）权重 0；robustness=两次执行确定性",
        },
        "limits": {"cpu": 4, "memory_gb": 8, "wall_clock_s": 600, "attempts": 3},
        "license_provenance": {
            "source": "NREL-Theseus/cfdllmbench + Kaggle nithinsekhar/cfdcodebench",
            "license": "BSD-3-Clause",
            "status": "confirmed-repo",
            "revision": ASSETS_REVISION,
            "mirror_allowed": True,
        },
    }


def _read_no_translate(p: Path) -> str:
    if not p.exists():
        return ""
    with open(p, encoding="utf-8", newline="") as f:
        return f.read()


def precompute_gold(prompts: dict, name_map: dict[str, str],
                    force: bool) -> dict[str, dict[str, str]]:
    """gold npys 已由离线预计算落 gold_outputs/（运行记录见 PROVENANCE.md）。

    此处只做：存在性校验 + sha256 摘要；缺失任务（EXCLUDED_WITH_REASON）返回空 dict。
    """
    digests_file = DATA / "gold_outputs_digests.json"
    if digests_file.exists() and not force:
        return json.loads(digests_file.read_text())
    GOLD_OUT.mkdir(parents=True, exist_ok=True)
    digests: dict[str, dict[str, str]] = {}
    for pname, sname in sorted(name_map.items()):
        if pname in EXCLUDED_WITH_REASON:
            continue
        save_values = list(prompts[pname]["save values"])
        d = {v: sha256_file(GOLD_OUT / f"{v}_{sname}.npy") for v in save_values
             if (GOLD_OUT / f"{v}_{sname}.npy").exists()}
        digests[pname] = d
    digests_file.write_text(json.dumps(digests, indent=1))
    return digests


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--check", action="store_true")
    ap.add_argument("--force-gold", action="store_true")
    args = ap.parse_args()

    prompts = json.loads((DATA / "prompt/PDE_TASK_QUESTION_ONLY.json").read_text())
    official = json.loads((DATA / "prompt/prompts.json").read_text())["prompts"]
    prompts_digest = sha256_file(DATA / "prompt/PDE_TASK_QUESTION_ONLY.json")
    name_map = {n: NAME_MAP_OVERRIDES.get(n, n) for n in prompts}
    digests = precompute_gold(prompts, name_map, args.force_gold)

    TASKS_DIR.mkdir(parents=True, exist_ok=True)
    drift, n = [], 0
    for pname in sorted(prompts):
        if pname in EXCLUDED_WITH_REASON:
            continue
        sname = name_map[pname]
        save_values = list(prompts[pname]["save values"])
        gold_digests = digests.get(pname, {})
        if len(gold_digests) != len(save_values):
            print(f"[skip] {pname}: gold 不全（{len(gold_digests)}/{len(save_values)}）")
            continue
        prompt_md = build_prompt_md(official[pname])
        prompt_sha = hashlib.sha256(prompt_md.encode()).hexdigest()
        want = yaml.safe_dump(task_yaml(pname, sname, save_values, prompts_digest,
                                        gold_digests, prompt_sha),
                              sort_keys=False, allow_unicode=True)
        tid = f"cfdcode_{_slug(pname)}"
        ypath, ppath = TASKS_DIR / f"{tid}.yaml", TASKS_DIR / f"{tid}.md"
        if args.check:
            if _read_no_translate(ypath) != want or _read_no_translate(ppath) != prompt_md:
                drift.append(tid)
        else:
            ypath.write_text(want, encoding="utf-8")
            ppath.write_text(prompt_md, encoding="utf-8")
        n += 1
    if args.check:
        if drift:
            print(f"[check] 不一致: {drift}")
            return 1
        print(f"[check] {n} 个任务与镜像一致")
        return 0
    print(f"[gen] {n} tasks -> {TASKS_DIR} | gold_outputs: {len(list(GOLD_OUT.glob('*.npy')))} npy")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
