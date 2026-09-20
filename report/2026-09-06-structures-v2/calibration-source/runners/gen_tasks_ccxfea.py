#!/usr/bin/env python3
"""gen_tasks_ccxfea.py — calculix.fea_basic 任务生成 + gold 预计算（structures 维）。

自建基准（同 gtm/cadgen DNA）：不镜像 SimJEB 数据，5 族 21 题参数化生成，
判分 100% 本地复现（gold = ccx 2.23 对参考 INP 的实跑值，oracle 逐字节复现）。

族（钢，mm-N-MPa-tonne，E=210000 MPa, ν=0.3, ρ=7.85e-9 tonne/mm³）：
  cb   悬臂梁静力       ×5  解析 δ=PL³/3EI / 反力=-P
  ssb  简支梁中点载荷   ×4  解析 δ=PL³/48EI / 支反力=P/2（knife-edge RBC）
  modal 悬臂梁模态      ×4  解析 EB f=β²/2π·√(EI/ρAL⁴)（弱轴/强轴）
  bkl  悬臂梁屈曲       ×4  解析欧拉 Pcr=π²EI/4L²（弱轴/强轴）
  lb   L 支架静力       ×4  无解析参照（gold=ccx 自洽；呼应 simjeb 支架域/cadgen L 族）

协议：模型写 make_case.py（生成 model.inp，不执行求解器）→ runner 跑 ccx →
.dat 数值对 gold 判分（rel_tol：静力 5% / 模态 3% / 屈曲 5%）。
网格自由度钉死：C3D20、轴向≥16/高度向≥4/宽度向≥2，离散化差进容差带。

用法：.venv/bin/python -m runners.gen_tasks_ccxfea  （幂等重跑，覆盖重写）
"""
from __future__ import annotations

import hashlib
import json
import math
import shutil
import subprocess
import sys
import tempfile
from pathlib import Path

from .solvers.calculix import ccx_binary, parse_dat, run_ccx

BENCH = Path(__file__).resolve().parent.parent
RID = "calculix.fea_basic"
TASKS_DIR = BENCH / "tasks" / RID
GOLD_DIR = BENCH / "data" / "calculix" / "fea_basic" / "gold"
E, NU, RHO = 210000.0, 0.3, 7.85e-9
REV = "ccxfea@selfbuilt-2026-08-24+ccx2.23"

# ---------------------------------------------------------------- 网格基元


def seg_grid(segs):
    """[(x0,x1,n),...] → 含中点的全网格线坐标表（每段 n 个 C3D20 单元）。"""
    out = []
    for x0, x1, n in segs:
        pts = [x0 + (x1 - x0) * i / (2 * n) for i in range(2 * n)]
        out.extend(pts if not out else pts[1:])
    return out


def build_mesh(xs, ys, zs, keep_cell=None):
    """结构化 C3D20 网格。keep_cell(i,j,k) 为假则剔单元（L 形域用）。
    返回 (nodes[(id,x,y,z)], els[(id,[20 ids])])——节点编号从 1 起，跨单元共享。"""
    nid: dict[tuple[int, int, int], int] = {}
    nodes: list[tuple[int, float, float, float]] = []

    def get_node(i, j, k):
        if (i, j, k) not in nid:
            nid[(i, j, k)] = len(nodes) + 1
            nodes.append((len(nodes) + 1, xs[i], ys[j], zs[k]))
        return nid[(i, j, k)]

    def elem(i, j, k):
        c = [(2 * i, 2 * j, 2 * k), (2 * i + 2, 2 * j, 2 * k),
             (2 * i + 2, 2 * j + 2, 2 * k), (2 * i, 2 * j + 2, 2 * k),
             (2 * i, 2 * j, 2 * k + 2), (2 * i + 2, 2 * j, 2 * k + 2),
             (2 * i + 2, 2 * j + 2, 2 * k + 2), (2 * i, 2 * j + 2, 2 * k + 2),
             (2 * i + 1, 2 * j, 2 * k), (2 * i + 2, 2 * j + 1, 2 * k),
             (2 * i + 1, 2 * j + 2, 2 * k), (2 * i, 2 * j + 1, 2 * k),
             (2 * i + 1, 2 * j, 2 * k + 2), (2 * i + 2, 2 * j + 1, 2 * k + 2),
             (2 * i + 1, 2 * j + 2, 2 * k + 2), (2 * i, 2 * j + 1, 2 * k + 2),
             (2 * i, 2 * j, 2 * k + 1), (2 * i + 2, 2 * j, 2 * k + 1),
             (2 * i + 2, 2 * j + 2, 2 * k + 1), (2 * i, 2 * j + 2, 2 * k + 1)]
        return [get_node(*p) for p in c]

    nx, ny, nz = (len(xs) - 1) // 2, (len(ys) - 1) // 2, (len(zs) - 1) // 2
    els = []
    for k in range(nz):
        for j in range(ny):
            for i in range(nx):
                if keep_cell and not keep_cell(i, j, k):
                    continue
                els.append((len(els) + 1, elem(i, j, k)))
    return nodes, els


def nodes_where(nodes, pred):
    return [n[0] for n in nodes if pred(n)]


def inp_text(nodes, els, sets, material, steps):
    """渲染 INP（ccx 16 项/行折行纪律内建）。"""
    L = ["*NODE"]
    for n_, x, y, z in nodes:
        L.append(f"{n_}, {x:.6f}, {y:.6f}, {z:.6f}")
    L.append("*ELEMENT, TYPE=C3D20, ELSET=EALL")
    for en, conn in els:
        ids = [en] + conn
        for s in range(0, len(ids), 16):
            L.append(", ".join(str(c) for c in ids[s:s + 16]))
    for name, ids in sets.items():
        L.append(f"*NSET, NSET={name}")
        for s in range(0, len(ids), 16):
            L.append(", ".join(str(c) for c in ids[s:s + 16]))
    L.append("*MATERIAL, NAME=STEEL")
    L.append("*ELASTIC")
    L.append(f"{material['E']}, {material['nu']}")
    L.append("*DENSITY")
    L.append(f"{material['rho']:.6e}")
    L.append("*SOLID SECTION, ELSET=EALL, MATERIAL=STEEL")
    L.extend(steps)
    return "\n".join(L) + "\n"


# ---------------------------------------------------------------- gold 生成器（模型可见的参考答案模板）

def gold_script(body: str) -> str:
    return GOLD_HEADER + body


GOLD_HEADER = '''"""make_case.py — write a valid CalculiX input deck `model.inp` in the cwd.

Units: mm, N, MPa, tonne/mm^3 (steel E=210000 MPa, nu=0.3, rho=7.85e-9).
20-node hex C3D20 elements on a structured mesh; connectivity and nset lines
are wrapped to at most 16 entries per line (CalculiX line limit).
"""
'''


def beam_body(fam, p):
    """cb/ssb/modal/bkl 族共用的 gold 脚本体（参数差异化；按族惰性渲染载荷步）。"""
    if fam == "cb":
        load_lines = f"""    f.write("*STEP\\n*STATIC\\n")
    for nd in NTIP:
        f.write(f"*CLOAD\\n{{nd}}, 2, {{{p['load']} / len(NTIP):.9f}}\\n")
    f.write("*NODE PRINT, NSET=NTIP\\nU\\n*NODE PRINT, NSET=NROOT\\nRF\\n*END STEP\\n")"""
    elif fam == "ssb":
        load_lines = f"""    f.write("*STEP\\n*STATIC\\n")
    for nd in NMID:
        f.write(f"*CLOAD\\n{{nd}}, 2, {{{p['load']} / len(NMID):.9f}}\\n")
    f.write("*NODE PRINT, NSET=NMID\\nU\\n*NODE PRINT, NSET=NLEFT\\nRF\\n*END STEP\\n")"""
    elif fam == "modal":
        load_lines = """    f.write("*STEP\\n*FREQUENCY\\n4\\n*END STEP\\n")"""
    else:  # bkl
        load_lines = """    f.write("*STEP\\n*BUCKLE\\n4\\n")
    for nd in NTIP:
        f.write(f"*CLOAD\\n{nd}, 1, {-1.0 / len(NTIP):.9f}\\n")
    f.write("*END STEP\\n")"""
    if fam in ("cb", "modal", "bkl"):
        bc = '*BOUNDARY\\nNROOT, 1, 3, 0.0\\n'
    else:  # ssb
        bc = '*BOUNDARY\\nNLEFT, 2, 2, 0.0\\nNRIGHT, 2, 2, 0.0\\nPIN, 1, 3, 0.0\\n'
    if fam == "ssb":
        sets_py = '''NROOT = [n[0] for n in nodes if abs(n[1]) < 1e-9]
NLEFT = [n[0] for n in nodes if abs(n[1]) < 1e-9 and abs(n[2] + H / 2) < 1e-9]
NRIGHT = [n[0] for n in nodes if abs(n[1] - L) < 1e-9 and abs(n[2] + H / 2) < 1e-9]
NMID = [n[0] for n in nodes if abs(n[1] - L / 2) < 1e-9]
PIN = [n[0] for n in nodes if abs(n[1]) < 1e-9 and abs(n[2] + H / 2) < 1e-9][:1]
sets = {"NLEFT": NLEFT, "NRIGHT": NRIGHT, "NMID": NMID, "PIN": PIN}'''
    else:
        sets_py = '''NROOT = [n[0] for n in nodes if abs(n[1]) < 1e-9]
NTIP = [n[0] for n in nodes if abs(n[1] - L) < 1e-9]
sets = {"NROOT": NROOT, "NTIP": NTIP}'''
    dens = "7.85e-9"
    return f'''import math

L, H, T = {p['L']}, {p['H']}, {p['T']}
NX, NY, NZ = {p['nx']}, {p['ny']}, {p['nz']}


def seg(x0, x1, n):
    return [x0 + (x1 - x0) * i / (2 * n) for i in range(2 * n + 1)]


xs, ys, zs = seg(0.0, L, NX), seg(-H / 2, H / 2, NY), seg(-T / 2, T / 2, NZ)
nid = {{}}
nodes = []


def get_node(i, j, k):
    if (i, j, k) not in nid:
        nid[(i, j, k)] = len(nodes) + 1
        nodes.append((len(nodes) + 1, xs[i], ys[j], zs[k]))
    return nid[(i, j, k)]


def elem(i, j, k):
    c = [(2 * i, 2 * j, 2 * k), (2 * i + 2, 2 * j, 2 * k),
         (2 * i + 2, 2 * j + 2, 2 * k), (2 * i, 2 * j + 2, 2 * k),
         (2 * i, 2 * j, 2 * k + 2), (2 * i + 2, 2 * j, 2 * k + 2),
         (2 * i + 2, 2 * j + 2, 2 * k + 2), (2 * i, 2 * j + 2, 2 * k + 2),
         (2 * i + 1, 2 * j, 2 * k), (2 * i + 2, 2 * j + 1, 2 * k),
         (2 * i + 1, 2 * j + 2, 2 * k), (2 * i, 2 * j + 1, 2 * k),
         (2 * i + 1, 2 * j, 2 * k + 2), (2 * i + 2, 2 * j + 1, 2 * k + 2),
         (2 * i + 1, 2 * j + 2, 2 * k + 2), (2 * i, 2 * j + 1, 2 * k + 2),
         (2 * i, 2 * j, 2 * k + 1), (2 * i + 2, 2 * j, 2 * k + 1),
         (2 * i + 2, 2 * j + 2, 2 * k + 1), (2 * i, 2 * j + 2, 2 * k + 1)]
    return [get_node(*q) for q in c]


els = []
for k in range(NZ):
    for j in range(NY):
        for i in range(NX):
            els.append((len(els) + 1, elem(i, j, k)))

{sets_py}

with open("model.inp", "w") as f:
    f.write("*NODE\\n")
    for n_, x, y, z in nodes:
        f.write(f"{{n_}}, {{x:.6f}}, {{y:.6f}}, {{z:.6f}}\\n")
    f.write("*ELEMENT, TYPE=C3D20, ELSET=EALL\\n")
    for en, conn in els:
        ids = [en] + conn
        for s in range(0, len(ids), 16):
            f.write(", ".join(str(c) for c in ids[s:s + 16]) + "\\n")
    for name, idlist in sets.items():
        f.write(f"*NSET, NSET={{name}}\\n")
        for s in range(0, len(idlist), 16):
            f.write(", ".join(str(c) for c in idlist[s:s + 16]) + "\\n")
    f.write("*MATERIAL, NAME=STEEL\\n*ELASTIC\\n210000.0, 0.3\\n*DENSITY\\n{dens}\\n")
    f.write("*SOLID SECTION, ELSET=EALL, MATERIAL=STEEL\\n")
    f.write("{bc}")
{load_lines}
'''


def lbracket_body(p):
    """L 支架族 gold：L 域 = 竖臂 x∈[0,t] + 横臂 y∈[0,t]，全域结构化网格剔域外单元。"""
    return f'''LH, LV, T, W = {p['LH']}, {p['LV']}, {p['T']}, {p['W']}
NXT, NXL, NYT, NYV, NZ = {p['nxt']}, {p['nxl']}, {p['nyt']}, {p['nyv']}, {p['nz']}


def seg(x0, x1, n):
    return [x0 + (x1 - x0) * i / (2 * n) for i in range(2 * n + 1)]


xs = seg(0.0, T, NXT)[:-1] + seg(T, LH, NXL)
ys = seg(0.0, T, NYT)[:-1] + seg(T, LV, NYV)
zs = seg(0.0, W, NZ)
nx, ny, nz = (len(xs) - 1) // 2, (len(ys) - 1) // 2, (len(zs) - 1) // 2

nid = {{}}
nodes = []


def get_node(i, j, k):
    if (i, j, k) not in nid:
        nid[(i, j, k)] = len(nodes) + 1
        nodes.append((len(nodes) + 1, xs[i], ys[j], zs[k]))
    return nid[(i, j, k)]


def elem(i, j, k):
    c = [(2 * i, 2 * j, 2 * k), (2 * i + 2, 2 * j, 2 * k),
         (2 * i + 2, 2 * j + 2, 2 * k), (2 * i, 2 * j + 2, 2 * k),
         (2 * i, 2 * j, 2 * k + 2), (2 * i + 2, 2 * j, 2 * k + 2),
         (2 * i + 2, 2 * j + 2, 2 * k + 2), (2 * i, 2 * j + 2, 2 * k + 2),
         (2 * i + 1, 2 * j, 2 * k), (2 * i + 2, 2 * j + 1, 2 * k),
         (2 * i + 1, 2 * j + 2, 2 * k), (2 * i, 2 * j + 1, 2 * k),
         (2 * i + 1, 2 * j, 2 * k + 2), (2 * i + 2, 2 * j + 1, 2 * k + 2),
         (2 * i + 1, 2 * j + 2, 2 * k + 2), (2 * i, 2 * j + 1, 2 * k + 2),
         (2 * i, 2 * j, 2 * k + 1), (2 * i + 2, 2 * j, 2 * k + 1),
         (2 * i + 2, 2 * j + 2, 2 * k + 1), (2 * i, 2 * j + 2, 2 * k + 1)]
    return [get_node(*q) for q in c]


def in_L(i, j):
    return xs[2 * i + 2] <= T + 1e-9 or ys[2 * j + 2] <= T + 1e-9


els = []
for k in range(nz):
    for j in range(ny):
        for i in range(nx):
            if not in_L(i, j):
                continue
            els.append((len(els) + 1, elem(i, j, k)))

NROOT = [n[0] for n in nodes if abs(n[1]) < 1e-9]
NLOAD = [n[0] for n in nodes if abs(n[1] - LH) < 1e-9]
sets = {{"NROOT": NROOT, "NLOAD": NLOAD}}

with open("model.inp", "w") as f:
    f.write("*NODE\\n")
    for n_, x, y, z in nodes:
        f.write(f"{{n_}}, {{x:.6f}}, {{y:.6f}}, {{z:.6f}}\\n")
    f.write("*ELEMENT, TYPE=C3D20, ELSET=EALL\\n")
    for en, conn in els:
        ids = [en] + conn
        for s in range(0, len(ids), 16):
            f.write(", ".join(str(c) for c in ids[s:s + 16]) + "\\n")
    for name, idlist in sets.items():
        f.write(f"*NSET, NSET={{name}}\\n")
        for s in range(0, len(idlist), 16):
            f.write(", ".join(str(c) for c in idlist[s:s + 16]) + "\\n")
    f.write("*MATERIAL, NAME=STEEL\\n*ELASTIC\\n210000.0, 0.3\\n*DENSITY\\n7.85e-9\\n")
    f.write("*SOLID SECTION, ELSET=EALL, MATERIAL=STEEL\\n")
    f.write("*BOUNDARY\\nNROOT, 1, 3, 0.0\\n")
    f.write("*STEP\\n*STATIC\\n")
    for nd in NLOAD:
        f.write(f"*CLOAD\\n{{nd}}, 2, {{{p['load']} / len(NLOAD):.9f}}\\n")
    f.write("*NODE PRINT, NSET=NLOAD\\nU\\n*NODE PRINT, NSET=NROOT\\nRF\\n*END STEP\\n")
'''


# ---------------------------------------------------------------- gold 实跑


def run_gold(script: str, extract: dict) -> dict:
    with tempfile.TemporaryDirectory(prefix="ccxgold_") as td:
        Path(td, "make_case.py").write_text(script, encoding="utf-8")
        r = subprocess.run([sys.executable, "make_case.py"], cwd=td,
                           capture_output=True, text=True, timeout=120)
        if r.returncode != 0:
            raise RuntimeError(f"gold make_case 失败: {r.stderr[-500:]}")
        if not Path(td, "model.inp").exists():
            raise RuntimeError("gold 未写出 model.inp")
        rr = run_ccx(td, "model", 240.0)
        if rr["exit"] != 0:
            raise RuntimeError(f"gold ccx 失败: {rr['stdout_tail'][-500:]}")
        return parse_dat(Path(td, "model.dat"), extract)


# ---------------------------------------------------------------- 任务定义

def tasks_def():
    T = []

    # ---- cb 悬臂静力 ×5
    cb_params = [
        dict(L=100, H=10, T=5, load=-1000.0, nx=20, ny=4, nz=2),
        dict(L=120, H=10, T=5, load=-800.0, nx=24, ny=4, nz=2),
        dict(L=80, H=12, T=6, load=-2000.0, nx=16, ny=4, nz=2),
        dict(L=150, H=12, T=6, load=-500.0, nx=30, ny=4, nz=2),
        dict(L=100, H=8, T=4, load=-1500.0, nx=20, ny=4, nz=2),
    ]
    for i, p in enumerate(cb_params, 1):
        I = p["T"] * p["H"] ** 3 / 12
        ana = {"tip_defl_mm": p["load"] * p["L"] ** 3 / (3 * E * I),
               "root_rf_sum_n": -p["load"]}
        T.append(dict(fam="cb", tid=f"ccx_cb_{i:02d}", p=p,
                      extract={"tip_defl_mm": dict(type="max_abs_udof", set="NTIP", dof=2),
                               "root_rf_sum_n": dict(type="sum_rf", set="NROOT", dof=2)},
                      ana=ana, tol=0.05,
                      title=f"Cantilever beam static deflection ({p['L']}×{p['H']}×{p['T']} mm, tip load {p['load']} N)"))

    # ---- ssb 简支梁 ×4
    ssb_params = [
        dict(L=200, H=10, T=5, load=-1000.0, nx=40, ny=4, nz=2),
        dict(L=160, H=12, T=6, load=-1200.0, nx=32, ny=4, nz=2),
        dict(L=240, H=10, T=6, load=-800.0, nx=48, ny=4, nz=2),
        dict(L=180, H=8, T=5, load=-600.0, nx=36, ny=4, nz=2),
    ]
    for i, p in enumerate(ssb_params, 1):
        I = p["T"] * p["H"] ** 3 / 12
        ana = {"mid_defl_mm": p["load"] * p["L"] ** 3 / (48 * E * I),
               "support_rf_sum_n": -p["load"] / 2}
        T.append(dict(fam="ssb", tid=f"ccx_ssb_{i:02d}", p=p,
                      extract={"mid_defl_mm": dict(type="max_abs_udof", set="NMID", dof=2),
                               "support_rf_sum_n": dict(type="sum_rf", set="NLEFT", dof=2)},
                      ana=ana, tol=0.05,
                      title=f"Simply supported beam, mid-span load ({p['L']}×{p['H']}×{p['T']} mm, P={p['load']} N)"))

    # ---- modal 悬臂模态 ×4（H/T=2：mode1=弱轴 mode2=强轴）
    md_params = [
        dict(L=100, H=10, T=5, nx=20, ny=4, nz=2),
        dict(L=150, H=12, T=6, nx=30, ny=4, nz=2),
        dict(L=120, H=8, T=4, nx=24, ny=4, nz=2),
        dict(L=200, H=12, T=6, nx=40, ny=4, nz=2),
    ]
    for i, p in enumerate(md_params, 1):
        A, Is, Iw = p["T"] * p["H"], p["T"] * p["H"] ** 3 / 12, p["H"] * p["T"] ** 3 / 12
        ana = {"f1_hz": 1.875 ** 2 / (2 * math.pi) * math.sqrt(E * Iw / (RHO * A * p["L"] ** 4)),
               "f2_hz": 1.875 ** 2 / (2 * math.pi) * math.sqrt(E * Is / (RHO * A * p["L"] ** 4))}
        T.append(dict(fam="modal", tid=f"ccx_md_{i:02d}", p=p,
                      extract={"f1_hz": dict(type="eigen_freq", mode=1),
                               "f2_hz": dict(type="eigen_freq", mode=2)},
                      ana=ana, tol=0.03,
                      title=f"Cantilever beam natural frequencies ({p['L']}×{p['H']}×{p['T']} mm)"))

    # ---- bkl 悬臂屈曲 ×4（总轴向单位载荷 -1 N，因子即 Pcr/N）
    bk_params = [
        dict(L=100, H=10, T=5, nx=20, ny=4, nz=2),
        dict(L=150, H=12, T=6, nx=30, ny=4, nz=2),
        dict(L=120, H=8, T=4, nx=24, ny=4, nz=2),
        dict(L=200, H=10, T=5, nx=40, ny=4, nz=2),
    ]
    for i, p in enumerate(bk_params, 1):
        Iw, Is = p["H"] * p["T"] ** 3 / 12, p["T"] * p["H"] ** 3 / 12
        ana = {"buckle_factor_1": math.pi ** 2 * E * Iw / (4 * p["L"] ** 2),
               "buckle_factor_2": math.pi ** 2 * E * Is / (4 * p["L"] ** 2)}
        T.append(dict(fam="bkl", tid=f"ccx_bk_{i:02d}", p=p,
                      extract={"buckle_factor_1": dict(type="buckle_factor", mode=1),
                               "buckle_factor_2": dict(type="buckle_factor", mode=2)},
                      ana=ana, tol=0.05,
                      title=f"Cantilever column buckling ({p['L']}×{p['H']}×{p['T']} mm, unit compressive load)"))

    # ---- lb L 支架 ×4（竖臂 x∈[0,T] y∈[0,LV]，横臂 y∈[0,T] x∈[0,LH]，z 向宽 W）
    lb_params = [
        dict(LH=60, LV=60, T=10, W=20, load=-500.0, nxt=2, nxl=8, nyt=2, nyv=8, nz=2),
        dict(LH=80, LV=50, T=8, W=16, load=-400.0, nxt=2, nxl=10, nyt=2, nyv=7, nz=2),
        dict(LH=50, LV=80, T=12, W=24, load=-800.0, nxt=3, nxl=6, nyt=2, nyv=9, nz=2),
        dict(LH=70, LV=70, T=10, W=20, load=-600.0, nxt=2, nxl=9, nyt=2, nyv=9, nz=2),
    ]
    for i, p in enumerate(lb_params, 1):
        T.append(dict(fam="lb", tid=f"ccx_lb_{i:02d}", p=p,
                      extract={"tip_defl_mm": dict(type="max_abs_udof", set="NLOAD", dof=2),
                               "root_rf_sum_n": dict(type="sum_rf", set="NROOT", dof=2)},
                      ana=None, tol=0.05,
                      title=f"L-bracket static deflection (arms {p['LH']}×{p['LV']} mm, t={p['T']} mm, W={p['W']} mm)"))
    return T


# ---------------------------------------------------------------- prompt 渲染

COMMON_RULES = """
## Deliverable

Respond with ONE complete ```python code block: a script that, when executed in an
empty working directory, writes a valid CalculiX 2.23 input deck named exactly
`model.inp` (in the current directory). The script must NOT run the solver, must not
use subprocess/network, and must be self-contained (no external files).

## Deck discipline (grading contract)

- Units: mm, N, MPa, tonne/mm^3 — steel: E = 210000 MPa, nu = 0.3,
  rho = 7.85e-9 tonne/mm^3.
- Elements: 20-node hexahedra `C3D20` ONLY, on a structured mesh with
  AT LEAST the minimum mesh counts stated above.
- Node sets with EXACTLY the names given below (grading parses the .dat output
  for these set names).
- Any data line must contain at most 16 comma-separated entries (wrap element
  connectivity and node-set lines across lines as needed).
- Request exactly the output prints specified below, inside the step.
"""


def render_prompt(t):
    p = t["p"]
    if t["fam"] == "cb":
        spec = f"""# {t['title']}

Model a straight cantilever beam with CalculiX (linear static):

- Geometry: length L = {p['L']} mm along +x (root at x=0), rectangular cross-section
  height H = {p['H']} mm (y from -H/2 to +H/2), width T = {p['T']} mm (z from -T/2 to +T/2).
- Root face x=0 fully clamped (all DOF, set NROOT = all nodes with x=0).
- Tip load: total force Fy = {p['load']} N distributed EQUALLY among ALL nodes of the
  tip face x=L (set NTIP) as concentrated nodal loads (*CLOAD), summing exactly to Fy.
- Minimum mesh: >= 16 elements along the length, >= 4 through the height,
  >= 2 through the width (C3D20).
- Node sets: NROOT (root face), NTIP (tip face).
- Output requests inside *STEP/*STATIC:
  `*NODE PRINT, NSET=NTIP` with `U`, and `*NODE PRINT, NSET=NROOT` with `RF`.
"""
    elif t["fam"] == "ssb":
        spec = f"""# {t['title']}

Model a simply supported beam on knife-edge supports with CalculiX (linear static):

- Geometry: length L = {p['L']} mm along x, cross-section H = {p['H']} mm (y from -H/2
  to +H/2), T = {p['T']} mm (z from -T/2 to +T/2).
- Supports (knife edges at the BOTTOM lines of the end faces, y = -H/2):
  set NLEFT = nodes at x=0, y=-H/2 (all z); set NRIGHT = nodes at x=L, y=-H/2 (all z).
  Constrain Uy = 0 on NLEFT and NRIGHT; additionally fix Ux and Uz of ONE node of
  NLEFT (set PIN, just that node) to remove rigid-body modes. All other DOF free.
- Mid-span load: total Fy = {p['load']} N distributed EQUALLY among ALL nodes of the
  mid-span section x=L/2 (set NMID), summing exactly to Fy.
- Minimum mesh: >= 16 elements along the length, >= 4 through the height,
  >= 2 through the width (C3D20).
- Output requests inside *STEP/*STATIC:
  `*NODE PRINT, NSET=NMID` with `U`, and `*NODE PRINT, NSET=NLEFT` with `RF`.
"""
    elif t["fam"] == "modal":
        spec = f"""# {t['title']}

Compute the first natural frequencies of a cantilever beam with CalculiX:

- Geometry: length L = {p['L']} mm along x, cross-section H = {p['H']} mm in y,
  T = {p['T']} mm in z (note H = 2T: first mode bends about the weak axis).
- Root face x=0 fully clamped (set NROOT = all nodes with x=0); set NTIP = tip face nodes.
- Material includes density (7.85e-9 tonne/mm^3) — required for *FREQUENCY.
- Analysis: `*STEP` with `*FREQUENCY` requesting 4 modes (linear perturbation).
- Minimum mesh: >= 16 elements along the length, >= 4 through the height,
  >= 2 through the width (C3D20).
- Node sets: NROOT, NTIP (not printed, but define them).
"""
    elif t["fam"] == "bkl":
        spec = f"""# {t['title']}

Compute the buckling load factors of a cantilever column with CalculiX:

- Geometry: length L = {p['L']} mm along x, cross-section H = {p['H']} mm in y,
  T = {p['T']} mm in z (H = 2T: mode 1 buckles about the weak axis).
- Root face x=0 fully clamped (set NROOT = all nodes with x=0); set NTIP = tip face nodes.
- Reference load for the buckling step: total axial force Fx = -1 N (compression)
  distributed EQUALLY among ALL nodes of the tip face (set NTIP); buckling factors
  multiply this reference load.
- Analysis: `*STEP` with `*BUCKLE` requesting 4 modes. Density in the material
  definition is fine (not used by *BUCKLE).
- Minimum mesh: >= 16 elements along the length, >= 4 through the height,
  >= 2 through the width (C3D20).
"""
    else:  # lb
        spec = f"""# {t['title']}

Model a wall-mounted L-bracket with CalculiX (linear static):

- Cross-section (x-y plane) is an L shape: vertical arm x in [0, {p['T']}] with
  y in [0, {p['LV']}], plus horizontal arm y in [0, {p['T']}] with x in [0, {p['LH']}].
  The bracket is extruded in z over width W = {p['W']} mm (z in [0, W]).
- Mount face: the whole face x=0 is clamped (set NROOT = all nodes with x=0).
- Load: total Fy = {p['load']} N (downward, -y) distributed EQUALLY among ALL nodes
  of the free end face x={p['LH']} (set NLOAD), summing exactly to Fy.
- Minimum mesh (C3D20, structured, conformal at the re-entrant corner): >= 2 elements
  across each arm thickness, >= 6 along each arm length, >= 2 through the width.
- Output requests inside *STEP/*STATIC:
  `*NODE PRINT, NSET=NLOAD` with `U`, and `*NODE PRINT, NSET=NROOT` with `RF`.
"""
    return spec + COMMON_RULES


# ---------------------------------------------------------------- 主流程


def emit_yaml(t, values, prompt_sha):
    keys = list(t["extract"].keys())
    vals_txt = "\n".join(f"    {k}: {values[k]!r}" for k in keys)
    ext_txt = "\n".join(
        f"    {k}:\n      type: {v['type']}" +
        (f"\n      set: {v['set']}" if "set" in v else "") +
        (f"\n      dof: {v['dof']}" if "dof" in v else "") +
        (f"\n      mode: {v['mode']}" if "mode" in v else "")
        for k, v in t["extract"].items())
    keys_txt = "\n".join(f"  - {k}" for k in keys)
    ana_note = "解析交叉验证：" + "; ".join(
        f"{k}={v:.4g}" for k, v in (t["ana"] or {}).items()) if t["ana"] else \
        "无解析参照（L 支架静不定；gold=ccx 参考网格自洽）"
    return f"""id: {t['tid']}
registry_id: {RID}
domain: structures
task_type: simulation_agent
model_profile: plain_llm
assets_revision: {REV}
environment_digest: computed-at-runtime
hidden: false
allowed_tools:
- python
- calculix
input:
  prompt_file: tasks/{RID}/{t['tid']}.md
  prompt_sha256: {prompt_sha}
  assets: []
output_contract:
- model.inp
reference:
  source: gold make_case.py 实跑 ccx 2.23 的 .dat 解析值（确定性；自建任务）
  revision: {REV}
  values:
{vals_txt}
  rel_tol: {t['tol']}
  uncertainty_note: {ana_note}；容差覆盖模型网格离散化差（题面钉死最小网格与 C3D20）
grader:
  answer_format: code
  exec_kind: ccx_fea
  validity_gate: true
  result_keys:
{keys_txt}
  numeric_rel_tol: {t['tol']}
  exact_keys: []
  extract:
{ext_txt}
  solver_backend: calculix-ccx-native
  oracle_source: data/calculix/fea_basic/gold/{t['tid']}.py
  sandbox:
    banned: shell/network/process
    isolated_interpreter: true
scoring:
  weights:
    physics: 0.5
    requirements: 0.5
    objective: 0.0
    robustness: 0.0
  note: physics=.dat 数值字段命中均值；requirements=模型可执行+model.inp+dat 键完备
limits:
  cpu: 1
  memory_gb: 4
  wall_clock_s: 300
  attempts: 3
license_provenance:
  source: 自建（受 SimJEB 支架域启发，未镜像其数据；求解器 CalculiX GPL-2.0 仅作执行后端）
  license: self-built
  status: confirmed-selfbuilt
  mirror_allowed: true
  revision: {REV}
"""


def main() -> int:
    TASKS_DIR.mkdir(parents=True, exist_ok=True)
    GOLD_DIR.mkdir(parents=True, exist_ok=True)
    ccx_binary()  # fail-fast
    rows = []
    for t in tasks_def():
        script = gold_script(
            lbracket_body(t["p"]) if t["fam"] == "lb" else beam_body(t["fam"], t["p"]))
        values = run_gold(script, t["extract"])
        missing = [k for k in t["extract"] if k not in values]
        if missing:
            raise SystemExit(f"{t['tid']}: gold 解析缺键 {missing}")
        prompt = render_prompt(t)
        psha = hashlib.sha256(prompt.encode("utf-8")).hexdigest()
        (TASKS_DIR / f"{t['tid']}.md").write_text(prompt, encoding="utf-8")
        (TASKS_DIR / f"{t['tid']}.yaml").write_text(emit_yaml(t, values, psha),
                                                    encoding="utf-8")
        (GOLD_DIR / f"{t['tid']}.py").write_text(script, encoding="utf-8")
        rel = {k: (values[k] - t["ana"][k]) / t["ana"][k] for k in (t["ana"] or {})}
        rows.append((t["tid"], values, rel))
    print(f"OK {len(rows)} tasks -> {TASKS_DIR}")
    print(f"{'task':<12} " + " | ".join(f"{k:<16}" for k in next(iter(rows), (('', {},)))[1]))
    for tid, values, rel in rows:
        v = " | ".join(f"{values[k]:<16.4g}" for k in values)
        print(f"{tid:<12} {v}")
    print("\n解析交叉验证（gold vs 解析，相对偏差）：")
    for tid, _, rel in rows:
        if rel:
            print(f"{tid:<12} " + "  ".join(f"{k}: {r:+.2%}" for k, r in rel.items()))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
