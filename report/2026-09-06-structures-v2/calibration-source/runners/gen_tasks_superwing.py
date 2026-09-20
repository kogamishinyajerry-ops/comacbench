"""gen_tasks_superwing.py — 从镜像 SuperWing 系数层生成 field_prediction 任务。

产出（幂等，--check 校验）：
  tasks/superwing.coeff_lite/superwing_{ge|it}_####.yaml + .md
  几何外推组（ge）= test.parquet（424 未训练构型）；内插组（it）= train.parquet（已见构型）。

任务契约（field_prediction / json 输出）：
  输入 = 翼型几何参数（configs.dat 前 38 参数）+ 工况 (aoa, mach)；
  目标 = cl_solver / cd_solver / cm_solver（RANS 求解器系数）；
  划分纪律：test 构型与 train 构型零交集（几何外推），分组独立报告；
  物理包络（训练集实测）：cl∈[-0.5,1.2] cd∈[0,0.2] cm∈[-0.5,1.5]。

用法：python3 -m runners.gen_tasks_superwing [--check] [--n_ge 70] [--n_it 30]
"""

from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path

import numpy as np
import pandas as pd
import yaml

from .common import sha256_file

BENCH = Path(__file__).resolve().parent.parent
DATA = BENCH / "data/superwing/coeff_lite"
TASKS_DIR = BENCH / "tasks/superwing.coeff_lite"
ASSETS_REVISION = "superwing@hf-coeff-lite-2026-08-19"

# configs.dat 前 38 个几何参数名（col1..col38）
GEO_PARAMS = ["SA", "DA", "DA_kink", "AR", "TR", "kink", "rootadj",
              "rtcs_0", "rtcs_1", "rtcs_2",
              "cambers_0", "cambers_1", "cambers_2",
              "twists_0", "twists_1", "twists_2", "twists_3",
              "Uroot_0", "Uroot_1", "Uroot_2", "Uroot_3", "Uroot_4",
              "Uroot_5", "Uroot_6", "Uroot_7", "Uroot_8", "Uroot_9",
              "Utip_0", "Utip_1", "Utip_2", "Utip_3", "Utip_4",
              "Utip_5", "Utip_6", "Utip_7", "Utip_8", "Utip_9", "tcroot"]

ENVELOPE = {"cl": [-0.5, 1.2], "cd": [0.0, 0.2], "cm": [-0.5, 1.5]}
TOLS = {"cl": 0.05, "cd": 0.10, "cm": 0.05}
COEFFS = ["cl", "cd", "cm"]
_WEIGHTS = {"physics": 0.6, "requirements": 0.4, "objective": 0.0, "robustness": 0.0}


def _load_configs() -> dict[int, dict[str, float]]:
    raw = open(DATA / "configs.dat").read().splitlines()
    lines = [l for l in raw if l and not l.startswith(("VARIABLES", "ZONE", "TITLE"))]
    shapes = {}
    for l in lines:
        vals = l.split()
        sidx = int(float(vals[0]))
        params = {GEO_PARAMS[i]: float(vals[i + 1]) for i in range(38)}
        shapes[sidx] = params
    return shapes


def build_prompt(geo: dict[str, float], aoa: float, mach: float) -> str:
    geo_lines = "\n".join(f"- {k}: {v:.6g}" for k, v in geo.items())
    return (
        "You are given the parametric geometry of a transonic kinked wing and a single "
        "operating condition, and must predict its aerodynamic coefficients.\n\n"
        "## Wing geometry parameters\n"
        f"{geo_lines}\n\n"
        f"## Operating condition\n- angle of attack (aoa, deg): {aoa:.6g}\n"
        f"- Mach number: {mach:.6g}\n\n"
        "The wing was simulated with a RANS solver (ADflow). Estimate the integrated "
        "aerodynamic coefficients.\n\n"
        "Respond with a single JSON object of the form "
        '{"cl": <lift coefficient>, "cd": <drag coefficient>, "cm": <pitching moment coefficient>} '
        "and nothing else. Values must be finite numbers within physical ranges "
        "(cl in [-0.5, 1.2], cd in [0, 0.2], cm in [-0.5, 1.5])."
    ) + "\n"


def task_yaml(tid: str, split_group: str, shape_idx: int, aoa: float, mach: float,
              true: dict, digests: dict[str, str], prompt_sha: str) -> dict:
    return {
        "id": tid,
        "registry_id": "superwing.coeff_lite",
        "domain": "cfd",
        "task_type": "field_prediction",
        "model_profile": "plain_llm",
        "assets_revision": ASSETS_REVISION,
        "environment_digest": "computed-at-runtime",
        "hidden": False,
        "allowed_tools": [],
        "input": {
            "prompt_file": f"tasks/superwing.coeff_lite/{tid}.md",
            "prompt_sha256": prompt_sha,
            "assets": [{"path": p, "digest": d} for p, d in digests.items()],
        },
        "output_contract": ["prediction"],
        "reference": {
            "source": "SuperWing 系数层（configs.dat + index.npy/parquet，RANS ADflow 真值）",
            "revision": ASSETS_REVISION,
            "wing_shape_idx": shape_idx,
            "aoa": aoa,
            "mach": mach,
            "true": true,
            "tol": TOLS,
            "envelope": ENVELOPE,
            "split_group": split_group,
            "uncertainty_note": "确定性 RANS 单次求解；系数真值无不确定度带（误差带评分用相对容差）",
        },
        "grader": {
            "answer_format": "json",
            "exec_kind": "field_prediction",
            "validity_gate": True,
            "coefficients": COEFFS,
            "band_tol": TOLS,
            "envelope": ENVELOPE,
        },
        "scoring": {
            "weights": _WEIGHTS,
            "note": "physics=系数相对误差带（cl/cm 5%/cd 10%）；requirements=字段完备；"
                    "objective=N/A；robustness=划分纪律（聚合层分组报告，不计逐任务分）",
        },
        "limits": {"cpu": 1, "memory_gb": 2, "wall_clock_s": 300, "attempts": 3},
        "license_provenance": {
            "source": "HuggingFace yunplus/SuperWing（系数层子集）",
            "license": "CC BY-SA 4.0",
            "status": "confirmed-dataset",
            "revision": ASSETS_REVISION,
            "mirror_allowed": True,
            "note": "SA 传染性：派生评测子集按同许可发布策略（scoring §8）；仅系数层不触体数据",
        },
    }


def _read_no_translate(p: Path) -> str:
    if not p.exists():
        return ""
    with open(p, encoding="utf-8", newline="") as f:
        return f.read()


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--check", action="store_true")
    ap.add_argument("--n_ge", type=int, default=70)
    ap.add_argument("--n_it", type=int, default=30)
    args = ap.parse_args()

    shapes = _load_configs()
    tr = pd.read_parquet(DATA / "train.parquet")
    te = pd.read_parquet(DATA / "test.parquet")
    digests = {}
    for f in ("configs.dat", "index.npy", "train.parquet", "test.parquet"):
        digests[f"data/superwing/coeff_lite/{f}"] = sha256_file(DATA / f)

    TASKS_DIR.mkdir(parents=True, exist_ok=True)

    # 采样（固定种子，几何外推优先形状多样性）
    rng = np.random.default_rng(20260819)
    ge = te.sample(n=min(args.n_ge, len(te)), random_state=42)
    it = tr.sample(n=min(args.n_it, len(tr)), random_state=43)

    jobs = []
    for grp, df in (("ge", ge), ("it", it)):
        for i, (_, row) in enumerate(df.iterrows(), 1):
            tid = f"superwing_{grp}_{i:04d}"
            sidx = int(row['wing_shape_idx'])
            aoa, mach = float(row['aoa']), float(row['mach'])
            true = {"cl": float(row['cl_solver']), "cd": float(row['cd_solver']),
                    "cm": float(row['cm_solver'])}
            jobs.append((tid, grp, sidx, aoa, mach, true))

    drift = []
    for tid, grp, sidx, aoa, mach, true in jobs:
        geo = shapes[sidx]
        prompt = build_prompt(geo, aoa, mach)
        prompt_sha = hashlib.sha256(prompt.encode()).hexdigest()
        want = yaml.safe_dump(task_yaml(tid, grp, sidx, aoa, mach, true, digests, prompt_sha),
                              sort_keys=False, allow_unicode=True)
        yp = TASKS_DIR / f"{tid}.yaml"
        pp = TASKS_DIR / f"{tid}.md"
        if args.check:
            if _read_no_translate(yp) != want or _read_no_translate(pp) != prompt:
                drift.append(tid)
        else:
            yp.write_text(want, encoding="utf-8")
            pp.write_text(prompt, encoding="utf-8")
    if args.check:
        if drift:
            print(f"[check] 不一致: {drift}")
            return 1
        print(f"[check] {len(jobs)} 个任务与镜像一致 (ge {args.n_ge} / it {args.n_it})")
        return 0
    print(f"[gen] {len(jobs)} tasks -> {TASKS_DIR} (ge {len(ge)} / it {len(it)})")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
