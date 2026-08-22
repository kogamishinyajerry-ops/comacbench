#!/usr/bin/env python3
"""bench_stats.py — 逐基准区分度统计（v0.2 报告口径修正，2026-08-23）。

动机：通识锚（humaneval/mbpp/gsm8k 等）对前沿模型已饱和（≥0.93），其分数
用于「校准」而非「区分模型」；汇总表若不标记，会误读为评测体系信度不足。
本工具对全部 integrated 基准输出三类证据：
  - 双模型分差 |Δ|（top-2 被测模型）——模型间区分度；
  - 任务级分数方差（最强被测模型）——基准内部难度梯度；
  - 饱和锚点标记（任一被测模型 ≥0.93）——该基准本轮不区分模型。

数据源：results/<rid>/<date>/<provider>/result_*.json（非被测 provider 不计：
oracle=判分自检、stub=地板、ml_*=ML 正例参照）。
用法：python3 bench_stats.py [--sat 0.93]
"""
from __future__ import annotations

import argparse
import json
import statistics
import sys
from pathlib import Path

BENCH = Path(__file__).resolve().parent.parent.parent
RESULTS = BENCH / "results"

SKIP_PROVIDERS = {"oracle", "stub", "ml-superwing", "ml-hilift",
                  "ml_superwing", "ml_hilift"}


def norm_provider(name: str) -> str:
    """provider 目录名归一：历史目录带模型后缀（glm-4.6）与裸名（glm）混用，
    归一为家族名（glm-4.6→glm、glm-4.6v→glmvl），同家族多轮取最新日期目录。"""
    if name.startswith("glm-4.6v"):
        return "glm-4.6v"
    if name.startswith("glm"):
        return "glm"
    if name.startswith("minimax"):
        return "minimax-m3"
    return name

# 18 integrated 基准（registry SSOT；顺序=九维报告主表）
BENCHMARKS = [
    "cfdllm.cfdquery", "aeroengqa.gold", "mechvqa.public_eval",
    "scicode.physics", "cfdllm.cfdcode", "humaneval.python",
    "humaneval.python_plus", "mbpp.sanitized", "mbpp.sanitized_plus",
    "gsm8k.math_reasoning", "math500.math_reasoning",
    "superwing.coeff_lite", "hilift_aeroml.lite", "cfdllm.foam_basic",
    "pycycle.engine_cycle", "aviary.transport_mission",
    "cadgen.local_validity", "gtm.transport_control",
]


def model_runs(rid: str) -> dict[str, tuple[str, list[float]]]:
    """该基准全部被测模型 {家族: (目录名, [score,...])}；同家族多轮取最新日期。"""
    root = RESULTS / rid
    latest: dict[str, tuple[str, list[float]]] = {}
    if not root.exists():
        return latest
    # glob 已按 日期/provider 排序 → 同家族后见覆盖前见 = 保留最新日期目录
    for prov_dir in sorted(root.glob("*/*/")):
        if prov_dir.name in SKIP_PROVIDERS:
            continue
        fs = list(prov_dir.glob("result_*.json"))
        if not fs:
            continue
        scores = []
        for f in fs:
            try:
                scores.append(json.loads(f.read_text())["score"])
            except Exception:  # noqa: BLE001
                continue
        if scores:
            latest[norm_provider(prov_dir.name)] = (prov_dir.name, scores)
    return latest


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--sat", type=float, default=0.93,
                    help="饱和阈值（任一被测模型均分 ≥ 此值记锚点）")
    args = ap.parse_args()

    rows = []
    for rid in BENCHMARKS:
        runs = model_runs(rid)
        if not runs:
            continue
        means = {fam: sum(s) / len(s) for fam, (_, s) in runs.items()}
        ranked = sorted(means.items(), key=lambda x: -x[1])
        top_fam, top_m = ranked[0]
        second_m = ranked[1][1] if len(ranked) > 1 else None
        delta = abs(top_m - second_m) if second_m is not None else None
        scores = runs[top_fam][1]
        std = statistics.pstdev(scores) if len(scores) > 1 else 0.0
        sat = top_m >= args.sat
        rows.append({
            "rid": rid, "n": len(scores),
            "top": f"{runs[top_fam][0]}={top_m:.4f}",
            "second": f"{runs[ranked[1][0]][0]}={second_m:.4f}" if second_m is not None else "—",
            "delta": delta, "std": std, "sat": sat,
        })

    print("| 基准 | n | 最强被测 | 次强 | 双家分差 | 任务方差 | 口径 |")
    print("| --- | --- | --- | --- | --- | --- | --- |")
    n_sat = 0
    for r in rows:
        tag = "⚓锚点(不区分)" if r["sat"] else ""
        if r["sat"]:
            n_sat += 1
        d = f"{r['delta']:.4f}" if r["delta"] is not None else "—"
        print(f"| {r['rid']} | {r['n']} | {r['top']} | {r['second']} "
              f"| {d} | {r['std']:.4f} | {tag} |")
    print(f"\n锚点 {n_sat}/{len(rows)}；区分带（非锚点）{len(rows)-n_sat} 个。"
          f"口径：分差=最强两被测模型均分之差；方差=最强模型任务级分数总体标准差；"
          f"锚点=任一被测模型 ≥{args.sat}（本轮校准用，不参与模型排序结论）。")
    return 0


if __name__ == "__main__":
    sys.exit(main())
