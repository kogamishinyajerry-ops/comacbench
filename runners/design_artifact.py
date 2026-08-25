"""design_artifact.py — 设计制品评审 adapter（五类标准 adapter 之四，YAML 驱动）。

适用（adapters/README.md §4）：cadgen.local_validity（dev；simjeb/openvsp 后续）。
首个落地基准：cadgen.local_validity —— 纯 Python CAD（cadquery）建模任务，
判分 100% 本地可复现（STEP 解析 / B-Rep 有效性 / 体积包络 / 接口几何 /
代码可重复执行复现同一制品），不含任何 CADGenBench 官方输入或私有 GT
相似度分数（PROVENANCE 见 data/cadgen/local_validity/PROVENANCE.md）。

模型输出契约：单个 ```python 代码块，只用 cadquery 库建模，参数写死无随机性，
在 cwd 导出 part.step（cq.exporters.export(shape, "part.step")）。

cadgen_local_validity 判分管线（严格顺序，前置不过即短路）：
  gate：
    1. 静态检查（复用 sandbox.static_check；网络/进程类违规）
       ——sandbox_escape_attempt（README 通用失败模式，单独告警）
    2. 脚本可执行（IsolatedRun 隔离执行 exit=0）——code_not_executable / timeout
    3. part.step 存在                             ——missing_output
    4. STEP 可解析 + B-Rep 有效（BRepCheck_Analyzer）+ 体积>0——invalid_geometry
    5. 重复执行一次，体积/包围盒三边 1e-6 相对一致
       （生成代码可重复执行复现同一制品，几何容差级）——nondeterministic_artifact
  physics      = 体积 + 包围盒三边 相对误差命中均值（各 1/4，tol=grader.numeric_rel_tol）
  requirements = grader.interface_checks 逐条通过率
                 （n_cyl_faces_with_radius[r,tol±1%] / n_faces_total[精确]）
  objective / robustness = N/A（本版无优化目标/扰动重算；权重 0，YAML 声明）

测量算子（gold 预计算与判分共用同一实现，单一事实源）：
  load_step / measure_step —— STEPControl_Reader 读回，GProp 体积、Bnd_Box 包络、
  TopExp 遍历面统计圆柱面半径（接口孔数核对），gen_tasks_cadgen 直接 import。

运行（须用 .venv-cad，判分侧依赖 cadquery/OCP）：
  cd benchmarks && .venv-cad/bin/python -m runners.design_artifact \
      --tasks tasks/cadgen.local_validity --out results/cadgen.local_validity/<date>/<provider> \
      --provider oracle --seed 0
"""

from __future__ import annotations

import argparse
import json
import time
from pathlib import Path
from typing import Any

from OCP.BRepAdaptor import BRepAdaptor_Surface
from OCP.BRepBndLib import BRepBndLib
from OCP.BRepCheck import BRepCheck_Analyzer
from OCP.BRepGProp import BRepGProp
from OCP.Bnd import Bnd_Box
from OCP.GProp import GProp_GProps
from OCP.GeomAbs import GeomAbs_SurfaceType
from OCP.IFSelect import IFSelect_ReturnStatus
from OCP.STEPControl import STEPControl_Reader
from OCP.TopAbs import TopAbs_FACE, TopAbs_SOLID
from OCP.TopExp import TopExp_Explorer
from OCP.TopoDS import TopoDS

from . import common
from .common import (FM_MISSING_OUTPUT, TaskSpec, aggregate_score, build_result,
                     environment_digest, gate_distribution, load_tasks,
                     write_run_manifest)
from .providers import ProviderError, get_answer
from .sandbox import IsolatedRun, static_check

ADAPTER = "design_artifact"
DEFAULT_WEIGHTS = {"physics": 0.5, "requirements": 0.5, "objective": 0.0, "robustness": 0.0}

OUTPUT_NAME = "part.step"
DETERMINISM_REL_TOL = 1e-6   # 复执行一致性（几何容差级；STEP 文本往返 ~1e-12）
IFACE_RADIUS_REL_TOL = 0.01  # 接口圆柱面半径匹配 ±1%

_SCRIPT_FAIL = "code_not_executable"
_GEOM_FAIL = "invalid_geometry"
_NONDET_FAIL = "nondeterministic_artifact"

# ---- 草图模式（cadbench_seldon.sketch_lite：2D 曲线制品，零实体） ----
SKETCH_KIND = "sketch_2d"          # grader.artifact_kind 取值，缺省 solid（cadgen）
SKETCH_OUTPUT = "sketch.step"
SKETCH_PT_TOL = 0.01               # mm；端点/拟合点匹配绝对容差（题面坐标 1e-6 精度）
SKETCH_PLANE_TOL = 0.01            # mm；共面性最大偏差
SKETCH_N_SAMPLE = 240              # 边采样点数（样条包含性/共面性检查用）

_ZERO_SUBS = {"physics": 0.0, "requirements": 0.0, "objective": None, "robustness": None}

APPLICABILITY = {
    "physics": "volume+bbox 三边相对误差 vs gold 预计算参考（各 1/4，1% 容差）",
    "requirements": "interface_checks 通过率（圆柱面数/半径匹配 ±1%、总面数精确）",
    "objective": "N/A(本版无优化目标)",
    "robustness": "N/A(无扰动重算；可重复执行复现同一制品由 gate 第 5 级覆盖)",
}


# ---------------------------------------------------------------- STEP 测量算子
# （gold 预计算（gen_tasks_cadgen）与判分共用，保证 reference 与 grade 同口径）

def load_step(path: Path):
    """读 STEP -> TopoDS_Shape；不可解析抛 ValueError（gate: invalid_geometry）。"""
    reader = STEPControl_Reader()
    if reader.ReadFile(str(path)) != IFSelect_ReturnStatus.IFSelect_RetDone:
        raise ValueError(f"STEP ReadFile failed: {path}")
    if not reader.TransferRoots():
        raise ValueError(f"STEP TransferRoots failed: {path}")
    shape = reader.OneShape()
    if shape.IsNull():
        raise ValueError(f"STEP OneShape is null: {path}")
    return shape


def measure_step(path: Path) -> dict[str, Any]:
    """对导出的 part.step 客观测量：B-Rep 有效性/体积/包围盒三边/面数/圆柱面半径。"""
    shape = load_step(path)
    valid = bool(BRepCheck_Analyzer(shape).IsValid())
    props = GProp_GProps()
    BRepGProp.VolumeProperties_s(shape, props)
    volume = float(props.Mass())
    box = Bnd_Box()
    BRepBndLib.Add_s(shape, box)
    x0, y0, z0, x1, y1, z1 = box.Get()

    n_faces, n_solids = 0, 0
    cyl_radii: list[float] = []
    exp_f = TopExp_Explorer(shape, TopAbs_FACE)
    while exp_f.More():
        face = TopoDS.Face_s(exp_f.Current())
        n_faces += 1
        try:
            adaptor = BRepAdaptor_Surface(face)
            if adaptor.GetType() == GeomAbs_SurfaceType.GeomAbs_Cylinder:
                cyl_radii.append(round(float(adaptor.Cylinder().Radius()), 9))
        except Exception:  # noqa: BLE001 — 单面退化不阻断整体测量，面数仍计入
            pass
        exp_f.Next()
    exp_s = TopExp_Explorer(shape, TopAbs_SOLID)
    while exp_s.More():
        n_solids += 1
        exp_s.Next()

    return {
        "brep_valid": valid,
        "volume_mm3": volume,
        "bbox_len_x": float(x1 - x0),
        "bbox_len_y": float(y1 - y0),
        "bbox_len_z": float(z1 - z0),
        "n_faces": n_faces,
        "n_solids": n_solids,
        "cyl_radii": sorted(cyl_radii),
    }


def count_cyl_faces(cyl_radii: list[float], radius: float,
                    rel_tol: float = IFACE_RADIUS_REL_TOL) -> int:
    """半径匹配（rel_tol 相对容差，缺省 ±1%）的圆柱面数——数孔。"""
    return sum(1 for r in cyl_radii
               if abs(r - radius) <= rel_tol * max(abs(radius), 1e-12))


def _rel(a: float, b: float) -> float:
    return abs(a - b) / max(abs(b), 1e-12)


# ---------------------------------------------------------------- 草图测量算子
# （gen_tasks_cbsk 预计算与判分共用；表示无关：STEP 往返可能线↔B样条，比对按几何等价）

def _edge_entities(path: Path) -> list[dict[str, Any]]:
    """读 STEP → 草图实体列表（line/bspline/circle；含采样点）。

    每实体：{kind, p0, p1（端点 3 元组）, pts（采样点，非 line 亦填充）,
    center/radius（仅 circle）}。无可读边 → ValueError（gate: invalid_geometry）。
    """
    from OCP.BRepAdaptor import BRepAdaptor_Curve
    from OCP.GeomAbs import GeomAbs_CurveType
    from OCP.TopAbs import TopAbs_EDGE

    shape = load_step(path)
    ents: list[dict[str, Any]] = []
    exp = TopExp_Explorer(shape, TopAbs_EDGE)
    while exp.More():
        edge = TopoDS.Edge_s(exp.Current())
        exp.Next()
        try:
            ad = BRepAdaptor_Curve(edge)
            t = ad.GetType()
            f, l = ad.FirstParameter(), ad.LastParameter()
            p0 = ad.Value(f); p1 = ad.Value(l)
            ent: dict[str, Any] = {
                "kind": {GeomAbs_CurveType.GeomAbs_Line: "line",
                         GeomAbs_CurveType.GeomAbs_Circle: "circle",
                         GeomAbs_CurveType.GeomAbs_BSplineCurve: "bspline"}.get(t, "other"),
                "p0": (p0.X(), p0.Y(), p0.Z()),
                "p1": (p1.X(), p1.Y(), p1.Z()),
                "pts": []}
            if ent["kind"] == "circle":
                circ = ad.Circle()
                c = circ.Location()
                ent["center"] = (c.X(), c.Y(), c.Z())
                ent["radius"] = float(circ.Radius())
                ent["full"] = abs((l - f) - 2 * 3.141592653589793) < 1e-6
            if ent["kind"] != "line":
                n = SKETCH_N_SAMPLE if ent["kind"] == "bspline" else 64
                ent["pts"] = []
                for i in range(n):
                    u = f + (l - f) * i / (n - 1)
                    q = ad.Value(u)
                    ent["pts"].append((q.X(), q.Y(), q.Z()))
            ents.append(ent)
        except Exception:  # noqa: BLE001 — 单边读取失败跳过（计数仍反映实体总数）
            ents.append({"kind": "unreadable", "p0": None, "p1": None, "pts": []})
    if not ents:
        raise ValueError("STEP 无可读边（非草图制品？）")
    return ents


def _d_pt_seg(p, a, b) -> float:
    """点 p 到线段 ab 的距离（共线偏差检查用）。"""
    ax, ay, az = a; bx, by, bz = b; px, py, pz = p
    abx, aby, abz = bx - ax, by - ay, bz - az
    apx, apy, apz = px - ax, py - ay, pz - az
    ab2 = abx * abx + aby * aby + abz * abz
    t = 0.0 if ab2 < 1e-18 else max(0.0, min(1.0, (apx * abx + apy * aby + apz * abz) / ab2))
    qx, qy, qz = ax + t * abx, ay + t * aby, az + t * abz
    return ((px - qx) ** 2 + (py - qy) ** 2 + (pz - qz) ** 2) ** 0.5


def _d_pt_polyline(p, pts) -> float:
    return min(_d_pt_seg(p, pts[i], pts[i + 1]) for i in range(len(pts) - 1))


def _ep_match(a0, a1, b0, b1, tol) -> bool:
    """两线段端点无序匹配。"""
    def d(x, y):
        return max(abs(x[i] - y[i]) for i in range(3))
    return ((d(a0, b0) <= tol and d(a1, b1) <= tol)
            or (d(a0, b1) <= tol and d(a1, b0) <= tol))


def match_sketch(gt: dict[str, Any], ents: list[dict[str, Any]],
                 tol: float = SKETCH_PT_TOL) -> dict[str, Any]:
    """GT 实体集 vs 模型实体集（贪心一对一；多余实体计数惩罚）。

    gt: {lines: [[p0,p1],...], splines: [[fit_pts...],...], circles: [[c3,r],...]}
    line 匹配表示无关：端点对齐即可，若模型侧为非 line 表示则另验共线偏差。
    """
    used = [False] * len(ents)
    hits: list[dict[str, Any]] = []
    n_gt = 0

    for g in gt.get("lines") or []:
        n_gt += 1
        hit = None
        for i, e in enumerate(ents):
            if used[i] or e["kind"] == "unreadable" or e.get("full"):
                continue
            if not _ep_match(g[0], g[1], e["p0"], e["p1"], tol):
                continue
            if e["kind"] != "line":   # B 样条表示的直线：共线偏差
                dev = max(_d_pt_seg(p, e["p0"], e["p1"]) for p in e["pts"])
                if dev > tol:
                    continue
            hit = i; break
        if hit is not None:
            used[hit] = True
            hits.append({"gt": f"line {g[0]}->{g[1]}", "ok": True})
        else:
            hits.append({"gt": f"line {g[0]}->{g[1]}", "ok": False, "status": "missing"})

    for fit in gt.get("splines") or []:
        n_gt += 1
        hit = None
        for i, e in enumerate(ents):
            if used[i] or e["kind"] == "unreadable" or e["kind"] == "circle":
                continue
            if not _ep_match(fit[0], fit[-1], e["p0"], e["p1"], tol):
                continue
            if all(_d_pt_polyline(p, e["pts"]) <= tol for p in fit):
                hit = i; break
        if hit is not None:
            used[hit] = True
            hits.append({"gt": f"spline {len(fit)}pts", "ok": True})
        else:
            hits.append({"gt": f"spline {len(fit)}pts", "ok": False, "status": "missing"})

    for spec in gt.get("circles") or []:
        n_gt += 1
        c, r = spec[0], float(spec[1])
        hit = None
        for i, e in enumerate(ents):
            if used[i] or e["kind"] != "circle" or not e.get("full"):
                continue
            dc = max(abs(e["center"][k] - c[k]) for k in range(3))
            if dc <= tol and abs(e["radius"] - r) <= max(tol, 1e-3 * r):
                hit = i; break
        if hit is not None:
            used[hit] = True
            hits.append({"gt": f"circle r={r}", "ok": True})
        else:
            hits.append({"gt": f"circle r={r}", "ok": False, "status": "missing"})

    n_extra = sum(1 for i, e in enumerate(ents) if not used[i]
                  and e["kind"] != "unreadable")
    matched = sum(1 for h in hits if h["ok"])
    return {"n_gt": n_gt, "matched": matched, "n_extra": n_extra, "hits": hits,
            "physics": round(max(0, matched - n_extra) / max(1, n_gt), 4)}


def closed_profiles(ents: list[dict[str, Any]],
                    tol: float = SKETCH_PT_TOL) -> int:
    """闭合环计数（两阶段）：
    1) 端点按 tol 聚类成几何顶点（并查集只 union 重合端点）；
    2) 边把顶点连成图分量；分量内全部顶点度恰为 2 ⇔ 简单闭合环。"""
    def d(x, y):
        return max(abs(x[i] - y[i]) for i in range(3))
    eps = [e for e in ents if e["kind"] != "unreadable"]
    ends = []
    for e in eps:
        ends.append(tuple(e["p0"])); ends.append(tuple(e["p1"]))
    n = len(ends)
    parent = list(range(n))

    def find(a):
        while parent[a] != a:
            parent[a] = parent[parent[a]]; a = parent[a]
        return a

    for i in range(n):
        for j in range(i + 1, n):
            if d(ends[i], ends[j]) <= tol:
                ra, rb = find(i), find(j)
                if ra != rb:
                    parent[ra] = rb

    # 阶段 1 完成后簇根稳定：顶点 = 去重后的根集合；边 → (r0, r1)
    verts = {}
    for i in range(n):
        verts.setdefault(find(i), len(verts))
    deg = [0] * len(verts)
    gp = list(range(len(verts)))

    def gfind(a):
        while gp[a] != a:
            gp[a] = gp[gp[a]]; a = gp[a]
        return a

    for k in range(len(eps)):
        a, b = verts[find(2 * k)], verts[find(2 * k + 1)]
        deg[a] += 1; deg[b] += 1
        ra, rb = gfind(a), gfind(b)
        if ra != rb:
            gp[ra] = rb

    closed = 0
    comp_all2 = {}
    for v in range(len(verts)):
        r = gfind(v)
        comp_all2[r] = comp_all2.get(r, True) and deg[v] == 2
    return sum(1 for ok in comp_all2.values() if ok)


def plane_check(ents: list[dict[str, Any]], normal_spec,
                tol_plane: float = SKETCH_PLANE_TOL) -> dict[str, Any]:
    """全部实体共面 + 法向与规格对齐（± 号不敏感）。"""
    import numpy as np
    pts = []
    for e in ents:
        if e["kind"] == "unreadable":
            continue
        pts.append(e["p0"]); pts.append(e["p1"])
        pts.extend(e.get("pts") or [])
    if len(pts) < 3:
        return {"ok": False, "reason": "points<3"}
    a = np.array(pts, dtype=float)
    c = a.mean(axis=0)
    _, _, vh = np.linalg.svd(a - c, full_matrices=False)
    normal = vh[-1]
    dev = float(np.abs((a - c) @ normal).max())
    ns = np.array(normal_spec, dtype=float)
    ns = ns / np.linalg.norm(ns)
    align = float(abs(normal @ ns))
    return {"ok": bool(dev <= tol_plane and align >= 0.999),
            "max_dev": round(dev, 6), "normal_align": round(align, 6)}


def sketch_canonical(ents: list[dict[str, Any]]) -> str:
    """实体集规范化串（确定性双跑比对用；1e-6 舍入吸收 STEP 文本往返噪声）。"""
    def r(p):
        return tuple(round(v, 6) for v in p) if p else None
    items = []
    for e in ents:
        if e["kind"] == "line":
            items.append(("l", r(e["p0"]), r(e["p1"])))
        elif e["kind"] == "circle":
            items.append(("c", r(e["center"]), round(e["radius"], 6)))
        elif e["kind"] == "bspline":
            items.append(("s", r(e["p0"]), r(e["p1"]),
                          tuple(r(p) for p in e["pts"][::12])))
        else:
            items.append(("u",))
    return repr(sorted(items, key=repr))


# ---------------------------------------------------------------- 草图判分管线

_SKETCH_APPLICABILITY = {
    "physics": "实体级匹配 vs 题面 GT（线段端点无序/样条拟合点在曲线上；多余实体惩罚）",
    "requirements": "实体数精确/闭合环数精确/共面与法向规格",
    "objective": "N/A(本版无优化目标)",
    "robustness": "N/A(可重复执行复现同一草图由 gate 第 5 级覆盖)",
}


def _run_sketch_task(
    task: TaskSpec, code: str, meta: dict,
    t0: float, env_digest: str, logs: list[str],
) -> dict[str, Any]:
    """sketch_2d：模型 cadquery 脚本构造题面规定的 2D 曲线（零实体），导出 sketch.step。

    gate（顺序短路）：静态检查 → 双跑可执行 → sketch.step 存在 → STEP 可解析出边
    且共面 → 双跑实体集一致（nondeterministic_artifact）。
    physics = match_sketch（GT 实体命中 - 多余实体）/ GT 总数；
    requirements = grader.sketch_checks（n_entities/n_closed_profiles/plane）。
    """
    g = task["grader"]
    timeout = float(task["limits"]["wall_clock_s"])
    gt = g["sketch_gt"]

    def _ret(gate: int, gf: list[str], fm: str | None,
             subs: dict[str, Any], details: dict[str, Any]):
        weights = {**DEFAULT_WEIGHTS, **(task["scoring"].get("weights") or {})}
        score = aggregate_score({k: (v if v is not None else 0.0)
                                 for k, v in subs.items()}, weights, gate)
        return build_result(task=task, adapter=ADAPTER, validity_gate=gate,
            gate_failures=gf, subscores=subs, score=score,
            artifacts={"code": json.dumps(code[:4000], ensure_ascii=False),
                       "model_meta": json.dumps(meta, ensure_ascii=False),
                       "grade_details": json.dumps(details, ensure_ascii=False)},
            timings={"agent_s": time.time() - t0, "setup_s": 0.0,
                     "grade_s": round(time.time() - grade_t0, 3)},
            env_digest=env_digest, logs=logs, failure_mode=fm,
            applicability=_SKETCH_APPLICABILITY)

    grade_t0 = time.time()
    ents_by_run: list[list[dict[str, Any]]] = []
    for run_no in (1, 2):
        iso = IsolatedRun()
        r = iso.run(iso.write("model.py", code), timeout)
        logs.append(f"run{run_no} exit={r['exit']} {r['duration_s']}s")
        if r["timeout"]:
            return _ret(0, ["timeout"], "timeout", _ZERO_SUBS,
                        {"run": run_no, "stderr_tail": r["stderr"][-800:]})
        if r["exit"] != 0:
            return _ret(0, [_SCRIPT_FAIL], _SCRIPT_FAIL, _ZERO_SUBS,
                        {"run": run_no, "exit": r["exit"],
                         "stderr_tail": r["stderr"][-800:]})
        step = iso.dir / SKETCH_OUTPUT
        if not step.exists():
            return _ret(0, [FM_MISSING_OUTPUT], FM_MISSING_OUTPUT, _ZERO_SUBS,
                        {"run": run_no, "missing": SKETCH_OUTPUT,
                         "dir_listing": sorted(p.name for p in iso.dir.iterdir())[:20]})
        try:
            ents = _edge_entities(step)
        except Exception as e:  # noqa: BLE001
            return _ret(0, [_GEOM_FAIL], _GEOM_FAIL, _ZERO_SUBS,
                        {"run": run_no, "parse_error": str(e)[:300]})
        pc = plane_check(ents, g["plane_normal"])
        if not pc["ok"]:
            return _ret(0, [_GEOM_FAIL], _GEOM_FAIL, _ZERO_SUBS,
                        {"run": run_no, "plane": pc,
                         "reason": "非共面或法向不符（实体非平面草图？）"})
        ents_by_run.append(ents)

    # ---- gate 5：确定性（实体集规范化串一致） ----
    c1, c2 = sketch_canonical(ents_by_run[0]), sketch_canonical(ents_by_run[1])
    if c1 != c2:
        return _ret(0, [_NONDET_FAIL], _NONDET_FAIL, _ZERO_SUBS,
                    {"determinism": {"run1": c1[:400], "run2": c2[:400]}})

    ents = ents_by_run[0]
    m = match_sketch(gt, ents)
    physics = float(m["physics"])

    checks_out: list[dict[str, Any]] = []
    for chk in g.get("sketch_checks") or []:
        kind = chk.get("check")
        if kind == "n_entities":
            got = len(ents); exp = int(chk["expect"])
            checks_out.append({"check": kind, "expect": exp, "got": got,
                               "ok": got == exp})
        elif kind == "n_closed_profiles":
            got = closed_profiles(ents); exp = int(chk["expect"])
            checks_out.append({"check": kind, "expect": exp, "got": got,
                               "ok": got == exp})
        elif kind == "plane":
            checks_out.append({"check": kind, "expect": True,
                               "got": pc["ok"], "ok": bool(pc["ok"])})
        else:
            checks_out.append({"check": str(kind), "error": "unknown check kind"})
    requirements = round(
        sum(1 for c in checks_out if c.get("ok")) / len(checks_out), 4) \
        if checks_out else 0.0

    details = {"kind": "sketch_2d", "match": {k: m[k] for k in
                                              ("n_gt", "matched", "n_extra")},
               "hits": m["hits"], "physics_score": physics,
               "sketch_checks": checks_out, "requirements_score": requirements,
               "n_model_entities": len(ents)}
    subs = {"physics": physics, "requirements": requirements,
            "objective": None, "robustness": None}
    logs.append(f"physics={physics} requirements={requirements} "
                f"matched={m['matched']}/{m['n_gt']} extra={m['n_extra']}")
    return _ret(1, [], None, subs, details)


# ---------------------------------------------------------------- 判分

def _eval_interface_checks(checks: list[dict], m: dict[str, Any]) -> list[dict]:
    """grader.interface_checks 逐条核对（客观算子，全部对 part.step 实测执行）。"""
    out: list[dict] = []
    for chk in checks:
        kind = chk.get("check")
        if kind == "n_cyl_faces_with_radius":
            radius = float(chk["radius"])
            got = count_cyl_faces(m["cyl_radii"], radius)
            out.append({"check": kind, "radius": radius, "expect": int(chk["expect"]),
                        "got": got, "ok": got == int(chk["expect"]),
                        "rel_tol": IFACE_RADIUS_REL_TOL})
        elif kind == "n_faces_total":
            got = int(m["n_faces"])
            out.append({"check": kind, "expect": int(chk["expect"]),
                        "got": got, "ok": got == int(chk["expect"])})
        else:
            out.append({"check": str(kind), "error": "unknown check kind"})
    return out


def run_task(
    task: TaskSpec, *, provider: str, model: str | None, seed: int,
    env_digest: str, prompt_cache: dict[str, str], assets_root: Path,
    oracle_cache: dict[str, str] | None,
    prompt_override: str | None = None,
) -> dict[str, Any]:
    t0 = time.time()
    prompt = prompt_override if prompt_override is not None else prompt_cache[task.id]
    g = task["grader"]
    timeout = float(task["limits"]["wall_clock_s"])

    # ---- 模型脚本 ----
    if provider == "oracle":
        code = oracle_cache[task.id]     # grader.oracle_source 指向的 gold 脚本原文
        meta = {"provider": "oracle", "note": "gold script verbatim（判分器自检）"}
    else:
        out = get_answer(provider, task, prompt, seed=seed, model=model,
                         max_attempts=int(task["limits"]["attempts"]), expect="code")
        code, meta = out["answer"], out["meta"]

    # gold 也过静态检查（其只 import math/cadquery，应当通过——如实核对而非豁免）
    violations, syntax_ok = static_check(code)
    logs = [f"violations={violations}", f"syntax_ok={syntax_ok}",
            f"provider={provider} code_len={len(code)}"]

    def _ret(gate: int, gf: list[str], fm: str | None,
             subs: dict[str, Any], details: dict[str, Any]):
        weights = {**DEFAULT_WEIGHTS, **(task["scoring"].get("weights") or {})}
        score = aggregate_score({k: (v if v is not None else 0.0)
                                 for k, v in subs.items()}, weights, gate)
        return build_result(task=task, adapter=ADAPTER, validity_gate=gate,
            gate_failures=gf, subscores=subs, score=score,
            artifacts={"code": json.dumps(code[:4000], ensure_ascii=False),
                       "model_meta": json.dumps(meta, ensure_ascii=False),
                       "grade_details": json.dumps(details, ensure_ascii=False)},
            timings={"agent_s": time.time() - t0, "setup_s": 0.0,
                     "grade_s": round(time.time() - grade_t0, 3)},
            env_digest=env_digest, logs=logs, failure_mode=fm,
            applicability=APPLICABILITY)

    grade_t0 = time.time()

    if violations:
        return _ret(0, ["sandbox_escape_attempt"], "sandbox_escape_attempt",
                    _ZERO_SUBS, {"violations": violations})
    if not syntax_ok:
        return _ret(0, [_SCRIPT_FAIL], _SCRIPT_FAIL,
                    _ZERO_SUBS, {"syntax_error": True})

    # ---- 草图模式分发（cadbench_seldon.sketch_lite；静态检查已共用） ----
    if g.get("artifact_kind") == SKETCH_KIND:
        return _run_sketch_task(task, code, meta, t0, env_digest, logs)

    # ---- gate 1-2：沙箱执行（sys.executable 即 .venv-cad，cadquery 可导入）----
    iso1 = IsolatedRun()
    r1 = iso1.run(iso1.write("model.py", code), timeout)
    logs.append(f"run1 exit={r1['exit']} {r1['duration_s']}s")
    if r1["timeout"]:
        return _ret(0, ["timeout"], "timeout", _ZERO_SUBS,
                    {"run": 1, "stderr_tail": r1["stderr"][-800:]})
    if r1["exit"] != 0:
        return _ret(0, [_SCRIPT_FAIL], _SCRIPT_FAIL, _ZERO_SUBS,
                    {"run": 1, "exit": r1["exit"],
                     "stderr_tail": r1["stderr"][-800:]})

    # ---- gate 3：产物存在 ----
    step1 = iso1.dir / OUTPUT_NAME
    if not step1.exists():
        return _ret(0, [FM_MISSING_OUTPUT], FM_MISSING_OUTPUT, _ZERO_SUBS,
                    {"run": 1, "missing": OUTPUT_NAME,
                     "dir_listing": sorted(p.name for p in iso1.dir.iterdir())[:20]})

    # ---- gate 4：STEP 可解析 + B-Rep 有效 + 体积>0 ----
    try:
        m1 = measure_step(step1)
    except Exception as e:  # noqa: BLE001 — STEP 不可解析/传输失败
        return _ret(0, [_GEOM_FAIL], _GEOM_FAIL, _ZERO_SUBS,
                    {"run": 1, "parse_error": str(e)[:300]})
    if not m1["brep_valid"]:
        return _ret(0, [_GEOM_FAIL], _GEOM_FAIL, _ZERO_SUBS,
                    {"run": 1, "brep_valid": False,
                     "n_faces": m1["n_faces"], "n_solids": m1["n_solids"]})
    if not m1["volume_mm3"] > 0.0:
        return _ret(0, [_GEOM_FAIL], _GEOM_FAIL, _ZERO_SUBS,
                    {"run": 1, "volume_nonpositive": m1["volume_mm3"]})

    # ---- gate 5：重复执行复现同一制品（体积/包围盒 1e-6 相对一致）----
    iso2 = IsolatedRun()
    r2 = iso2.run(iso2.write("model.py", code), timeout)
    logs.append(f"run2 exit={r2['exit']} {r2['duration_s']}s")
    if r2["timeout"]:
        return _ret(0, ["timeout"], "timeout", _ZERO_SUBS,
                    {"run": 2, "stderr_tail": r2["stderr"][-800:]})
    if r2["exit"] != 0 or not (iso2.dir / OUTPUT_NAME).exists():
        return _ret(0, [_NONDET_FAIL], _NONDET_FAIL, _ZERO_SUBS,
                    {"run": 2, "exit": r2["exit"],
                     "missing": None if r2["exit"] != 0 else OUTPUT_NAME,
                     "stderr_tail": r2["stderr"][-800:]})
    try:
        m2 = measure_step(iso2.dir / OUTPUT_NAME)
    except Exception as e:  # noqa: BLE001
        return _ret(0, [_NONDET_FAIL], _NONDET_FAIL, _ZERO_SUBS,
                    {"run": 2, "parse_error": str(e)[:300]})
    det = {
        "tol": DETERMINISM_REL_TOL,
        "volume_rel_diff": _rel(m2["volume_mm3"], m1["volume_mm3"]),
        "bbox_rel_diff": [_rel(m2["bbox_len_x"], m1["bbox_len_x"]),
                          _rel(m2["bbox_len_y"], m1["bbox_len_y"]),
                          _rel(m2["bbox_len_z"], m1["bbox_len_z"])],
    }
    det["bbox_max_rel_diff"] = max(det["bbox_rel_diff"])
    det["ok"] = bool(det["volume_rel_diff"] <= DETERMINISM_REL_TOL
                     and det["bbox_max_rel_diff"] <= DETERMINISM_REL_TOL)
    if not det["ok"]:
        return _ret(0, [_NONDET_FAIL], _NONDET_FAIL, _ZERO_SUBS,
                    {"run": 2, "determinism": det,
                     "m1": {k: m1[k] for k in ("volume_mm3", "bbox_len_x",
                                               "bbox_len_y", "bbox_len_z")},
                     "m2": {k: m2[k] for k in ("volume_mm3", "bbox_len_x",
                                               "bbox_len_y", "bbox_len_z")}})

    # ---- physics：体积 + 包围盒三边 相对误差命中（各 1/4）----
    tol = float(g.get("numeric_rel_tol", 0.01))
    ref = task["reference"]["values"]
    comps = [("volume_mm3", m1["volume_mm3"], float(ref["volume_mm3"])),
             ("bbox_len_x", m1["bbox_len_x"], float(ref["bbox_len_x"])),
             ("bbox_len_y", m1["bbox_len_y"], float(ref["bbox_len_y"])),
             ("bbox_len_z", m1["bbox_len_z"], float(ref["bbox_len_z"]))]
    hits: dict[str, Any] = {}
    for key, got, expect in comps:
        rel = _rel(got, expect)
        hits[key] = {"rel_err": round(rel, 9), "ok": bool(rel <= tol),
                     "got": round(got, 6), "ref": round(expect, 6)}
    physics = round(sum(1 for v in hits.values() if v["ok"]) / len(comps), 4)

    # ---- requirements：接口配合逐条核对 ----
    checks = list(g.get("interface_checks") or [])
    iface = _eval_interface_checks(checks, m1)
    requirements = round(
        sum(1 for c in iface if c.get("ok")) / len(iface), 4) if iface else 0.0

    details = {
        "kind": "cadgen_local_validity",
        "runs": [{"exit": r1["exit"], "duration_s": r1["duration_s"]},
                 {"exit": r2["exit"], "duration_s": r2["duration_s"]}],
        "determinism": det,
        "measured": {"volume_mm3": round(m1["volume_mm3"], 6),
                     "bbox_len": [round(m1["bbox_len_x"], 6),
                                  round(m1["bbox_len_y"], 6),
                                  round(m1["bbox_len_z"], 6)],
                     "n_faces": m1["n_faces"], "n_solids": m1["n_solids"],
                     "cyl_radii": m1["cyl_radii"]},
        "reference": {"volume_mm3": round(float(ref["volume_mm3"]), 6),
                      "bbox_len": [round(float(ref["bbox_len_x"]), 6),
                                   round(float(ref["bbox_len_y"]), 6),
                                   round(float(ref["bbox_len_z"]), 6)]},
        "physics_hits": hits, "physics_score": physics,
        "interface_checks": iface, "requirements_score": requirements,
        "rel_tol": tol,
    }
    subs = {"physics": physics, "requirements": requirements,
            "objective": None, "robustness": None}
    logs.append(f"physics={physics} requirements={requirements} "
                f"vol_rel={hits['volume_mm3']['rel_err']:.2e}")
    return _ret(1, [], None, subs, details)


# ---------------------------------------------------------------- 迭代协议（v0.3，镜像 simulation_agent）

# 可反馈修复：脚本/产物/几何/非确定（timeout=资源、sandbox=策略违规不进迭代）
_DA_FIXABLE = {_SCRIPT_FAIL, FM_MISSING_OUTPUT, _GEOM_FAIL, _NONDET_FAIL}


def build_feedback_prompt(base_prompt: str, prev_result: dict[str, Any],
                          round_no: int) -> str:
    """design_artifact 反馈提示：原题面 + 上一轮代码 + 执行/几何诊断。"""
    try:
        code = json.loads(prev_result["artifacts"].get("code") or '""')
    except Exception:  # noqa: BLE001
        code = ""
    code = str(code)[:6000]
    det = json.loads(prev_result["artifacts"].get("grade_details") or "{}")
    diag = [f"- failure_mode: {prev_result.get('failure_mode')}",
            f"- gate_failures: {prev_result.get('gate_failures')}"]
    for k in ("stderr_tail", "missing", "volume_nonpositive", "parse_error",
              "n_faces", "n_solids", "determinism", "measured", "reference"):
        if det.get(k) is not None:
            diag.append(f"- {k}: {det[k]}")
    return (f"{base_prompt}\n\n---\n\n## ITERATION FEEDBACK — attempt {round_no} FAILED\n\n"
            f"Your previous script:\n```python\n{code}\n```\n\n"
            f"Execution diagnostics:\n" + "\n".join(diag) +
            "\n\nFix the failure. Respond with a single complete "
            "```python code block (the full revised script, not a diff).")


def run_task_iterate(
    task: TaskSpec, *, iterate: int, provider: str, model: str | None, seed: int,
    env_digest: str, prompt_cache: dict[str, str], assets_root: Path,
    oracle_cache: dict[str, str] | None = None,
) -> dict[str, Any]:
    """迭代协议包装（与 simulation_agent.run_task_iterate 同构）：
    rounds_to_success 落 artifacts.iteration 不进 score；iterate=1 行为与直调一致。"""
    r = run_task(task, provider=provider, model=model, seed=seed,
                 env_digest=env_digest, prompt_cache=prompt_cache,
                 assets_root=assets_root, oracle_cache=oracle_cache)
    rounds_used = 1
    while (r["validity_gate"] == 0 and rounds_used < iterate
           and (r.get("failure_mode") in _DA_FIXABLE)):
        fb = build_feedback_prompt(prompt_cache[task.id], r, rounds_used)
        r = run_task(task, provider=provider, model=model, seed=seed,
                     env_digest=env_digest, prompt_cache=prompt_cache,
                     assets_root=assets_root, oracle_cache=oracle_cache,
                     prompt_override=fb)
        rounds_used += 1
    r["artifacts"]["iteration"] = json.dumps(
        {"rounds_used": rounds_used, "iterate_max": iterate,
         "converged": r["validity_gate"] == 1}, ensure_ascii=False)
    if "applicability" in r:
        r["applicability"]["iteration"] = f"rounds {rounds_used}/{iterate}"
    return r


# ---------------------------------------------------------------- summary

def write_summary(out_dir: Path, results: list[dict[str, Any]],
                  provider: str, model_label: str, seed: int) -> Path:
    dist = gate_distribution(results)
    lines = []
    a = lines.append
    a(f"# design_artifact 结果汇总（provider={provider}, model={model_label}, seed={seed}）")
    a("")
    a("## ValidityGate 分布（先看 gate，再看子分）")
    a("")
    a(f"- 任务总数: {dist['n_tasks']}")
    a(f"- gate 通过: {dist['gate_passed']}")
    a(f"- gate 失败: {dist['gate_failed']}（直接 0 分）")
    a(f"- 作废: {dist['voided']}")
    a(f"- gate 失败原因分布: {dist['gate_failure_reasons'] or '无'}")
    a("")
    sc = [r["score"] for r in results]
    a(f"## 均分: {sum(sc) / len(sc):.4f}（gate 均值 {dist['gate_passed']}/{dist['n_tasks']}）")
    a("")
    a("## 每任务明细")
    a("")
    a("| task | gate | 失败模式 | vol_rel | bbox_max_rel | iface | physics | req | score |")
    a("| --- | --- | --- | --- | --- | --- | --- | --- | --- |")
    for r in results:
        det_raw = r["artifacts"].get("grade_details")
        vol_rel = bbox_rel = "-"
        iface = "-"
        if det_raw:
            d = json.loads(det_raw)
            if "physics_hits" in d:
                vol_rel = f"{d['physics_hits']['volume_mm3']['rel_err']:.2e}"
                bbox_rel = f"{max(d['physics_hits'][k]['rel_err'] for k in
                                   ('bbox_len_x', 'bbox_len_y', 'bbox_len_z')):.2e}"
            if "interface_checks" in d:
                n_ok = sum(1 for c in d["interface_checks"] if c.get("ok"))
                iface = f"{n_ok}/{len(d['interface_checks'])}"
        ph = r["subscores"]["physics"]
        rq = r["subscores"]["requirements"]
        a(f"| {r['task_id']} | {r['validity_gate']} "
          f"| {r['failure_mode'] or '-'} | {vol_rel} | {bbox_rel} | {iface} "
          f"| {ph if ph is not None else '-'} "
          f"| {rq if rq is not None else '-'} | {r['score']} |")
    p = out_dir / "summary.md"
    p.write_text("\n".join(lines) + "\n", encoding="utf-8")
    return p


# ---------------------------------------------------------------- CLI

def main() -> int:
    ap = argparse.ArgumentParser(description="design_artifact adapter runner")
    ap.add_argument("--tasks", required=True)
    ap.add_argument("--out", required=True)
    ap.add_argument("--provider", default="stub",
                    choices=["stub", "oracle", "openai_compat", "glm", "minimax"])
    ap.add_argument("--model", default=None)
    ap.add_argument("--seed", type=int, default=0)
    ap.add_argument("--resume", action="store_true",
                    help="跳过 out 下已有 result_<task_id>.json 的任务（读入参与"
                         "汇总，损坏文件自动重跑）；summary/manifest 按全量重建")
    ap.add_argument("--iterate", type=int, default=1,
                    help="迭代协议轮数上限（v0.3 harness 臂 H3）：失败且可修复时"
                         "把诊断喂回模型修订重跑；1=单轮（默认，与既有行为一致）")
    ap.add_argument("--limit", type=int, default=0,
                    help="只跑前 K 个任务（0=全量）")
    ap.add_argument("--scaffold", default=None,
                    help="H2/H3 harness 臂：蒸馏工作流文档路径，注入每题 prompt"
                         "前部（反馈轮自动携带）；与 --iterate 组合构成臂矩阵")
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
            text = f.read()
        want = t["input"].get("prompt_sha256")
        if want and common.sha256_bytes(text.encode()) != want:
            raise SystemExit(f"{t.id}: 题面 sha256 漂移（{pf}）——按新评测周期处理")
        prompt_cache[t.id] = text
        asset_paths.append(pf)
    env_digest = environment_digest(extra_paths=asset_paths)

    tasks = tasks[:args.limit] if args.limit > 0 else tasks

    # H2/H3 harness 臂：蒸馏工作流文档注入 prompt 前部（镜像 simulation_agent）
    if args.scaffold:
        sp = Path(args.scaffold)
        if not sp.is_absolute():
            sp = (common.BENCH_ROOT / sp).resolve()
        scaffold_text = sp.read_text(encoding="utf-8").strip() + "\n\n---\n\n# TASK\n\n"
        for tid in prompt_cache:
            prompt_cache[tid] = scaffold_text + prompt_cache[tid]

    oracle_cache: dict[str, str] = {}
    if args.provider == "oracle":
        for t in tasks:
            src = t["grader"].get("oracle_source")
            if not src:
                raise SystemExit(f"{t.id}: 无 oracle_source")
            p = Path(src)
            if not p.is_absolute():
                p = (assets_root / src).resolve()
            oracle_cache[t.id] = p.read_text(encoding="utf-8")

    from .providers import PROVIDER_PRESETS
    model_label = args.model or PROVIDER_PRESETS.get(args.provider, {}).get(
        "model_default", "n/a")

    rerun = (f"cd {common.BENCH_ROOT} && .venv-cad/bin/python -m runners.design_artifact "
             f"--tasks {tasks_dir.as_posix()} --out {out_dir.as_posix()} "
             f"--provider {args.provider}"
             + (f" --model {args.model}" if args.model else "")
             + f" --seed {args.seed}"
             + (" --resume" if args.resume else ""))

    results, crash, resumed = [], 0, 0
    for t in tasks:
        rp = out_dir / f"result_{t.id}.json"
        if args.resume and rp.exists():
            try:
                results.append(json.loads(rp.read_text(encoding="utf-8")))
                resumed += 1
                continue
            except Exception:  # noqa: BLE001 — 损坏的半截文件按缺失处理重跑
                pass
        try:
            if args.iterate > 1 or args.scaffold:
                r = run_task_iterate(t, iterate=max(1, args.iterate),
                                     provider=args.provider, model=args.model,
                                     seed=args.seed, env_digest=env_digest,
                                     prompt_cache=prompt_cache,
                                     assets_root=assets_root,
                                     oracle_cache=oracle_cache or None)
            else:
                r = run_task(t, provider=args.provider, model=args.model, seed=args.seed,
                             env_digest=env_digest, prompt_cache=prompt_cache,
                             assets_root=assets_root,
                             oracle_cache=oracle_cache or None)
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
                            extra={"crash_tasks": crash, "model": model_label,
                                   "resumed_tasks": resumed,
                                   "harness_arm": ("H3" if (args.scaffold and args.iterate > 1)
                                                   else "H2" if args.scaffold
                                                   else "H1" if args.iterate > 1 else "H0"),
                                   "scaffold": (args.scaffold or None),
                                   "iterate_rounds": args.iterate,
                                   "limit": args.limit,
                                   "python": ".venv-cad/bin/python",
                                   "determinism_rel_tol": DETERMINISM_REL_TOL,
                                   "iface_radius_rel_tol": IFACE_RADIUS_REL_TOL})
    sm = write_summary(out_dir, results, args.provider, model_label, args.seed)
    dist = gate_distribution(results)
    scores = [r["score"] for r in results]
    print(f"[done] {dist['n_tasks']} tasks | gate pass {dist['gate_passed']} "
          f"| fail {dist['gate_failed']} | voided {dist['voided']} | crash {crash} "
          f"| mean {sum(scores) / len(scores):.4f}")
    print(f"       summary -> {sm}")
    print(f"       rerun: {rerun}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
