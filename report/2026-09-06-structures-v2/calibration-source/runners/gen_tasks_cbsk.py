#!/usr/bin/env python3
"""gen_tasks_cbsk.py — cadbench_seldon.sketch_lite 任务生成 + gold + 判分自检。

改编协议（窄路 A，2026-08-25 用户裁决）：Seldon CADBench-Hard 的 5 道 proc 草图题
（空文档起步、题面坐标全给）按本仓库协议改编为 cadquery 脚本任务；另加 10 题自建
同族变体，共 15 题。GT 一手源 = 题面几何规格（"They describe the required final
geometry"）；answer.f3d 不可解析（Fusion 私有），后续经 tools/fusion_export_gt.py
导出后作交叉核验（非判分依赖）。

协议：模型写单个 ```python（cadquery）——在指定 origin 平面构造题面规定的 2D 曲线
（仅曲线零实体），导出 sketch.step。判分（design_artifact sketch_2d 模式）：
  gate：静态检查 → 双跑可执行 → sketch.step 存在 → STEP 可解析出边且共面
        → 双跑实体集一致
  physics = 实体级匹配（线段端点无序/样条拟合点在曲线上；多余实体惩罚）
  requirements = 实体数精确 + 闭合环数精确 + 平面规格

平面映射（本仓库口径，题面明示）：YZ → 全局 (0,u,v)，法向 +X；XZ → (u,0,v)，法向 -Y。

用法：.venv-cad/bin/python -m runners.gen_tasks_cbsk   （幂等；生成后跑 gold 全链自检）
"""
from __future__ import annotations

import hashlib
import json
import math
import subprocess
import sys
import tempfile
from pathlib import Path

BENCH = Path(__file__).resolve().parent.parent
RID = "cadbench_seldon.sketch_lite"
TASKS_DIR = BENCH / "tasks" / RID
GOLD_DIR = BENCH / "data" / "cadbench-seldon" / "sketch_lite" / "gold"
REV = "cbsk@adapted-2026-08-25+ccx-side-none"

PLANES = {  # 平面名 → (法向, 局部(u,v)→全局 3D 映射)
    "YZ": ((1.0, 0.0, 0.0), lambda u, v: (0.0, u, v)),
    "XZ": ((0.0, -1.0, 0.0), lambda u, v: (u, 0.0, v)),
}


# ---------------------------------------------------------------- 任务定义

def _polygon_lines(center, r, n, deg0):
    cx, cy = center
    pts = []
    for i in range(n):
        th = math.radians(deg0 + i * 360.0 / n)
        pts.append((round(cx + r * math.cos(th), 6), round(cy + r * math.sin(th), 6)))
    return [(pts[i], pts[(i + 1) % n]) for i in range(n)]


def tasks_def():
    T = []

    def add(tid, fam, plane, lines, splines, closed, src):
        T.append(dict(tid=tid, fam=fam, plane=plane, lines=lines,
                      splines=splines, closed=closed, source=src,
                      n_ent=len(lines) + len(splines)))

    # ---- 改编 5 题（源：CADBench-Hard proc_*，CC-BY-4.0，几何规格取题面原文） ----
    add("cbsk_chain_s01", "chain", "YZ",
        [((-13, -19), (-32, -19)), ((-32, -19), (-32, -37)),
         ((-32, -37), (-43, -37)), ((-43, -37), (-43, -49))],
        [], 0, "proc_connected_lines_14e1ddda38c3")
    add("cbsk_polygon_s01", "polygon", "YZ",
        _polygon_lines((-7, 11), 24.0, 8, 296.0),
        [], 1, "proc_polygon_6a15b2b2b55d")
    add("cbsk_spline_s01", "spline", "XZ",
        [((25, 0), (4, -24)), ((4, -24), (-25, 0))],
        [[(-25, 0), (-8.333333, 24), (8.333333, 24), (25, 0)]],
        1, "proc_spline_profile_29ee4d0d9bf2")
    add("cbsk_spline_s02", "spline", "XZ",
        [((34, 0), (6, -20)), ((6, -20), (-34, 0))],
        [[(-34, 0), (-11.333333, 17), (11.333333, 32), (34, 0)]],
        1, "proc_spline_profile_617986cd5abf")
    add("cbsk_spline_s03", "spline", "XZ",
        [((30, 0), (-6, -19)), ((-6, -19), (-30, 0))],
        [[(-30, 0), (-18, 30), (-6, 23), (6, 31), (18, 15), (30, 0)]],
        1, "proc_spline_profile_9d745c7e4ed3")

    # ---- 自建 10 题（同族参数化变体，GT 解析计算） ----
    add("cbsk_chain_b01", "chain", "YZ",
        [((-5, 8), (14, 8)), ((14, 8), (14, 22)), ((14, 22), (-2, 22))],
        [], 0, None)
    add("cbsk_chain_b02", "chain", "YZ",
        [((6, 3), (6, 25)), ((6, 25), (-13, 25)), ((-13, 25), (-13, 41)),
         ((-13, 41), (28, 41)), ((28, 41), (28, 53))],
        [], 0, None)
    add("cbsk_chain_b03", "chain", "YZ",
        [((0, 0), (19, 0)), ((19, 0), (19, 14)), ((19, 14), (7, 14)),
         ((7, 14), (7, 32)), ((7, 32), (-15, 32)), ((-15, 32), (-15, -9))],
        [], 0, None)
    add("cbsk_chain_b04", "chain", "YZ",
        [((-8, -12), (21, -12)), ((21, -12), (21, 5)), ((21, 5), (9, 5)),
         ((9, 5), (9, 26)), ((9, 26), (31, 26)), ((31, 26), (31, 44)),
         ((31, 44), (-3, 44))],
        [], 0, None)
    add("cbsk_polygon_b01", "polygon", "YZ", _polygon_lines((5, -9), 18.0, 5, 17.0),
        [], 1, None)
    add("cbsk_polygon_b02", "polygon", "YZ", _polygon_lines((-11, -4), 30.0, 6, 203.0),
        [], 1, None)
    add("cbsk_polygon_b03", "polygon", "YZ", _polygon_lines((8, 6), 15.0, 12, 311.0),
        [], 1, None)
    add("cbsk_spline_b01", "spline", "XZ",
        [((28, 0), (0, -18)), ((0, -18), (-28, 0))],
        [[(-28, 0), (-14, 21), (0, 26), (14, 21), (28, 0)]], 1, None)
    add("cbsk_spline_b02", "spline", "XZ",
        [((32, 0), (2, -17)), ((2, -17), (-32, 0))],
        [[(-32, 0), (-19, 24), (-4, 31), (12, 26), (24, 12), (32, 0)]], 1, None)
    add("cbsk_spline_b03", "spline", "XZ",
        [((26, 0), (-4, -16)), ((-4, -16), (-26, 0))],
        [[(-26, 0), (-22, 19), (-11, 28), (0, 22), (11, 29), (22, 17), (26, 0)]],
        1, None)
    return T


# ---------------------------------------------------------------- gold 脚本

def gold_script(t) -> str:
    lines_py = []
    for a, b in t["lines"]:
        lines_py.append(f"    ({a}, {b}),")
    spline_py = []
    for sp in t["splines"]:
        pts = ", ".join(f"({u}, {v})" for u, v in sp)
        spline_py.append(f"    [{pts}],")
    spline_block = ""
    if t["splines"]:
        spline_block = ("\nSPLINES = [\n" + "\n".join(spline_py) + "\n]\n"
                        "for fit in SPLINES:\n"
                        "    edges.append(cq.Edge.makeSpline([w(u, v) for u, v in fit]))\n")
    return f'''"""gold — {t['tid']}：在 {t['plane']} 平面构造题面规定的 2D 草图并导出 sketch.step。"""
import cadquery as cq

PLANE = cq.Plane.named("{t['plane']}")


def w(u, v):
    return PLANE.toWorldCoords((u, v))


edges = []
LINES = [
{chr(10).join(lines_py)}
]
for a, b in LINES:
    edges.append(cq.Edge.makeLine(w(*a), w(*b)))
{spline_block}
cq.exporters.export(cq.Compound.makeCompound(edges), "sketch.step")
'''


# ---------------------------------------------------------------- prompt

RULES = """
## Deliverable contract

Respond with ONE complete ```python code block (cadquery only, deterministic,
self-contained, no randomness, no other files). The script must:

1. Build the sketch on cadquery plane "{plane}" — construct points via
   `P = cq.Plane.named("{plane}"); P.toWorldCoords((u, v))` so the LOCAL sketch
   coordinates below map to global {mapping}.
2. Create EXACTLY the listed curve entities and nothing else (no extra curves,
   points, construction geometry, solids, or bodies).
3. Export the curves as a compound of edges to a file named exactly
   `sketch.step` in the current directory:
   `cq.exporters.export(cq.Compound.makeCompound(edges), "sketch.step")`.
"""


def render_prompt(t) -> str:
    normal, map_fn = PLANES[t["plane"]]
    mapping = {"YZ": "(x, y, z) = (0, u, v)  [local u -> global +Y, v -> global +Z]",
               "XZ": "(x, y, z) = (u, 0, v)  [local u -> global +X, v -> global +Z]"}[t["plane"]]
    head = {"chain": f"# Open orthogonal line chain — 2D sketch ({t['plane']} plane, mm)",
            "polygon": f"# Regular polygon — 2D sketch ({t['plane']} plane, mm)",
            "spline": f"# Closed profile with fitted spline — 2D sketch ({t['plane']} plane, mm)"}[t["fam"]]
    L = [head, "",
         "All coordinates are LOCAL sketch coordinates in millimetres. Establish "
         "exact values numerically (do not approximate on a grid).", "", "## Required entities", ""]
    for i, (a, b) in enumerate(t["lines"], 1):
        L.append(f"{i}. Line from ({a[0]}, {a[1]}) to ({b[0]}, {b[1]}).")
    for i, sp in enumerate(t["splines"], len(t["lines"]) + 1):
        pts = ", ".join(f"({u}, {v})" for u, v in sp)
        L.append(f"{i}. Fitted spline through these fit points in order: {pts}."
                 " Use a smooth interpolation through the points (no kinks);"
                 " a cadquery `cq.Edge.makeSpline([...])` through the mapped points is acceptable.")
    L.append("")
    L.append(f"## Completion requirements")
    L.append(f"- Exactly {t['n_ent']} curve entities total.")
    L.append(f"- The entities must form exactly {t['closed']} closed profile(s)"
             f" ({'closed loop' if t['closed'] else 'open chain'}).")
    L.append("- All entities coplanar on the specified plane.")
    if t["fam"] == "chain":
        L.append("- Consecutive segments share truly coincident endpoints; leave the chain open.")
    if t["fam"] == "spline":
        L.append("- Junctions coincident so the profile closes exactly once.")
    L.append(RULES.format(plane=t["plane"], mapping=mapping))
    if t["fam"] == "polygon":
        # 权威参数注记（源题面口径：center/radius/n/orientation authoritative）
        L.insert(2, "_Vertex coordinates above are derived from the authoritative "
                    "parameters: regular polygon, given center, circumradius, side "
                    "count, first-vertex angle (counterclockwise from local +X)._")
    return "\n".join(L)


# ---------------------------------------------------------------- YAML

def emit_yaml(t, prompt_sha):
    normal, map_fn = PLANES[t["plane"]]
    gt_lines = [[list(map_fn(*a)), list(map_fn(*b))] for a, b in t["lines"]]
    gt_splines = [[list(map_fn(*pt)) for pt in sp] for sp in t["splines"]]
    src = (f"改编自 Seldon CADBench-Hard `{t['source']}`（CC-BY-4.0，几何规格取题面原文；"
           f"协议由 GUI 改为本仓库 cadquery 脚本制") if t["source"] else "自建（同族参数化变体）"
    lic = ("CC-BY-4.0（Seldon Technologies，署名衍生；改编协议变更如实标注）"
           if t["source"] else "self-built")
    status = "confirmed-adapted-ccby4" if t["source"] else "confirmed-selfbuilt"
    return f"""id: {t['tid']}
registry_id: {RID}
domain: cad_geometry
task_type: design_artifact
model_profile: plain_llm
assets_revision: {REV}
environment_digest: computed-at-runtime
hidden: false
allowed_tools:
- python
input:
  prompt_file: tasks/{RID}/{t['tid']}.md
  prompt_sha256: {prompt_sha}
  assets: []
output_contract:
- sketch.step
reference:
  source: {src}；GT=题面几何规格解析计算（3D 化映射 {t['plane']}）
  revision: {REV}
  values:
    n_entities: {t['n_ent']}
    n_closed_profiles: {t['closed']}
  rel_tol: 0.05
  uncertainty_note: 实体级匹配（端点容差 0.01mm/样条拟合点在曲线上）；无连续场误差
grader:
  artifact_kind: sketch_2d
  answer_format: code
  validity_gate: true
  plane_normal: [{normal[0]}, {normal[1]}, {normal[2]}]
  sketch_gt:
    lines: {gt_lines}
    splines: {gt_splines}
    circles: []
  sketch_checks:
  - check: n_entities
    expect: {t['n_ent']}
  - check: n_closed_profiles
    expect: {t['closed']}
  - check: plane
    expect: true
  oracle_source: data/cadbench-seldon/sketch_lite/gold/{t['tid']}.py
  numeric_rel_tol: 0.05
  sandbox:
    banned: shell/network/process
    isolated_interpreter: true
scoring:
  weights:
    physics: 0.5
    requirements: 0.5
    objective: 0.0
    robustness: 0.0
  note: physics=GT 实体命中-多余实体惩罚；requirements=实体数/闭合环数/平面精确
limits:
  cpu: 1
  memory_gb: 4
  wall_clock_s: 240
  attempts: 3
license_provenance:
  source: {src}
  license: {lic}
  status: {status}
  mirror_allowed: true
  revision: {REV}
"""


# ---------------------------------------------------------------- 自检（gold 全链）

def gold_selfcheck(t) -> dict:
    """tempdir 跑 gold → 判分管线（_edge_entities/match/closed/plane）→ 期望满分。"""
    from runners.design_artifact import (_edge_entities, closed_profiles,
                                         match_sketch, plane_check)
    normal, map_fn = PLANES[t["plane"]]
    with tempfile.TemporaryDirectory(prefix="cbsk_") as td:
        Path(td, "model.py").write_text(gold_script(t), encoding="utf-8")
        r = subprocess.run([sys.executable, "model.py"], cwd=td,
                           capture_output=True, text=True, timeout=180)
        if r.returncode != 0:
            raise RuntimeError(f"{t['tid']} gold 执行失败: {r.stderr[-400:]}")
        step = Path(td, "sketch.step")
        if not step.exists():
            raise RuntimeError(f"{t['tid']} gold 未产出 sketch.step")
        ents = _edge_entities(step)
        gt = {"lines": [[list(map_fn(*a)), list(map_fn(*b))] for a, b in t["lines"]],
              "splines": [[list(map_fn(*pt)) for pt in sp] for sp in t["splines"]],
              "circles": []}
        m = match_sketch(gt, ents)
        pc = plane_check(ents, normal)
        cp = closed_profiles(ents)
        ok = (m["physics"] == 1.0 and pc["ok"] and cp == t["closed"]
              and len(ents) == t["n_ent"])
        return {"tid": t["tid"], "physics": m["physics"], "n_ents": len(ents),
                "closed": cp, "plane_ok": pc["ok"], "pass": ok}


def main() -> int:
    TASKS_DIR.mkdir(parents=True, exist_ok=True)
    GOLD_DIR.mkdir(parents=True, exist_ok=True)
    rows = []
    for t in tasks_def():
        prompt = render_prompt(t)
        psha = hashlib.sha256(prompt.encode("utf-8")).hexdigest()
        (TASKS_DIR / f"{t['tid']}.md").write_text(prompt, encoding="utf-8")
        (TASKS_DIR / f"{t['tid']}.yaml").write_text(emit_yaml(t, psha), encoding="utf-8")
        (GOLD_DIR / f"{t['tid']}.py").write_text(gold_script(t), encoding="utf-8")
        rows.append(gold_selfcheck(t))
        print(f"gen {t['tid']:<20} {t['fam']:<8} n={t['n_ent']} src={t['source'] or 'self'}")
    print("\ngold 全链自检（判分管线对 gold 实跑）：")
    n_ok = 0
    for r in rows:
        flag = "PASS" if r["pass"] else "FAIL"
        n_ok += r["pass"]
        print(f"  {flag}  {r['tid']:<20} physics={r['physics']} ents={r['n_ents']} "
              f"closed={r['closed']} plane={r['plane_ok']}")
    print(f"\n{n_ok}/{len(rows)} 通过；任务 -> {TASKS_DIR}")
    return 0 if n_ok == len(rows) else 1


if __name__ == "__main__":
    raise SystemExit(main())
