"""workload 家族的独立 evaluator（判分侧资产，artifacts.v2）。

对每个变体，从冻结规则与 case 输入**独立推导期望**，再与 agent 交付对账：
  - normalized.json：行级规范化记录（含单位与血缘）
  - run_manifest.csv：运行清单（每个被接受工况一行）
  - exceptions.csv：拒收/需澄清/陈旧清单

推导规则（与 private/workload_oracle.py 的冻结行为一致）：
  - 输入行按序处理；altitude 缺明示单位（有 altitude 无 altitude_m）→ 拒收 missing_unit
  - point 重复出现（无论两条数值是否一致）→ 冲突，两条全部拒收（先接受的行也要撤回）
  - stale_results 中的 point → 陈旧拒收，不得进入 normalized/manifest
  - 其余行合法：期望值直接取输入行的 altitude_m / mass_flow_kg_s，血缘取 case 的
    case_id / version

对账要求：按 point 主键的精确多重集合（不漏、不多、不重），数值逐行与输入精确
比对（排除 bool/NaN/Inf），manifest 三元组 (point, case_id, version) 精确集合相等，
exceptions 逐 point 对账且理由必须与问题类别匹配。比较全部基于内容，不依赖列序/
行序/字节表示。
"""
from __future__ import annotations

import csv
import io
import json
import math
from collections import Counter
from pathlib import Path

REQUIRED_KINDS = ("normalized", "run_manifest", "exceptions")
MANIFEST_COLUMNS = ("point", "case_id", "version")
EXCEPTION_COLUMNS = ("point", "reason", "detail")
ROW_FIELDS = ("point", "altitude_m", "mass_flow_kg_s", "source_version")
REASON_KEYWORDS = {
    "missing_unit": ("unit", "单位"),
    "conflict": ("conflict", "冲突", "矛盾"),
    "stale": ("stale", "陈旧", "旧版"),
}


def _read_json(p: Path):
    try:
        return json.loads(p.read_text(encoding="utf-8"))
    except (ValueError, OSError, UnicodeError):
        return None


def _read_csv_strict(p: Path):
    """返回 (header, rows)；不可读或不可解析返回 (None, None)。空表返回 (header, [])。"""
    try:
        text = p.read_text(encoding="utf-8")
    except (OSError, UnicodeError):
        return None, None
    try:
        parsed = list(csv.reader(io.StringIO(text)))
    except csv.Error:
        return None, None
    if not parsed:
        return [], []
    header = parsed[0]
    rows = list(csv.DictReader(io.StringIO(text)))
    return header, rows


def _case(task) -> dict:
    p = Path(task.yaml_path).parents[2] / "assets" / f"{task.id}_case.json"
    data = _read_json(p)
    return data if isinstance(data, dict) else {}


def _is_number(x) -> bool:
    return (type(x) in (int, float) and not isinstance(x, bool)
            and math.isfinite(x))


def _derive_expected(case: dict):
    """从冻结规则与输入推导期望：合法行集合与拒收清单。"""
    accepted: list[dict] = []
    rejected: list[dict] = []
    seen: set = set()
    rows = case.get("rows")
    if not isinstance(rows, list):
        rows = []
    for r in rows:
        if not isinstance(r, dict):
            continue
        pt = r.get("point")
        if "altitude_m" not in r and "altitude" in r:
            rejected.append({"point": pt, "category": "missing_unit"})
            continue
        if pt in seen:
            rejected.append({"point": pt, "category": "conflict"})
            accepted = [x for x in accepted if x["point"] != pt]
            continue
        seen.add(pt)
        accepted.append({
            "point": pt,
            "altitude_m": r.get("altitude_m"),
            "mass_flow_kg_s": r.get("mass_flow_kg_s"),
            "source_version": case.get("version"),
            "case_id": case.get("case_id"),
        })
    stale = case.get("stale_results")
    if isinstance(stale, list):
        for s in stale:
            if isinstance(s, dict):
                rejected.append({"point": s.get("point"), "category": "stale"})
    return accepted, rejected


def evaluate(task, workspace: Path, deliverables) -> dict:
    case = _case(task)
    exp_rows, exp_exc = _derive_expected(case)
    exp_by_point = {r["point"]: r for r in exp_rows}
    exp_points = Counter(str(r["point"]) for r in exp_rows)
    exp_triples = sorted(
        (str(r["point"]), str(r["case_id"]), str(r["source_version"]))
        for r in exp_rows)
    exp_exc_points = Counter(str(e["point"]) for e in exp_exc)
    exp_exc_cat = {str(e["point"]): e["category"] for e in exp_exc}

    checks: list[dict] = []

    def add(name, passed, expected, actual):
        checks.append({"name": name, "passed": bool(passed),
                       "expected": expected, "actual": actual})

    # ---- deliverable 声明：三个必要 kind 各恰好一次 ----
    declared: Counter = Counter()
    by_kind: dict = {}
    if isinstance(deliverables, list):
        for d in deliverables:
            if (isinstance(d, dict) and isinstance(d.get("kind"), str)
                    and isinstance(d.get("path"), str)
                    and d["kind"] in REQUIRED_KINDS):
                declared[d["kind"]] += 1
                by_kind.setdefault(d["kind"], workspace / d["path"])
    add("deliverable_kinds_declared",
        all(declared[k] == 1 for k in REQUIRED_KINDS),
        "normalized/run_manifest/exceptions 各声明恰好一次",
        {k: declared.get(k, 0) for k in REQUIRED_KINDS})

    # ---- normalized.json：结构防御 ----
    data = None
    if "normalized" in by_kind and by_kind["normalized"].is_file():
        data = _read_json(by_kind["normalized"])
    if not isinstance(data, dict):
        add("normalized_present", False, "normalized.json 为可解析的 JSON 对象",
            "文件缺失或不可解析" if data is None
            else f"顶层类型 {type(data).__name__}")
        data = None
    else:
        add("normalized_present", True, "JSON 对象", "ok")

    rows = data.get("rows") if data is not None else None
    safe_rows: list = []
    if not isinstance(rows, list):
        add("normalized_structure", False,
            "rows 为列表，每行是含 point 字符串字段的对象",
            f"rows 缺失或类型为 {type(rows).__name__}")
    else:
        bad = [f"第{i}行非对象或缺 point 字符串"
               for i, r in enumerate(rows)
               if not (isinstance(r, dict) and isinstance(r.get("point"), str))]
        add("normalized_structure", not bad,
            "rows 为列表，每行是含 point 字符串字段的对象", bad or "ok")
        safe_rows = [r for r in rows
                     if isinstance(r, dict) and isinstance(r.get("point"), str)]

    # ---- 行形状与数值语义 ----
    bad_shape = []
    for r in safe_rows:
        missing = [f for f in ROW_FIELDS if f not in r]
        if missing:
            bad_shape.append([r.get("point"), missing])
    add("row_shape_valid", not bad_shape,
        "每行字段齐全: point/altitude_m/mass_flow_kg_s/source_version",
        bad_shape[:5] or "ok")

    bad_units = []
    for r in safe_rows:
        for f in ("altitude_m", "mass_flow_kg_s"):
            v = r.get(f)
            if not _is_number(v):
                bad_units.append([r.get("point"), f, repr(v)])
    add("units_explicit", not bad_units,
        "altitude_m 与 mass_flow_kg_s 为有限数值（排除 bool/NaN/Inf）",
        bad_units[:5] or "ok")

    # ---- 多重集合对账（按 point 主键） ----
    act_points = Counter(str(r["point"]) for r in safe_rows)
    if act_points == exp_points:
        add("rows_reconciled", True,
            f"合法 point 恰好各出现一次: {sorted(exp_points)}", "ok")
    else:
        missing = sorted(p for p, c in exp_points.items()
                         if act_points.get(p, 0) < c)
        surplus = sorted(p for p, c in act_points.items()
                         if exp_points.get(p, 0) < c)
        add("rows_reconciled", False,
            f"合法 point 恰好各出现一次: {sorted(exp_points)}",
            f"缺失 {missing} 多余/重复 {surplus} 实际计数 {dict(act_points)}")

    mismatches = []
    for r in safe_rows:
        pt = r["point"]
        e = exp_by_point.get(pt)
        if e is None:
            continue  # 非法 point 已由 rows_reconciled 判定
        for f in ("altitude_m", "mass_flow_kg_s"):
            a, x = r.get(f), e[f]
            if not (_is_number(a) and _is_number(x) and float(a) == float(x)):
                mismatches.append([pt, f, f"输入={x!r} 交付={a!r}"])
    add("values_match_input", not mismatches,
        "逐行数值与输入对应值精确一致（期望值取自输入行）",
        mismatches[:5] or "ok")

    # ---- 血缘 ----
    act_cid = data.get("case_id") if data is not None else None
    add("case_id_lineage",
        data is not None and act_cid == case.get("case_id"),
        f"normalized.case_id == {case.get('case_id')!r}",
        "normalized 不可解析" if data is None else repr(act_cid))

    bad_ver = [[r.get("point"),
                f"输入 version={case.get('version')!r}",
                f"交付={r.get('source_version')!r}"]
               for r in safe_rows
               if r.get("source_version") != case.get("version")]
    add("source_version_lineage", not bad_ver,
        f"每行 source_version == {case.get('version')!r}",
        bad_ver[:5] or "ok")

    # ---- run_manifest.csv ----
    m_path = by_kind.get("run_manifest")
    if m_path is None or not m_path.is_file():
        add("manifest_present", False, "run_manifest.csv 已声明且文件存在",
            "deliverable 未声明" if m_path is None else "文件缺失")
        m_header, m_rows = None, None
    else:
        add("manifest_present", True, "已声明且存在", "ok")
        m_header, m_rows = _read_csv_strict(m_path)

    hdr_ok = (m_header is not None
              and set(MANIFEST_COLUMNS) <= set(m_header)
              and len(m_header) == len(set(m_header)))
    add("manifest_header_valid", hdr_ok,
        f"表头包含 {list(MANIFEST_COLUMNS)}（列序不限、无重复列）",
        "文件不可解析" if m_header is None else m_header)

    if m_rows is None:
        act_triples = None
    else:
        act_triples = sorted(
            (str(r.get("point")), str(r.get("case_id")), str(r.get("version")))
            for r in m_rows if isinstance(r, dict))
    add("manifest_reconciled", act_triples == exp_triples,
        [list(t) for t in exp_triples],
        "文件不可解析" if act_triples is None
        else [list(t) for t in act_triples])

    # ---- exceptions.csv ----
    e_path = by_kind.get("exceptions")
    if e_path is None or not e_path.is_file():
        add("exceptions_present", False, "exceptions.csv 已声明且文件存在",
            "deliverable 未声明" if e_path is None else "文件缺失")
        e_header, e_rows = None, None
    else:
        add("exceptions_present", True, "已声明且存在", "ok")
        e_header, e_rows = _read_csv_strict(e_path)

    ehdr_ok = (e_header is not None
               and set(EXCEPTION_COLUMNS) <= set(e_header)
               and len(e_header) == len(set(e_header)))
    add("exceptions_header_valid", ehdr_ok,
        f"表头包含 {list(EXCEPTION_COLUMNS)}（列序不限、无重复列）",
        "文件不可解析" if e_header is None else e_header)

    if e_rows is None:
        add("exceptions_reconciled", False,
            f"每个被拒收 point 一行: {dict(exp_exc_points)}", "文件不可解析")
    else:
        act_exc_points = Counter(str(r.get("point"))
                                 for r in e_rows if isinstance(r, dict))
        add("exceptions_reconciled", act_exc_points == exp_exc_points,
            f"每个被拒收 point 一行: {dict(exp_exc_points)}",
            f"实际计数 {dict(act_exc_points)}")

    bad_reasons = []
    if e_rows is None:
        add("rejection_reasons_match", False,
            "拒收理由与问题类别匹配且 detail 非空", "文件不可解析")
    else:
        for r in e_rows:
            if not isinstance(r, dict):
                continue
            pt = str(r.get("point"))
            cat = exp_exc_cat.get(pt)
            if cat is None:
                continue  # 多余行已由 exceptions_reconciled 判定
            reason = r.get("reason")
            detail = r.get("detail")
            reason_s = "" if reason is None else str(reason)
            detail_s = "" if detail is None else str(detail)
            kw_ok = any(kw in reason_s.lower() or kw in reason_s
                        for kw in REASON_KEYWORDS[cat])
            if not (kw_ok and detail_s.strip()):
                bad_reasons.append([pt, f"期望类别={cat}",
                                    f"reason={reason_s!r}", f"detail={detail_s!r}"])
        add("rejection_reasons_match", not bad_reasons,
            "拒收理由与问题类别匹配且 detail 非空",
            bad_reasons[:5] or "ok")

    failed = [c["name"] for c in checks if not c["passed"]]
    return {"checks": checks,
            "summary": f"{len(checks)-len(failed)}/{len(checks)} checks passed",
            "failed": failed}
