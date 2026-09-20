"""gen_tasks_cadgen.py — 自建 cadgen.local_validity 任务集（batch-2，design_artifact）。

产出（幂等；参考值由 gold 脚本预计算锁定）：
  data/cadgen/local_validity/{gold/,references/,PROVENANCE.md} + 任务 YAML/MD

任务协议（design_artifact adapter）：
  被测模型写 python 脚本，只用 cadquery 建模，在 cwd 导出 part.step；
  判分 = STEP 解析/B-Rep 有效/体积/包络/接口几何（全部本地可复现，OCP 实测），
  外加「重复执行复现同一制品」gate。无任何 CADGenBench 官方输入/GT。

任务集：6 个自建参数化族 × 3-4 个参数变体 = 22 道（同族变体体积互差 >2%，
生成器断言防简并）：
  圆法兰+螺栓孔环 / 矩形板+四角孔+边倒圆 / L 角支架(内圆角+腿孔) /
  套筒环形件 / 阶梯轴+中心孔 / 带凸台底板。

gold 脚本在干净目录用 .venv-cad 执行导出 part.step，测量结果（与判分器同一
实现 runners.design_artifact.measure_step）落 references/<tid>.json 并内嵌任务
YAML reference.values（照 gen_tasks_pycycle 的 gold 预计算+references 锁定范式）。

用法：.venv-cad/bin/python -m runners.gen_tasks_cadgen [--check] [--force-refs]
"""

from __future__ import annotations

import argparse
import hashlib
import json
import math
import os
import subprocess
import tempfile
from pathlib import Path

import yaml

from .design_artifact import measure_step

BENCH = Path(__file__).resolve().parent.parent
DATA = BENCH / "data/cadgen/local_validity"
TASKS_DIR = BENCH / "tasks/cadgen.local_validity"
ASSETS_REVISION = "cadgen-local@selfbuilt-2026-08-21+cadquery2.8.0"

REL_TOL = 0.01          # 体积/包围盒 1%；接口半径 ±1%（runner 同款）
VOL_SPREAD = 0.02       # 同族变体体积互差 >2%（防简并，题集区分度下限）

_VENV_PY = BENCH / ".venv-cad/bin/python"

_PROMPT_TAIL = (
    "Hard-code all parameters (no randomness), use only the cadquery library, and "
    "export the final single solid to the current working directory as part.step "
    "(e.g. cq.exporters.export(shape, \"part.step\")).\n\n"
    "Grading is fully local and reproducible: part.step must parse and yield a "
    "B-Rep valid solid with positive volume; re-running your script must reproduce "
    "the same artifact (volume/bounding box within 1e-6 relative); volume and the "
    "three bounding-box edge lengths must match the reference within {tol} relative; "
    "interface checks: {iface}; total face count must match exactly.\n\n"
    "Respond with a single ```python code block and nothing else.\n")


# ---------------------------------------------------------------- gold 模板

def _gold_flange(p: dict) -> str:
    return f'''"""gold 解（cadquery 圆法兰+螺栓孔环）。判分参考预计算用；模型不可见。"""
import cadquery as cq

PLATE_D = {p["plate_d"]!r}
THK = {p["thickness"]!r}
N_HOLES = {p["n_holes"]!r}
HOLE_D = {p["hole_d"]!r}
PCD = {p["pcd"]!r}

part = (cq.Workplane("XY").circle(PLATE_D / 2.0).extrude(THK)
        .faces(">Z").workplane()
        .polarArray(PCD / 2.0, 0.0, 360.0, N_HOLES)
        .circle(HOLE_D / 2.0).cutThruAll())
cq.exporters.export(part.val(), "part.step")
'''


def _gold_plate(p: dict) -> str:
    return f'''"""gold 解（cadquery 矩形板+四角孔+边倒圆）。判分参考预计算用；模型不可见。"""
import cadquery as cq

L = {p["L"]!r}
W = {p["W"]!r}
T = {p["t"]!r}
HOLE_D = {p["hole_d"]!r}
CORNER_R = {p["corner_r"]!r}
INSET = {p["hole_inset"]!r}

part = (cq.Workplane("XY").rect(L, W).extrude(T)
        .edges("|Z").fillet(CORNER_R)
        .faces(">Z").workplane()
        .pushPoints([(-L / 2.0 + INSET, -W / 2.0 + INSET),
                     (L / 2.0 - INSET, -W / 2.0 + INSET),
                     (-L / 2.0 + INSET, W / 2.0 - INSET),
                     (L / 2.0 - INSET, W / 2.0 - INSET)])
        .circle(HOLE_D / 2.0).cutThruAll())
cq.exporters.export(part.val(), "part.step")
'''


def _gold_lbracket(p: dict) -> str:
    return f'''"""gold 解（cadquery L 角支架：两腿+内圆角+腿孔）。判分参考预计算用；模型不可见。"""
import math

import cadquery as cq

LEG_X = {p["leg_x"]!r}
H = {p["H"]!r}
T = {p["t"]!r}
WID = {p["width"]!r}
FILLET_R = {p["fillet_r"]!r}
HOLE_D = {p["hole_d"]!r}
HX = T + (LEG_X - T) / 2.0
VZ = T + (H - T) / 2.0
OVER = 1.0  # 切割圆柱超出材料 1mm，避免共面布尔退化

profile = (cq.Workplane("XZ")
           .moveTo(0.0, 0.0).lineTo(LEG_X, 0.0).lineTo(LEG_X, T).lineTo(T + FILLET_R, T)
           .threePointArc((T + FILLET_R - FILLET_R / math.sqrt(2.0),
                           T + FILLET_R - FILLET_R / math.sqrt(2.0)),
                          (T, T + FILLET_R))
           .lineTo(T, H).lineTo(0.0, H).close().extrude(WID))
solid = profile.val()
if solid.Center().y < 0.0:
    solid = solid.translate(cq.Vector(0.0, WID, 0.0))
hole_h = cq.Solid.makeCylinder(HOLE_D / 2.0, T + 2.0 * OVER,
                               cq.Vector(HX, WID / 2.0, -OVER), cq.Vector(0.0, 0.0, 1.0))
hole_v = cq.Solid.makeCylinder(HOLE_D / 2.0, T + 2.0 * OVER,
                               cq.Vector(-OVER, WID / 2.0, VZ), cq.Vector(1.0, 0.0, 0.0))
solid = solid.cut(hole_h).cut(hole_v)
cq.exporters.export(solid, "part.step")
'''


def _gold_sleeve(p: dict) -> str:
    return f'''"""gold 解（cadquery 套筒/环形件）。判分参考预计算用；模型不可见。"""
import cadquery as cq

OD = {p["OD"]!r}
BORE_D = {p["ID"]!r}
H = {p["h"]!r}

part = cq.Workplane("XY").circle(OD / 2.0).circle(BORE_D / 2.0).extrude(H)
cq.exporters.export(part.val(), "part.step")
'''


def _gold_shaft(p: dict) -> str:
    segs = ", ".join(f"({d!r}, {l!r})" for d, l in p["segments"])
    return f'''"""gold 解（cadquery 阶梯轴+中心通孔）。判分参考预计算用；模型不可见。"""
import cadquery as cq

SEGMENTS = [{segs}]
BORE_D = {p["bore_d"]!r}

part = cq.Workplane("XY")
_z = 0.0
for _d, _l in SEGMENTS:
    _seg = cq.Workplane("XY").workplane(offset=_z).circle(_d / 2.0).extrude(_l)
    part = _seg if _z == 0.0 else part.union(_seg)
    _z += _l
part = part.faces(">Z").workplane().circle(BORE_D / 2.0).cutThruAll()
cq.exporters.export(part.val(), "part.step")
'''


def _gold_bossplate(p: dict) -> str:
    return f'''"""gold 解（cadquery 带凸台底板）。判分参考预计算用；模型不可见。"""
import cadquery as cq

L = {p["L"]!r}
W = {p["W"]!r}
T = {p["t"]!r}
BOSS_D = {p["boss_d"]!r}
BOSS_H = {p["boss_h"]!r}
HOLE_D = {p["hole_d"]!r}
INSET = {p["hole_inset"]!r}

part = (cq.Workplane("XY").rect(L, W).extrude(T)
        .faces(">Z").workplane().circle(BOSS_D / 2.0).extrude(BOSS_H)
        .faces(">Z").workplane()
        .pushPoints([(-L / 2.0 + INSET, -W / 2.0 + INSET),
                     (L / 2.0 - INSET, -W / 2.0 + INSET),
                     (-L / 2.0 + INSET, W / 2.0 - INSET),
                     (L / 2.0 - INSET, W / 2.0 - INSET)])
        .circle(HOLE_D / 2.0).cutThruAll())
cq.exporters.export(part.val(), "part.step")
'''


# ---------------------------------------------------------------- 题面

def _fmt(x: float) -> str:
    return f"{x:g}"


def _prompt_flange(p: dict) -> str:
    r_hole, r_rim = p["hole_d"] / 2.0, p["plate_d"] / 2.0
    body = (
        f"# Circular flange with bolt-hole ring\n\n"
        f"Model a circular flange as a single solid in cadquery with these exact "
        f"dimensions (mm):\n"
        f"- Flange disc: outer diameter {_fmt(p['plate_d'])}, thickness "
        f"{_fmt(p['thickness'])}, axis along Z, centered on the origin in the XY "
        f"plane, base face at z=0.\n"
        f"- Bolt holes: {p['n_holes']} through holes of diameter "
        f"{_fmt(p['hole_d'])} on a bolt-circle diameter (PCD) of {_fmt(p['pcd'])}, "
        f"evenly spaced with the first hole on the +X axis, hole axes parallel to Z, "
        f"through the full thickness.\n"
        f"- No fillets, chamfers, counterbores or any other features.\n\n")
    iface = (f"exactly {p['n_holes']} cylindrical faces of radius {_fmt(r_hole)} "
             f"(bolt holes) and exactly 1 cylindrical face of radius "
             f"{_fmt(r_rim)} (rim)")
    return body + _PROMPT_TAIL.format(tol=f"{REL_TOL:.0%}", iface=iface)


def _prompt_plate(p: dict) -> str:
    r_hole, r_corner = p["hole_d"] / 2.0, p["corner_r"]
    hx, hy = p["L"] / 2.0 - p["hole_inset"], p["W"] / 2.0 - p["hole_inset"]
    body = (
        f"# Rectangular plate with corner fillets and bolt holes\n\n"
        f"Model a rectangular plate as a single solid in cadquery with these exact "
        f"dimensions (mm):\n"
        f"- Plate: {_fmt(p['L'])} (X) x {_fmt(p['W'])} (Y) x {_fmt(p['t'])} (Z), "
        f"centered on the origin in XY, base face at z=0, thickness along Z.\n"
        f"- All four vertical (Z-parallel) edges filleted with radius "
        f"{_fmt(p['corner_r'])}.\n"
        f"- Four through holes of diameter {_fmt(p['hole_d'])}, axes parallel to Z, "
        f"through the full thickness, centered at (+/-{_fmt(hx)}, +/-{_fmt(hy)}).\n"
        f"- No other features.\n\n")
    iface = (f"exactly 4 cylindrical faces of radius {_fmt(r_hole)} (holes) and "
             f"exactly 4 cylindrical faces of radius {_fmt(r_corner)} (edge fillets)")
    return body + _PROMPT_TAIL.format(tol=f"{REL_TOL:.0%}", iface=iface)


def _prompt_lbracket(p: dict) -> str:
    hx = p["t"] + (p["leg_x"] - p["t"]) / 2.0
    vz = p["t"] + (p["H"] - p["t"]) / 2.0
    wy = p["width"] / 2.0
    body = (
        f"# L-bracket with inner fillet and leg holes\n\n"
        f"Model an L-angle bracket as a single solid in cadquery with these exact "
        f"dimensions (mm):\n"
        f"- Horizontal leg: length {_fmt(p['leg_x'])} along +X (x from 0 to "
        f"{_fmt(p['leg_x'])}), thickness {_fmt(p['t'])} (z from 0 to "
        f"{_fmt(p['t'])}).\n"
        f"- Vertical leg: height {_fmt(p['H'])} along +Z (z from 0 to "
        f"{_fmt(p['H'])}), thickness {_fmt(p['t'])} (x from 0 to {_fmt(p['t'])}).\n"
        f"- Both legs share width {_fmt(p['width'])} along +Y (y from 0 to "
        f"{_fmt(p['width'])}); outer corners sharp.\n"
        f"- Inner concave fillet of radius {_fmt(p['fillet_r'])} where the two legs "
        f"meet (tangent to the top face of the horizontal leg and to the inner face "
        f"of the vertical leg).\n"
        f"- One through hole of diameter {_fmt(p['hole_d'])} in each leg: "
        f"horizontal-leg hole axis parallel to Z centered at "
        f"(x={_fmt(hx)}, y={_fmt(wy)}); vertical-leg hole axis parallel to X "
        f"centered at (y={_fmt(wy)}, z={_fmt(vz)}).\n"
        f"- No other features.\n\n")
    iface = (f"exactly 2 cylindrical faces of radius {_fmt(p['hole_d'] / 2.0)} "
             f"(leg holes) and exactly 1 cylindrical face of radius "
             f"{_fmt(p['fillet_r'])} (inner fillet)")
    return body + _PROMPT_TAIL.format(tol=f"{REL_TOL:.0%}", iface=iface)


def _prompt_sleeve(p: dict) -> str:
    body = (
        f"# Plain sleeve (annular ring)\n\n"
        f"Model a hollow cylindrical sleeve as a single solid in cadquery with these "
        f"exact dimensions (mm):\n"
        f"- Outer diameter {_fmt(p['OD'])}, coaxial through bore of diameter "
        f"{_fmt(p['ID'])}, height {_fmt(p['h'])} along Z.\n"
        f"- Centered on the origin in the XY plane, base face at z=0; no chamfers, "
        f"fillets or other features.\n\n")
    iface = (f"exactly 1 cylindrical face of radius {_fmt(p['OD'] / 2.0)} (outer) "
             f"and exactly 1 cylindrical face of radius {_fmt(p['ID'] / 2.0)} (bore)")
    return body + _PROMPT_TAIL.format(tol=f"{REL_TOL:.0%}", iface=iface)


def _prompt_shaft(p: dict) -> str:
    segs = p["segments"]
    z = 0.0
    seg_lines = []
    for i, (d, l) in enumerate(segs, 1):
        seg_lines.append(f"- Segment {i}: diameter {_fmt(d)}, from z={_fmt(z)} to "
                         f"z={_fmt(z + l)}")
        z += l
    seg_txt = "\n".join(seg_lines)
    body = (
        f"# Stepped shaft with central bore\n\n"
        f"Model a stepped shaft as a single solid in cadquery with these exact "
        f"dimensions (mm):\n"
        f"- Three coaxial cylindrical segments stacked along +Z, all centered on the "
        f"Z axis:\n{seg_txt}\n"
        f"- Central through bore of diameter {_fmt(p['bore_d'])}, coaxial along Z, "
        f"through the full length.\n"
        f"- No chamfers, fillets or other features.\n\n")
    iface = (f"exactly 1 cylindrical face of radius {_fmt(p['bore_d'] / 2.0)} (bore) "
             + " and exactly 1 cylindrical face of each radius "
             + ", ".join(_fmt(d / 2.0) for d, _ in segs)
             + " (shaft steps)")
    return body + _PROMPT_TAIL.format(tol=f"{REL_TOL:.0%}", iface=iface)


def _prompt_bossplate(p: dict) -> str:
    hx, hy = p["L"] / 2.0 - p["hole_inset"], p["W"] / 2.0 - p["hole_inset"]
    body = (
        f"# Base plate with central boss and bolt holes\n\n"
        f"Model a base plate with a central cylindrical boss as a single solid in "
        f"cadquery with these exact dimensions (mm):\n"
        f"- Base plate: {_fmt(p['L'])} (X) x {_fmt(p['W'])} (Y) x {_fmt(p['t'])} (Z), "
        f"centered on the origin in XY, base face at z=0.\n"
        f"- Cylindrical boss on the top face of the plate: diameter "
        f"{_fmt(p['boss_d'])}, height {_fmt(p['boss_h'])}, axis along Z centered at "
        f"the plate center (boss top face at z={_fmt(p['t'] + p['boss_h'])}).\n"
        f"- Four through holes in the plate of diameter {_fmt(p['hole_d'])}, axes "
        f"parallel to Z, through the plate thickness only, centered at "
        f"(+/-{_fmt(hx)}, +/-{_fmt(hy)}).\n"
        f"- No fillets, chamfers or other features.\n\n")
    iface = (f"exactly 4 cylindrical faces of radius {_fmt(p['hole_d'] / 2.0)} "
             f"(bolt holes) and exactly 1 cylindrical face of radius "
             f"{_fmt(p['boss_d'] / 2.0)} (boss)")
    return body + _PROMPT_TAIL.format(tol=f"{REL_TOL:.0%}", iface=iface)


# ---------------------------------------------------------------- 族定义

def task_defs() -> list[dict]:
    T: list[dict] = []

    def add(tid, family, params, gold_fn, prompt_fn, check_specs, expect_counts,
            analytic_vol, feasible):
        T.append({"tid": tid, "family": family, "params": params,
                  "gold": gold_fn(params), "prompt": prompt_fn(params),
                  "check_specs": check_specs, "expect_counts": expect_counts,
                  "analytic_volume": analytic_vol(params), "feasible": feasible})

    # ---- 族 1：圆法兰 + 螺栓孔环 ----
    def _flange_feasible(p):
        assert p["pcd"] / 2.0 + p["hole_d"] / 2.0 <= p["plate_d"] / 2.0 - 3.0, "孔-外缘间距"
        chord = p["pcd"] * math.sin(math.pi / p["n_holes"])
        assert chord > p["hole_d"] + 4.0, "相邻孔间距"
        assert p["n_holes"] >= 3
    _F1 = [
        ("cg_flange_001", dict(plate_d=100.0, thickness=10.0, n_holes=6, hole_d=8.0, pcd=76.0)),
        ("cg_flange_002", dict(plate_d=120.0, thickness=12.0, n_holes=8, hole_d=10.0, pcd=94.0)),
        ("cg_flange_003", dict(plate_d=140.0, thickness=10.0, n_holes=12, hole_d=8.0, pcd=116.0)),
        ("cg_flange_004", dict(plate_d=90.0, thickness=8.0, n_holes=4, hole_d=9.0, pcd=68.0)),
    ]
    for tid, p in _F1:
        add(tid, "flange", p, _gold_flange, _prompt_flange,
            [{"check": "n_cyl_faces_with_radius", "radius": p["hole_d"] / 2.0},
             {"check": "n_cyl_faces_with_radius", "radius": p["plate_d"] / 2.0},
             {"check": "n_faces_total"}],
            {f"cyl@{p['hole_d'] / 2.0:g}": p["n_holes"], f"cyl@{p['plate_d'] / 2.0:g}": 1},
            lambda q: math.pi / 4.0 * (q["plate_d"] ** 2 - q["n_holes"] * q["hole_d"] ** 2)
                      * q["thickness"],
            _flange_feasible)

    # ---- 族 2：矩形板 + 四角孔 + 边倒圆 ----
    def _plate_feasible(p):
        assert p["hole_inset"] >= p["corner_r"] + p["hole_d"] / 2.0 + 3.0, "孔-倒圆间距"
        assert p["hole_inset"] + p["hole_d"] / 2.0 < min(p["L"], p["W"]) / 2.0, "孔-边间距"
        assert 2.0 * p["corner_r"] < min(p["L"], p["W"]), "倒圆半径过大"
    _F2 = [
        ("cg_plate_001", dict(L=120.0, W=80.0, t=10.0, hole_d=8.0, corner_r=10.0, hole_inset=18.0)),
        ("cg_plate_002", dict(L=100.0, W=60.0, t=8.0, hole_d=6.0, corner_r=8.0, hole_inset=15.0)),
        ("cg_plate_003", dict(L=160.0, W=100.0, t=12.0, hole_d=10.0, corner_r=12.0, hole_inset=22.0)),
        ("cg_plate_004", dict(L=90.0, W=70.0, t=6.0, hole_d=7.0, corner_r=9.0, hole_inset=16.0)),
    ]
    for tid, p in _F2:
        add(tid, "plate", p, _gold_plate, _prompt_plate,
            [{"check": "n_cyl_faces_with_radius", "radius": p["hole_d"] / 2.0},
             {"check": "n_cyl_faces_with_radius", "radius": p["corner_r"]},
             {"check": "n_faces_total"}],
            {f"cyl@{p['hole_d'] / 2.0:g}": 4, f"cyl@{p['corner_r']:g}": 4},
            lambda q: (q["L"] * q["W"] - (4.0 - math.pi) * q["corner_r"] ** 2) * q["t"]
                      - 4.0 * math.pi * (q["hole_d"] / 2.0) ** 2 * q["t"],
            _plate_feasible)

    # ---- 族 3：L 角支架（两腿+内圆角+腿上孔） ----
    def _lbr_feasible(p):
        t, r = p["t"], p["fillet_r"]
        assert t + r < min(p["leg_x"], p["H"]) - 2.0, "内圆角超出腿长"
        hx = t + (p["leg_x"] - t) / 2.0
        vz = t + (p["H"] - t) / 2.0
        assert hx - p["hole_d"] / 2.0 > t + 2.0 and hx + p["hole_d"] / 2.0 < p["leg_x"] - 2.0
        assert vz - p["hole_d"] / 2.0 > t + r + 2.0 and vz + p["hole_d"] / 2.0 < p["H"] - 2.0
        assert p["hole_d"] < p["width"] - 4.0, "孔径 vs 腿宽"
    _F3 = [
        ("cg_lbracket_001", dict(leg_x=80.0, H=60.0, t=10.0, width=40.0, fillet_r=12.0, hole_d=9.0)),
        ("cg_lbracket_002", dict(leg_x=100.0, H=70.0, t=12.0, width=50.0, fillet_r=10.0, hole_d=10.0)),
        ("cg_lbracket_003", dict(leg_x=60.0, H=50.0, t=8.0, width=30.0, fillet_r=8.0, hole_d=8.0)),
        ("cg_lbracket_004", dict(leg_x=120.0, H=80.0, t=10.0, width=60.0, fillet_r=15.0, hole_d=10.0)),
    ]
    for tid, p in _F3:
        add(tid, "lbracket", p, _gold_lbracket, _prompt_lbracket,
            [{"check": "n_cyl_faces_with_radius", "radius": p["hole_d"] / 2.0},
             {"check": "n_cyl_faces_with_radius", "radius": p["fillet_r"]},
             {"check": "n_faces_total"}],
            {f"cyl@{p['hole_d'] / 2.0:g}": 2, f"cyl@{p['fillet_r']:g}": 1},
            lambda q: (q["leg_x"] * q["t"] + (q["H"] - q["t"]) * q["t"]
                       + q["fillet_r"] ** 2 * (1.0 - math.pi / 4.0)) * q["width"]
                      - 2.0 * math.pi * (q["hole_d"] / 2.0) ** 2 * q["t"],
            _lbr_feasible)

    # ---- 族 4：套筒/环形件 ----
    def _sleeve_feasible(p):
        assert p["ID"] + 10.0 <= p["OD"], "壁厚 >=5mm"
        assert p["h"] >= 5.0
    _F4 = [
        ("cg_sleeve_001", dict(OD=60.0, ID=40.0, h=20.0)),
        ("cg_sleeve_002", dict(OD=80.0, ID=50.0, h=25.0)),
        ("cg_sleeve_003", dict(OD=100.0, ID=70.0, h=30.0)),
    ]
    for tid, p in _F4:
        add(tid, "sleeve", p, _gold_sleeve, _prompt_sleeve,
            [{"check": "n_cyl_faces_with_radius", "radius": p["OD"] / 2.0},
             {"check": "n_cyl_faces_with_radius", "radius": p["ID"] / 2.0},
             {"check": "n_faces_total"}],
            {f"cyl@{p['OD'] / 2.0:g}": 1, f"cyl@{p['ID'] / 2.0:g}": 1},
            lambda q: math.pi / 4.0 * (q["OD"] ** 2 - q["ID"] ** 2) * q["h"],
            _sleeve_feasible)

    # ---- 族 5：阶梯轴（各段直径/长度，中心通孔） ----
    def _shaft_feasible(p):
        ds = [d for d, _ in p["segments"]]
        assert ds[0] > ds[1] > ds[2] > p["bore_d"] + 4.0, "直径单调且大于孔"
        assert all(l >= 10.0 for _, l in p["segments"])
    _F5 = [
        ("cg_shaft_001", dict(segments=[(40.0, 30.0), (28.0, 25.0), (18.0, 20.0)], bore_d=8.0)),
        ("cg_shaft_002", dict(segments=[(50.0, 35.0), (36.0, 30.0), (22.0, 22.0)], bore_d=10.0)),
        ("cg_shaft_003", dict(segments=[(60.0, 40.0), (44.0, 28.0), (30.0, 25.0)], bore_d=12.0)),
        ("cg_shaft_004", dict(segments=[(36.0, 25.0), (24.0, 30.0), (14.0, 18.0)], bore_d=6.0)),
    ]
    for tid, p in _F5:
        seg_specs = [{"check": "n_cyl_faces_with_radius", "radius": d / 2.0}
                     for d, _ in p["segments"]]
        expect = {f"cyl@{d / 2.0:g}": 1 for d, _ in p["segments"]}
        add(tid, "shaft", p, _gold_shaft, _prompt_shaft,
            [{"check": "n_cyl_faces_with_radius", "radius": p["bore_d"] / 2.0}]
            + seg_specs + [{"check": "n_faces_total"}],
            {**expect, f"cyl@{p['bore_d'] / 2.0:g}": 1},
            lambda q: math.pi / 4.0 * sum((d ** 2 - q["bore_d"] ** 2) * l
                                          for d, l in q["segments"]),
            _shaft_feasible)

    # ---- 族 6：带凸台的底板 ----
    def _boss_feasible(p):
        assert p["hole_inset"] >= p["hole_d"] / 2.0 + 3.0, "孔-边间距"
        hx = p["L"] / 2.0 - p["hole_inset"]
        hy = p["W"] / 2.0 - p["hole_inset"]
        assert math.hypot(hx, hy) - p["boss_d"] / 2.0 - p["hole_d"] / 2.0 >= 4.0, "孔-凸台间距"
        assert p["boss_d"] / 2.0 + 4.0 <= min(p["L"], p["W"]) / 2.0, "凸台-边间距"
    _F6 = [
        ("cg_bossplate_001", dict(L=90.0, W=60.0, t=10.0, boss_d=30.0, boss_h=20.0,
                                  hole_d=8.0, hole_inset=12.0)),
        ("cg_bossplate_002", dict(L=110.0, W=70.0, t=12.0, boss_d=40.0, boss_h=25.0,
                                  hole_d=9.0, hole_inset=14.0)),
        ("cg_bossplate_003", dict(L=80.0, W=80.0, t=8.0, boss_d=25.0, boss_h=15.0,
                                  hole_d=7.0, hole_inset=12.0)),
    ]
    for tid, p in _F6:
        add(tid, "bossplate", p, _gold_bossplate, _prompt_bossplate,
            [{"check": "n_cyl_faces_with_radius", "radius": p["hole_d"] / 2.0},
             {"check": "n_cyl_faces_with_radius", "radius": p["boss_d"] / 2.0},
             {"check": "n_faces_total"}],
            {f"cyl@{p['hole_d'] / 2.0:g}": 4, f"cyl@{p['boss_d'] / 2.0:g}": 1},
            lambda q: q["L"] * q["W"] * q["t"] + math.pi * (q["boss_d"] / 2.0) ** 2 * q["boss_h"]
                      - 4.0 * math.pi * (q["hole_d"] / 2.0) ** 2 * q["t"],
            _boss_feasible)

    return T


# ---------------------------------------------------------------- gold 执行

def run_gold(gold_code: str, workdir: Path) -> dict:
    """干净目录执行 gold（.venv-cad）导出 part.step，返回同口径测量值。"""
    script = workdir / "gold.py"
    script.write_text(gold_code, encoding="utf-8")
    env = dict(os.environ)
    env["MPLCONFIGDIR"] = str(workdir)
    r = subprocess.run([str(_VENV_PY), str(script)], cwd=workdir,
                       capture_output=True, text=True, timeout=600, env=env)
    if r.returncode != 0:
        raise RuntimeError(f"gold 失败: {r.stderr[-800:]}")
    step = workdir / "part.step"
    if not step.exists():
        raise RuntimeError("gold 未导出 part.step")
    m = measure_step(step)
    if not m["brep_valid"] or not m["volume_mm3"] > 0:
        raise RuntimeError(f"gold 制品无效: valid={m['brep_valid']} vol={m['volume_mm3']}")
    return m


def build_refs_and_checks(t: dict, m: dict) -> tuple[dict, list[dict]]:
    """测量值 -> reference.values + grader.interface_checks（含防漂移断言）。"""
    for key, expect in t["expect_counts"].items():
        radius = float(key.split("@")[1])
        got = sum(1 for r in m["cyl_radii"]
                  if abs(r - radius) <= 0.01 * radius)
        assert got == expect, f"{t['tid']} {key}: 期望 {expect} 实测 {got}（建模/测量器漂移）"
    assert not m["volume_mm3"] > 0 or abs(
        m["volume_mm3"] - t["analytic_volume"]) <= 1e-3 * t["analytic_volume"], \
        f"{t['tid']} 体积与闭式解差 >0.1%: {m['volume_mm3']} vs {t['analytic_volume']}"

    checks: list[dict] = []
    refs: dict = {"volume_mm3": m["volume_mm3"],
                  "bbox_len_x": m["bbox_len_x"],
                  "bbox_len_y": m["bbox_len_y"],
                  "bbox_len_z": m["bbox_len_z"],
                  "n_faces_total": m["n_faces"]}
    for spec in t["check_specs"]:
        if spec["check"] == "n_cyl_faces_with_radius":
            radius = float(spec["radius"])
            n = sum(1 for r in m["cyl_radii"] if abs(r - radius) <= 0.01 * radius)
            checks.append({"check": "n_cyl_faces_with_radius", "radius": radius,
                           "expect": n})
            refs[f"n_cyl_faces_radius_{radius:g}"] = n
        else:
            checks.append({"check": "n_faces_total", "expect": m["n_faces"]})
    return refs, checks


def _spec_for(t: dict, refs: dict, checks: list[dict], prompt_sha: str) -> dict:
    return {
        "id": t["tid"],
        "registry_id": "cadgen.local_validity",
        "domain": "cad_design",
        "task_type": "design_artifact",
        "model_profile": "plain_llm",
        "assets_revision": ASSETS_REVISION,
        "environment_digest": "computed-at-runtime",
        "hidden": False,
        "allowed_tools": ["python", "cadquery"],
        "input": {"prompt_file": f"tasks/cadgen.local_validity/{t['tid']}.md",
                  "prompt_sha256": prompt_sha, "assets": []},
        "output_contract": ["part.step"],
        "reference": {
            "source": "gold 脚本预计算（自建参数化 CAD 任务，cadquery 2.8.0 + OCP 本地测量）",
            "revision": ASSETS_REVISION, "values": refs, "rel_tol": REL_TOL,
            "uncertainty_note": "确定性几何；容差覆盖 STEP 精度与建模口径差（1e-7 量级）",
        },
        "grader": {
            "answer_format": "code",
            "exec_kind": "cadgen_local_validity",
            "validity_gate": True,
            "numeric_rel_tol": REL_TOL,
            "interface_checks": checks,
            "oracle_source": f"data/cadgen/local_validity/gold/{t['tid']}.py",
            "sandbox": {"banned": "network/process/ctypes", "isolated_interpreter": True},
        },
        "scoring": {
            "weights": {"physics": 0.5, "requirements": 0.5, "objective": 0.0,
                        "robustness": 0.0},
            "note": ("physics=体积+包围盒三边相对误差命中均值（各 1/4，1% 容差）；"
                     "requirements=interface_checks 通过率（圆柱面数 ±1%/总面数精确）"),
        },
        "limits": {"cpu": 4, "memory_gb": 8, "wall_clock_s": 300, "attempts": 3},
        "license_provenance": {
            "source": "自建参数化任务（未使用 CADGenBench 输入/GT）+ cadquery (Apache-2.0)",
            "license": "任务文本与 gold 自建；cadquery Apache-2.0",
            "status": "confirmed-repo", "revision": ASSETS_REVISION,
            "mirror_allowed": True,
            "attribution": "cadquery, github.com/CadQuery/cadquery（仅作为建模库依赖）",
        },
    }


_PROVENANCE = """# cadgen.local_validity 数据来源与判分边界（PROVENANCE）

- 定位：**自建参数化任务**（受 CADGenBench「本地可复现子集」定位启发；
  registry `cadgen.local_validity`，adapter `design_artifact`，adapters/README.md §4）。
- **未镜像其 ODC-BY 输入**：题面/尺寸全部由 runners/gen_tasks_cadgen.py 的
  参数化族生成，不使用 CADGenBench 官方 text+image 输入与输入制品。
- **未用其私有 GT**：CADGenBench 服务端相似度分数与私有 ground truth
  （cadgenbench-data-gt 空仓）不可得也不纳入——私有 GT 相似度分数不得混入本地分数。
- **判分 100% 本地可复现**：
  - STEP 可解析（STEPControl_Reader）+ B-Rep 有效（BRepCheck_Analyzer）；
  - 体积/包络（GProp / Bnd_Box）对 gold 预计算参考的相对误差（1%）；
  - 接口几何（TopExp 遍历圆柱面数/半径，±1%）与总面数（精确）；
  - 生成代码可重复执行复现同一制品（体积/包围盒 1e-6 相对一致）。
- 环境：仓库根 `.venv-cad`（Python 3.12.13 + cadquery 2.8.0 + OCP wheel），
  assets_revision `cadgen-local@selfbuilt-2026-08-21+cadquery2.8.0`。
- gold 全量预计算锁定：每题 `gold/<tid>.py` 在干净目录执行导出 part.step，
  测量结果（与判分器同一实现 `runners/design_artifact.measure_step`）落
  `references/<tid>.json` 并内嵌任务 YAML `reference.values`。
- 生成器幂等校验：`.venv-cad/bin/python -m runners.gen_tasks_cadgen --check`。

## 任务族（6 族 22 题，同族变体体积互差 >2%）

| 族 | 题数 | 参数 |
| --- | --- | --- |
| 圆法兰+螺栓孔环 cg_flange_* | 4 | plate_d, thickness, n_holes, hole_d, pcd |
| 矩形板+四角孔+边倒圆 cg_plate_* | 4 | L, W, t, hole_d, corner_r, hole_inset |
| L 角支架 cg_lbracket_* | 4 | leg_x, H, t, width, fillet_r, hole_d |
| 套筒/环形件 cg_sleeve_* | 3 | OD, ID, h |
| 阶梯轴+中心孔 cg_shaft_* | 4 | segments[(d,l)x3], bore_d |
| 带凸台底板 cg_bossplate_* | 3 | L, W, t, boss_d, boss_h, hole_d, hole_inset |
"""


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--check", action="store_true")
    ap.add_argument("--force-refs", action="store_true")
    args = ap.parse_args()

    tasks = task_defs()

    # 可行性 + 族内体积互差 >2%（防简并）——gen/check 两种模式都断言
    by_fam: dict[str, list[float]] = {}
    for t in tasks:
        t["feasible"](t["params"])
        by_fam.setdefault(t["family"], []).append(t["analytic_volume"])
    for fam, vols in by_fam.items():
        for i in range(len(vols)):
            for j in range(i + 1, len(vols)):
                lo, hi = sorted((vols[i], vols[j]))
                assert (hi - lo) / lo > VOL_SPREAD, \
                    f"族 {fam} 变体体积简并: {lo:.3f} vs {hi:.3f}"

    (DATA / "gold").mkdir(parents=True, exist_ok=True)
    (DATA / "references").mkdir(parents=True, exist_ok=True)
    TASKS_DIR.mkdir(parents=True, exist_ok=True)

    drift = []
    for t in tasks:
        gold_path = DATA / "gold" / f"{t['tid']}.py"
        ref_path = DATA / "references" / f"{t['tid']}.json"
        yaml_path = TASKS_DIR / f"{t['tid']}.yaml"
        md_path = TASKS_DIR / f"{t['tid']}.md"

        if args.check:
            for p, want in ((gold_path, t["gold"]), (md_path, t["prompt"])):
                if not p.exists() or p.read_text(encoding="utf-8") != want:
                    drift.append(str(p.relative_to(BENCH)))
            refs = None
            if not ref_path.exists():
                drift.append(f"{ref_path.relative_to(BENCH)} (missing)")
            else:
                try:
                    refs = json.loads(ref_path.read_text(encoding="utf-8"))
                except Exception:  # noqa: BLE001
                    drift.append(f"{ref_path.relative_to(BENCH)} (corrupt)")
            if refs is not None:
                try:
                    checks = _checks_from_refs(t, refs)
                    want_yaml = yaml.safe_dump(
                        _spec_for(t, refs, checks,
                                  hashlib.sha256(t["prompt"].encode()).hexdigest()),
                        sort_keys=False, allow_unicode=True)
                    if not yaml_path.exists() or \
                            yaml_path.read_text(encoding="utf-8") != want_yaml:
                        drift.append(str(yaml_path.relative_to(BENCH)))
                except KeyError as e:
                    drift.append(f"{ref_path.relative_to(BENCH)} (missing key {e})")
            continue

        gold_path.write_text(t["gold"], encoding="utf-8")

        if args.force_refs or not ref_path.exists():
            with tempfile.TemporaryDirectory() as td:
                m = run_gold(t["gold"], Path(td))
            refs, checks = build_refs_and_checks(t, m)
            refs = {k: refs[k] for k in sorted(refs)}   # 与落盘 JSON 同序（幂等）
            ref_path.write_text(json.dumps(refs, indent=1, sort_keys=True),
                                encoding="utf-8")
        else:
            refs = json.loads(ref_path.read_text(encoding="utf-8"))
            checks = _checks_from_refs(t, refs)

        prompt_sha = hashlib.sha256(t["prompt"].encode()).hexdigest()
        yaml_path.write_text(
            yaml.safe_dump(_spec_for(t, refs, checks, prompt_sha),
                           sort_keys=False, allow_unicode=True), encoding="utf-8")
        md_path.write_text(t["prompt"], encoding="utf-8")
        print(f"[gen] {t['tid']}: vol={refs['volume_mm3']:.3f} "
              f"bbox=({refs['bbox_len_x']:.3f},{refs['bbox_len_y']:.3f},"
              f"{refs['bbox_len_z']:.3f}) n_faces={refs['n_faces_total']} "
              f"checks={len(checks)}")

    if not args.check:
        (DATA / "PROVENANCE.md").write_text(_PROVENANCE, encoding="utf-8")
        print(f"[gen] {len(tasks)} tasks -> {TASKS_DIR}；PROVENANCE -> {DATA}")
        return 0

    if drift:
        print(f"[check] 漂移 {len(drift)} 处: {drift}")
        return 1
    print(f"[check] {len(tasks)} 个任务全部一致（gold/yaml/md/references）")
    return 0


def _checks_from_refs(t: dict, refs: dict) -> list[dict]:
    """从磁盘 references 重建 interface_checks（幂等重建，不重跑 gold）。"""
    checks = []
    for spec in t["check_specs"]:
        if spec["check"] == "n_cyl_faces_with_radius":
            radius = float(spec["radius"])
            checks.append({"check": "n_cyl_faces_with_radius", "radius": radius,
                           "expect": refs[f"n_cyl_faces_radius_{radius:g}"]})
        else:
            checks.append({"check": "n_faces_total", "expect": refs["n_faces_total"]})
    return checks


if __name__ == "__main__":
    raise SystemExit(main())
