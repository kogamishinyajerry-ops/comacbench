"""field_prediction.py — 流场/系数预测 adapter（五类标准 adapter 之五，YAML 驱动）。

适用（adapters/README.md §5）：superwing.coeff_lite（dev）；hilift/airfrans 后续。
判分管线（严格顺序）：
  1. validity gate：输出格式/形状合法 + 无非物理值（NaN/Inf、系数越物理包络）；
  2. physics：系数误差带评分（CL/CD/CM 相对误差 → 分档）；
  3. requirements：预测目标字段完备（缺项按 0）；
  4. objective：任务化目标（反设计/排序一致性），coeff_lite 基础题 N/A；
  5. robustness：**划分纪律**——内插/几何外推/工况外推分组独立报告；任何划分按几何构型分组。

coeff_lite 物理包络（训练集实测，进 YAML envelope）：
  cl ∈ [-0.5, 1.2]；cd ∈ [0.0, 0.2]（恒正）；cm ∈ [-0.5, 1.5]。

模型输出契约：单个 JSON 对象 {"cl":.., "cd":.., "cm":..}。

CLI（venv 非必需，纯数值判分用系统 python 即可）：
  python3 -m runners.field_prediction --tasks tasks/superwing.coeff_lite \
      --out results/superwing.coeff_lite/<date>/<provider> --provider minimax --model MiniMax-M3 --seed 0
"""

from __future__ import annotations

import argparse
import json
import time
from pathlib import Path
from typing import Any

from . import common
from .common import (FM_MISSING_OUTPUT, TaskSpec, aggregate_score,
                     build_result, environment_digest, gate_distribution,
                     load_tasks, write_run_manifest)
from .providers import ProviderError, get_answer

ADAPTER = "field_prediction"
DEFAULT_WEIGHTS = {"physics": 0.35, "requirements": 0.30,
                   "objective": 0.20, "robustness": 0.15}

_NOT_PHYSICAL = "non_physical_values"
_BAD_FORMAT = "missing_output"


def band_score(rel_err: float, tol: float) -> float:
    """误差带评分：|Δ|/|ref| ≤ tol → 1.0；≤ 2tol → 0.5；≤ 4tol → 0.25；else 0。"""
    if rel_err <= tol:
        return 1.0
    if rel_err <= 2 * tol:
        return 0.5
    if rel_err <= 4 * tol:
        return 0.25
    return 0.0


def run_task(
    task: TaskSpec, *, provider: str, model: str | None, seed: int,
    env_digest: str, prompt_cache: dict[str, str], assets_root: Path,
) -> dict[str, Any]:
    t0 = time.time()
    prompt = prompt_cache[task.id]
    g = task["grader"]
    ref = task["reference"]
    true = ref["true"]
    tols = ref["tol"]
    envelope = ref.get("envelope", {})
    coeffs = list(g["coefficients"])

    # ---- 模型输出（json expect）----
    if provider == "oracle":
        pred = dict(true)
        meta = {"provider": "oracle"}
    elif provider == "ml_superwing":
        from .providers import _ml_superwing_predict
        pred = _ml_superwing_predict(task)
        meta = {"provider": "ml_superwing",
                "model": "RandomForestRegressor(100 trees, seed=0)"}
    else:
        out = get_answer(provider, task, prompt, seed=seed, model=model,
                         max_attempts=int(task["limits"]["attempts"]), expect="json")
        pred, meta = out["answer"], out["meta"]

    applicability = {"physics": "coefficient_rel_err_band",
                     "requirements": "coeff 字段完备",
                     "objective": "N/A(coeff_lite 基础题)",
                     "robustness": f"split={ref.get('split_group', 'n/a')}"}

    # ---- gate：格式 + 物理包络 ----
    gate_failures = []
    if not isinstance(pred, dict):
        gate_failures.append(_BAD_FORMAT)
    else:
        for c in coeffs:
            v = pred.get(c)
            if not isinstance(v, (int, float)) or v != v or v in (float('inf'), float('-inf')):
                gate_failures.append(_NOT_PHYSICAL)
                break
            lo, hi = envelope.get(c, (-1e9, 1e9))
            if not (lo <= v <= hi):
                gate_failures.append(_NOT_PHYSICAL)
                break
    gate = 0 if gate_failures else 1

    # ---- physics：逐系数误差带 ----
    hits = {}
    for c in coeffs:
        if not isinstance(pred, dict) or c not in pred or not isinstance(pred.get(c), (int, float)):
            hits[c] = {"status": "missing"}
            continue
        tv = float(true[c])
        pv = float(pred[c])
        rel = abs(pv - tv) / max(abs(tv), 1e-9)
        hits[c] = {"rel_err": round(rel, 6), "pred": pv, "true": tv,
                   "band": band_score(rel, tols[c])}
    n_scored = sum(1 for v in hits.values() if "band" in v)
    physics = round(sum(v["band"] for v in hits.values() if "band" in v) / max(1, n_scored), 4) if gate else 0.0

    # ---- requirements：字段完备 ----
    req_ratio = round(sum(1 for c in coeffs if isinstance(pred, dict) and c in pred and isinstance(pred.get(c), (int, float))) / len(coeffs), 4) if gate else 0.0

    subscores = {"physics": physics, "requirements": req_ratio,
                 "objective": None, "robustness": None}
    weights = {**DEFAULT_WEIGHTS, **(task["scoring"].get("weights") or {})}
    score = aggregate_score({k: (v if v is not None else 0.0)
                             for k, v in subscores.items()}, weights, gate)

    details = {"kind": "field_prediction", "hits": hits,
               "split_group": ref.get("split_group"),
               "wing_shape_idx": ref.get("wing_shape_idx")}
    logs = [f"pred={pred if isinstance(pred, dict) else type(pred).__name__}",
            f"gate={gate} failures={gate_failures}"]
    return build_result(task=task, adapter=ADAPTER, validity_gate=gate,
        gate_failures=gate_failures, subscores=subscores, score=score,
        artifacts={"prediction": json.dumps(pred, ensure_ascii=False),
                   "model_meta": json.dumps(meta, ensure_ascii=False),
                   "grade_details": json.dumps(details, ensure_ascii=False)},
        timings={"agent_s": time.time() - t0, "setup_s": 0.0, "grade_s": 0.0},
        env_digest=env_digest, logs=logs,
        failure_mode=(gate_failures[0] if gate_failures else None),
        applicability=applicability)


def write_summary(out_dir: Path, results: list[dict[str, Any]],
                  provider: str, model_label: str, seed: int) -> Path:
    dist = gate_distribution(results)
    lines = []
    a = lines.append
    a(f"# field_prediction 结果汇总（provider={provider}, model={model_label}, seed={seed}）")
    a("")
    a("## ValidityGate 分布（先看 gate，再看子分）")
    a("")
    a(f"- 任务总数: {dist['n_tasks']}")
    a(f"- gate 通过: {dist['gate_passed']}")
    a(f"- gate 失败: {dist['gate_failed']}（直接 0 分）")
    a(f"- gate 失败原因分布: {dist['gate_failure_reasons'] or '无'}")
    a("")
    # 划分纪律：按 split_group 分组报告误差
    groups: dict[str, list[dict]] = {}
    for r in results:
        det = json.loads(r["artifacts"].get("grade_details", "{}"))
        groups.setdefault(det.get("split_group", "n/a"), []).append(r)
    a("## 划分纪律（内插 / 几何外推 分组独立报告）")
    a("")
    a("| 组 | n | gate | 物理层均值 | CL rel_err | CD rel_err | CM rel_err |")
    a("| --- | --- | --- | --- | --- | --- | --- |")
    for grp, rs in sorted(groups.items()):
        n = len(rs)
        gp = sum(1 for r in rs if r["validity_gate"] == 1)
        ph = [r["subscores"]["physics"] for r in rs if r["subscores"]["physics"] is not None]
        errs = {c: [] for c in ("cl", "cd", "cm")}
        for r in rs:
            det = json.loads(r["artifacts"].get("grade_details", "{}"))
            for c, v in det.get("hits", {}).items():
                if c in errs and "rel_err" in v:
                    errs[c].append(v["rel_err"])
        def mean(xs): return f"{sum(xs)/len(xs):.4f}" if xs else "—"
        a(f"| {grp} | {n} | {gp}/{n} | {mean(ph)} | {mean(errs['cl'])} "
          f"| {mean(errs['cd'])} | {mean(errs['cm'])} |")
    a("")
    a("## 每任务明细")
    a("")
    a("| task | gate | cl_err | cd_err | cm_err | physics | score |")
    a("| --- | --- | --- | --- | --- | --- | --- |")
    for r in results:
        det = json.loads(r["artifacts"].get("grade_details", "{}"))
        hits = det.get("hits", {})
        def e(c): return hits.get(c, {}).get("rel_err", "—")
        ph = r["subscores"]["physics"]
        a(f"| {r['task_id']} | {r['validity_gate']} | {e('cl')} | {e('cd')} "
          f"| {e('cm')} | {ph if ph is not None else '-'} | {r['score']} |")
    p = out_dir / "summary.md"
    p.write_text("\n".join(lines) + "\n", encoding="utf-8")
    return p


def main() -> int:
    ap = argparse.ArgumentParser(description="field_prediction adapter runner")
    ap.add_argument("--tasks", required=True)
    ap.add_argument("--out", required=True)
    ap.add_argument("--provider", default="stub",
                    choices=["stub", "oracle", "openai_compat", "glm", "minimax",
                             "ml_superwing"])
    ap.add_argument("--model", default=None)
    ap.add_argument("--seed", type=int, default=0)
    args = ap.parse_args()

    tasks_dir = Path(args.tasks)
    out_dir = Path(args.out)
    out_dir.mkdir(parents=True, exist_ok=True)
    tasks = load_tasks(tasks_dir)
    rids = {t["registry_id"] for t in tasks}
    if len(rids) > 1:
        raise SystemExit(f"一次运行只允许一个 registry_id: {rids}")
    registry_id = rids.pop()
    assets_root = tasks_dir.resolve().parent.parent

    asset_hashes, asset_paths = {}, []
    for t in tasks:
        for a in t.get("input", {}).get("assets", []) or []:
            p = Path(a["path"])
            if not p.is_absolute():
                p = (assets_root / p).resolve()
            common.verify_asset(p, a["digest"], f"{t.id}:{a['path']}")
            asset_hashes[a["path"]] = a["digest"]
            asset_paths.append(p)
    env_digest = environment_digest(extra_paths=asset_paths)

    prompt_cache = {}
    for t in tasks:
        pf = Path(t["input"]["prompt_file"])
        if not pf.is_absolute():
            pf = (assets_root / pf).resolve()
        with open(pf, encoding="utf-8", newline="") as f:
            prompt_cache[t.id] = f.read()

    from .providers import PROVIDER_PRESETS
    model_label = args.model or PROVIDER_PRESETS.get(args.provider, {}).get("model_default", "n/a")

    rerun = (f"cd {common.BENCH_ROOT} && python3 -m runners.field_prediction "
             f"--tasks {tasks_dir.as_posix()} --out {out_dir.as_posix()} "
             f"--provider {args.provider}"
             + (f" --model {args.model}" if args.model else "")
             + f" --seed {args.seed}")

    results, crash = [], 0
    for t in tasks:
        try:
            r = run_task(t, provider=args.provider, model=args.model, seed=args.seed,
                         env_digest=env_digest, prompt_cache=prompt_cache,
                         assets_root=assets_root)
        except ProviderError as e:
            raise SystemExit(f"[终止] provider 失败: {e}")
        except Exception as e:  # noqa: BLE001
            crash += 1
            r = build_result(task=t, adapter=ADAPTER, validity_gate=0,
                gate_failures=[common.FM_CRASH],
                subscores={"physics": None, "requirements": None, "objective": None,
                           "robustness": None}, score=0.0, artifacts={},
                timings={"agent_s": 0.0, "setup_s": 0.0, "grade_s": 0.0},
                env_digest=env_digest, logs=[f"runner exception: {e!r}"],
                failure_mode=common.FM_CRASH)
        results.append(r)
        (out_dir / f"result_{t.id}.json").write_text(
            json.dumps(r, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")

    mf = write_run_manifest(out_dir, registry_id=registry_id, adapter=ADAPTER,
                            provider=args.provider, seed=args.seed, tasks_dir=tasks_dir,
                            env_digest=env_digest, assets=asset_hashes,
                            rerun_command=rerun,
                            extra={"crash_tasks": crash, "model": model_label})
    sm = write_summary(out_dir, results, args.provider, model_label, args.seed)
    dist = gate_distribution(results)
    print(f"[done] {dist['n_tasks']} tasks | gate pass {dist['gate_passed']} "
          f"| fail {dist['gate_failed']} | voided {dist['voided']} | crash {crash}")
    print(f"       summary -> {sm}")
    print(f"       rerun: {rerun}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
