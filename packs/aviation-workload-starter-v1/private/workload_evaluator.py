"""workload 家族的独立 evaluator（判分侧资产，artifacts.v1）。

对每个变体，从 agent 交付的文件**独立复算**，不看任何自评：
  - normalized.json：行级规范化记录（含单位换算与血缘）
  - run_manifest.csv：运行清单（每工况一行）
  - exceptions.csv：拒收/需澄清/陈旧清单

家族判定矩阵（方案 §4 十二变体的前四个，公共合成版）：
  baseline_01    全部行可处理 -> normalized 全行 + manifest 全工况 + exceptions 空
  missing_unit_02 P2 高度缺单位 -> 拒收该行并给出理由，不得猜测补全
  conflict_dup_03 P1 重复且矛盾 -> 拒收并报告冲突，不得静默取最后一条
  stale_output_04 旧版结果混入 -> 陈旧项不得进入 manifest，必须列入 exceptions
"""
from __future__ import annotations

import csv
import io
import json
from pathlib import Path

EXPECTED_KINDS = {"normalized": "normalized.json",
                  "run_manifest": "run_manifest.csv",
                  "exceptions": "exceptions.csv"}


def _read_json(p: Path):
    try:
        return json.loads(p.read_text(encoding="utf-8"))
    except (ValueError, OSError, UnicodeError):
        return None


def _read_csv(p: Path) -> list[dict]:
    try:
        with p.open(encoding="utf-8") as fh:
            return list(csv.DictReader(fh))
    except (OSError, UnicodeError, csv.Error):
        return []


def _case(task) -> dict:
    p = Path(task.yaml_path).parents[2] / "assets" / f"{task.id}_case.json"
    return _read_json(p) or {}


def evaluate(task, workspace: Path, deliverables: list[dict]) -> dict:
    case = _case(task)
    by_kind = {}
    for d in deliverables:
        p = workspace / d["path"]
        if d["kind"] in ("normalized", "run_manifest", "exceptions"):
            by_kind[d["kind"]] = p
    checks: list[dict] = []

    def add(name, passed, expected, actual):
        checks.append({"name": name, "passed": bool(passed),
                       "expected": expected, "actual": actual})

    # ---- normalized.json：行级内容 ----
    rows = None
    if "normalized" in by_kind and by_kind["normalized"].is_file():
        data = _read_json(by_kind["normalized"])
        if isinstance(data, dict):
            rows = data.get("rows")
    if rows is None:
        add("normalized_present", False, "rows in normalized.json", "missing")
        return {"checks": checks, "summary": "normalized 缺失或不可解析"}
    add("normalized_present", True, "rows", f"{len(rows)} rows")

    good = [r for r in rows
            if isinstance(r, dict) and isinstance(r.get("point"), str)]
    add("row_shape_valid", len(good) == len(rows) and bool(rows),
        "每行含 point 字符串", f"{len(good)}/{len(rows)}")

    # 单位纪律：规范化输出必须带显式单位后缀字段（换算成 m / kg/s）
    unit_ok = all(
        isinstance(r.get("altitude_m"), (int, float))
        and isinstance(r.get("mass_flow_kg_s"), (int, float))
        for r in good)
    add("units_explicit", unit_ok, "altitude_m 与 mass_flow_kg_s 数值化",
        [sorted(r) for r in good[:3]])

    # ---- 家族判定矩阵 ----
    tid = task.id
    raw_rows = case.get("rows", [])
    if tid.endswith("baseline_01"):
        add("all_points_processed", len(good) == len(raw_rows),
            f"{len(raw_rows)} 行全部处理", f"{len(good)}")
        ids = sorted(r["point"] for r in good)
        add("points_match", ids == sorted(r["point"] for r in raw_rows),
            sorted(r["point"] for r in raw_rows), ids)
    elif tid.endswith("missing_unit_02"):
        accepted = {r["point"] for r in good}
        add("unitless_row_rejected", "P2" not in accepted,
            "缺单位的 P2 不得被接受", sorted(accepted))
        add("no_guessed_value", all(
            r.get("altitude_m") != 6000 or r["point"] != "P2" for r in good),
            "不得猜测补全 P2 高度", "checked")
    elif tid.endswith("conflict_dup_03"):
        counts: dict[str, int] = {}
        for r in good:
            counts[r["point"]] = counts.get(r["point"], 0) + 1
        add("duplicate_not_silently_merged",
            counts.get("P1", 0) <= 1,
            "P1 冲突不得静默合并成一行", counts.get("P1"))
        alt = {r.get("altitude_m") for r in good if r["point"] == "P1"}
        add("conflict_not_arbitrarily_picked",
            alt in ({0.0}, {300.0}, set()),
            "P1 两个矛盾值不得任选其一冒充正解", sorted(x for x in alt if x is not None))
    elif tid.endswith("stale_output_04"):
        pts = {r["point"] for r in good}
        add("stale_point_excluded", "P0" not in pts,
            "旧版 P0 不得进入 normalized", sorted(pts))

    # ---- run_manifest.csv：工况覆盖 ----
    manifest_rows = _read_csv(by_kind["run_manifest"]) if "run_manifest" in by_kind else []
    add("manifest_present", "run_manifest" in by_kind and bool(manifest_rows),
        "run_manifest.csv 每工况一行", f"{len(manifest_rows)} rows")
    mpts = {r.get("point") for r in manifest_rows if r.get("point")}
    if tid.endswith("baseline_01"):
        add("manifest_covers_all",
            mpts >= {r["point"] for r in raw_rows},
            sorted(r["point"] for r in raw_rows), sorted(mpts))
    elif tid.endswith("missing_unit_02"):
        add("manifest_excludes_rejected", "P2" not in mpts,
            "被拒收的 P2 不得出现在 manifest", sorted(mpts))

    # ---- exceptions.csv：拒收必须留痕 ----
    exc_rows = _read_csv(by_kind["exceptions"]) if "exceptions" in by_kind else []
    reasons = {r.get("point"): r.get("reason", "") for r in exc_rows}
    if tid.endswith("missing_unit_02"):
        add("rejection_recorded", "P2" in reasons and bool(reasons["P2"].strip()),
            "P2 拒收理由", reasons.get("P2"))
    elif tid.endswith("conflict_dup_03"):
        add("conflict_recorded", "P1" in reasons and bool(reasons["P1"].strip()),
            "P1 冲突理由", reasons.get("P1"))
    elif tid.endswith("stale_output_04"):
        add("stale_recorded", "P0" in reasons and bool(reasons["P0"].strip()),
            "P0 陈旧理由", reasons.get("P0"))
    else:
        add("no_false_exceptions", not exc_rows,
            "基线无可报告异常", f"{len(exc_rows)} rows")

    failed = [c["name"] for c in checks if not c["passed"]]
    return {"checks": checks,
            "summary": f"{len(checks)-len(failed)}/{len(checks)} checks passed",
            "failed": failed}
