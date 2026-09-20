"""gen_tasks_hilift.py — 从镜像 HiLiftAeroML-Lite 生成 field_prediction 任务。

产出（幂等，--check 校验）：
  tasks/hilift_aeroml.lite/hilift_{ge|it}_####.yaml + .md

任务契约：与 superwing.coeff_lite 同款 field_prediction / json 输出。
- 输入 = 8 个高升力几何参数（缝翼/襟翼偏度 + 缝道乘子）+ AoA；
- 目标 = cl / cd / cm（WMLES 真值）；
- 划分纪律：180 构型按几何分组——内插（训练构型的保留迎角）vs 几何外推（保留构型全部迎角）；
- 物理包络（全量实测）：cl∈[0.5,4.5]、cd∈[0.10,0.55]、cm∈[-1.6,-0.05]。

用法：python3 -m runners.gen_tasks_hilift [--check] [--n_ge 70] [--n_it 30]
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
DATA = BENCH / "data/hilift/lite"
TASKS_DIR = BENCH / "tasks/hilift_aeroml.lite"
ASSETS_REVISION = "hilift@hf-lite-2026-08-19"

GEO_PARAMS = ["IB_Flap_Deflection", "OB_Flap_Deflection",
              "IB_Flap_Gap_Multiplier", "OB_Flap_Gap_Multiplier",
              "IB_Slat_Deflection", "OB_Slat_Deflection",
              "IB_Slat_Gap_Multiplier", "OB_Slat_Gap_Multiplier"]

ENVELOPE = {"cl": [0.0, 5.0], "cd": [0.05, 0.8], "cm": [-2.0, 0.5]}
TOLS = {"cl": 0.05, "cd": 0.10, "cm": 0.05}
COEFFS = ["cl", "cd", "cm"]
_WEIGHTS = {"physics": 0.6, "requirements": 0.4, "objective": 0.0, "robustness": 0.0}


def build_prompt(geo: dict[str, float], aoa: float) -> str:
    geo_lines = "\n".join(f"- {k}: {v:.6g}" for k, v in geo.items())
    return (
        "You are given the high-lift geometry parameters of a NASA CRM-HL aircraft "
        "(CRM with slats and flaps deployed) and an angle of attack, and must predict "
        "its aerodynamic force/moment coefficients.\n\n"
        "## High-lift geometry parameters\n"
        f"{geo_lines}\n\n"
        f"## Operating condition\n- angle of attack (deg): {aoa:g}\n\n"
        "The flow was simulated with wall-modeled LES (Fidelity Charles, 300-500M cell "
        "adaptive grids). Estimate the integrated coefficients.\n\n"
        "Respond with a single JSON object of the form "
        '{"cl": <lift coefficient>, "cd": <drag coefficient>, "cm": <pitching moment coefficient>} '
        "and nothing else. Values must be finite numbers within physical ranges "
        "(cl in [0, 5], cd in [0.05, 0.8], cm in [-2, 0.5])."
    ) + "\n"


def task_yaml(tid: str, split_group: str, geo_id: str, aoa: float,
              true: dict, digests: dict[str, str], prompt_sha: str) -> dict:
    return {
        "id": tid,
        "registry_id": "hilift_aeroml.lite",
        "domain": "cfd",
        "task_type": "field_prediction",
        "model_profile": "plain_llm",
        "assets_revision": ASSETS_REVISION,
        "environment_digest": "computed-at-runtime",
        "hidden": False,
        "allowed_tools": [],
        "input": {
            "prompt_file": f"tasks/hilift_aeroml.lite/{tid}.md",
            "prompt_sha256": prompt_sha,
            "assets": [{"path": p, "digest": d} for p, d in digests.items()],
        },
        "output_contract": ["prediction"],
        "reference": {
            "source": "HiLiftAeroML-Lite 系数层（WMLES 真值，force_mom_all.csv）",
            "revision": ASSETS_REVISION,
            "wing_shape_idx": geo_id,
            "aoa": aoa,
            "mach": None,
            "true": true,
            "tol": TOLS,
            "envelope": ENVELOPE,
            "split_group": split_group,
            "uncertainty_note": "WMLES 带统计不确定度（csv 含 stdev/ci95）；首批用点值+相对容差",
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
                    "objective=N/A；robustness=划分纪律（聚合层分组报告）",
        },
        "limits": {"cpu": 1, "memory_gb": 2, "wall_clock_s": 300, "attempts": 3},
        "license_provenance": {
            "source": "HuggingFace nvidia/HiLiftAeroML（Lite 系数层子集）",
            "license": "CC BY 4.0",
            "status": "confirmed-dataset",
            "revision": ASSETS_REVISION,
            "mirror_allowed": True,
            "attribution": "Neil Ashton (contact@caemldatasets.org)",
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

    fm = pd.read_csv(DATA / "force_mom_all.csv")
    geo = pd.read_csv(DATA / "geo_values_all.csv").set_index("GeoID")
    digests = {}
    for f in ("force_mom_all.csv", "geo_values_all.csv"):
        digests[f"data/hilift/lite/{f}"] = sha256_file(DATA / f)

    TASKS_DIR.mkdir(parents=True, exist_ok=True)
    rng = np.random.default_rng(20260819)

    # 划分：36 个构型保留为几何外推（20%），其余 144 为训练构型
    all_geos = sorted(fm["GeoID"].unique())
    holdout = set(rng.choice(all_geos, size=36, replace=False).tolist())
    # 内插 = 训练构型中抽样（每构型取 1-2 个迎角）；几何外推 = 保留构型全迎角中抽样
    ge_df = fm[fm["GeoID"].isin(holdout)].sample(n=args.n_ge, random_state=42)
    it_df = fm[~fm["GeoID"].isin(holdout)].sample(n=args.n_it, random_state=43)

    jobs = []
    for grp, df in (("ge", ge_df), ("it", it_df)):
        for i, (_, row) in enumerate(df.iterrows(), 1):
            tid = f"hilift_{grp}_{i:04d}"
            g = geo.loc[row["GeoID"]]
            jobs.append((tid, grp, row["GeoID"], float(row["AoA"]),
                         {"cl": float(row["cl"]), "cd": float(row["cd"]),
                          "cm": float(row["cm"])},
                         {k: float(g[k]) for k in GEO_PARAMS}))

    drift = []
    for tid, grp, gid, aoa, true, gp in jobs:
        prompt = build_prompt(gp, aoa)
        prompt_sha = hashlib.sha256(prompt.encode()).hexdigest()
        want = yaml.safe_dump(task_yaml(tid, grp, gid, aoa, true, digests, prompt_sha),
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
    print(f"[gen] {len(jobs)} tasks -> {TASKS_DIR} (ge {args.n_ge} / it {args.n_it})")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
