"""gen_tasks_gtm.py — 自建 gtm.transport_control 任务集（25 题，MATLAB 飞控；2026-08-22）.

产出（幂等；参考值由 gold 脚本 MATLAB 预计算锁定）：
  data/gtm/transport_control/{gold/,references/,PROVENANCE.md} + 任务 YAML/MD
  （tasks/gtm.transport_control/gtm_<tid>.{yaml,md}）

任务协议（simulation_agent / gtm_matlab 分支）：
  被测模型输出单个 ```matlab 代码块；脚本以 model.m 在隔离目录 `matlab -batch model`
  执行（R2026a，Control System Toolbox 可用）；必须在 cwd 写 result.json（jsonencode
  顶层对象）；数值键 1% 相对容差，exact_keys 精确匹配。task.limits.wall_clock_s
  覆盖 MATLAB 启动（~10-30s/次）。

任务族（8 族 25 题）：
  F1 纵向模态 ×5（lon_*）        给 A 求 omega_sp/zeta_sp/omega_ph/zeta_ph
  F2 配平 ×3（trim_*）           定直平飞 L=W,D=T 解 alpha_trim_deg/thrust_lbf
  F3 静稳定裕度 ×2（sm_*）       static_margin=-Cma/CLa 与 h_n
  F4 控制律设计 ×4（kdesign_*）  place 目标 SP 极点，判 cl_omega_sp/cl_zeta_sp
  F5 时域指标 ×3（tdm_*）        精确离散 dt=0.01/T=30s 钉死口径的阶跃指标
  F6 模型修复 ×2（repair_*）     corrupted_param(exact)+restored_value(1%)
  F7 包线鲁棒 ×3（env_*）        3 飞行条件 6 键 SP 模态
  F8 横航向模态 ×3（lat_*）      DR 对 + 滚转/螺旋实根

模态自检窗口（生成器对写出的每个 A 强制验证，不满足即抛错）：
  SP  ωn∈[1.2,2.8] ζ∈[0.25,0.65]（同任务规格）
  PH  ζ∈[0.02,0.12]（同规格）；ωn∈[0.025,0.06] ——【对规格的记录在案的偏差】
      规格 PH ωn∈[0.08,0.25] 与其同时给定的参数盒在数学上不相容：本结构
      char(0)=g·Zu·Mw ⇒ wn_sp·wn_ph=sqrt(g·|Zu·Mw|)，参数盒(|Zu|≤0.05,
      |Mw|≤0.008)加 SP 窗口可证 wn_ph 全域 ≤0.06（4 万点 LHS 扫描 max 0.0496）。
      取物理可达包络 [0.025,0.06]（周期 105-250s，运输机巡航量级），保持
      「模态分离干净、判分稳定」的规格意图；全部导数留在规格参数盒内。
  DR  ωn∈[0.8,1.8] ζ∈[0.05,0.25]；滚转实根∈[-2.5,-1.2]；螺旋实根∈[-0.10,-0.05]
      （全稳定；横航向最终系数直接写死——规格如此要求，Lβ 量级为满足全稳定
      螺旋窗所需，超出文献典型值，模态窗口优先。）

gold 预计算：runners/solvers/matlab.py::run_matlab（串行 matlab -batch，与判分
oracle 完全同路径执行）→ references/<tid>.json + YAML reference.values 内嵌；
numpy 侧独立复算每个参考值（<1e-6 相对差）防 MATLAB/numpy 口径漂移。

用法：python3 -m runners.gen_tasks_gtm [--check] [--force-refs]
"""

from __future__ import annotations

import argparse
import hashlib
import json
import tempfile
import time
from pathlib import Path

import numpy as np
import yaml

BENCH = Path(__file__).resolve().parent.parent
DATA = BENCH / "data/gtm/transport_control"
TASKS_DIR = BENCH / "tasks/gtm.transport_control"
ASSETS_REVISION = "gtm-flight@selfbuilt-2026-08-22+matlabR2026a"
REGISTRY_ID = "gtm.transport_control"
REL_TOL = 0.01
GOLD_TIMEOUT_S = 300.0

G = 32.174
RHO0 = 0.0023769

# 模态自检窗口（见模块 docstring 偏差记录）
SP_WN, SP_Z = (1.2, 2.8), (0.25, 0.65)
PH_WN, PH_Z = (0.025, 0.06), (0.02, 0.12)
DR_WN, DR_Z = (0.8, 1.8), (0.05, 0.25)
ROLL_L, SPIRAL_L = (-2.5, -1.2), (-0.10, -0.05)


# ================================================================ 参数表（写死，无 rng）

# 纵向 4 状态 x=[u w q θ]：A = [[Xu,Xw,0,-g],[Zu,Zw,V,0],[0,Mw,Mq,0],[0,0,1,0]]
# (V, Xu, Xw, Zu, Zw, Mw, Mq) — 全部系数在规格参数盒内
LON: dict[str, tuple] = {
    "lon_01": (700, -0.0065, 0.035, -0.030, -0.70, -0.0050, -0.90),
    "lon_02": (620, -0.0060, 0.045, -0.042, -0.85, -0.0065, -1.10),
    "lon_03": (780, -0.0060, 0.025, -0.020, -0.55, -0.0035, -0.65),
    "lon_04": (660, -0.0075, 0.055, -0.048, -0.78, -0.0072, -1.05),
    "lon_05": (745, -0.0055, 0.030, -0.025, -0.62, -0.0042, -0.75),
    "kdesign_01": (715, -0.0068, 0.040, -0.034, -0.73, -0.0054, -0.92),
    "kdesign_02": (640, -0.0062, 0.048, -0.044, -0.82, -0.0068, -1.08),
    "kdesign_03": (770, -0.0062, 0.028, -0.022, -0.58, -0.0038, -0.68),
    "kdesign_04": (690, -0.0058, 0.052, -0.046, -0.80, -0.0070, -1.00),
    "rep_01": (700, -0.0068, 0.040, -0.035, -0.72, -0.0055, -0.95),
    "rep_02": (680, -0.0064, 0.038, -0.033, -0.70, -0.0050, -0.85),
}

# F7 包线：每任务一套 3 飞行条件三元组（力导数随密度单调，Mw/Zw 比值近似保持）
# 每 FC: (alt_ft, V, Xu, Xw, Zu, Zw, Mw, Mq)
ENV: dict[str, tuple] = {
    "env_01": ((32000, 760, -0.0060, 0.046, -0.043, -0.80, -0.0062, -1.02),
               (36000, 710, -0.0058, 0.036, -0.031, -0.68, -0.0048, -0.88),
               (40000, 650, -0.0056, 0.026, -0.021, -0.56, -0.0036, -0.66)),
    "env_02": ((28000, 800, -0.0058, 0.050, -0.046, -0.84, -0.0068, -1.10),
               (33000, 745, -0.0060, 0.040, -0.034, -0.72, -0.0054, -0.94),
               (37000, 680, -0.0062, 0.030, -0.024, -0.60, -0.0042, -0.76)),
    "env_03": ((30000, 720, -0.0056, 0.044, -0.038, -0.76, -0.0058, -0.98),
               (34000, 665, -0.0058, 0.034, -0.028, -0.66, -0.0046, -0.84),
               (39000, 610, -0.0060, 0.024, -0.020, -0.56, -0.0036, -0.68)),
}

# F4：B=[0;Zde;Mde;0] 与目标闭环 SP（ωn_cl∈[1.8,2.6] ζ_cl∈[0.55,0.70]）
KD_B: dict[str, tuple] = {
    "kdesign_01": (-6.0, -4.0, 2.0, 0.60),
    "kdesign_02": (-5.0, -5.5, 2.3, 0.55),
    "kdesign_03": (-7.5, -3.0, 1.9, 0.65),
    "kdesign_04": (-4.5, -2.5, 2.5, 0.62),
}

# F6：损坏参数（真值在 LON 表；corrupted = factor × true）
REPAIR: dict[str, dict] = {
    "repair_01": {"base": "rep_01", "param": "Mw", "factor": 3.0,
                  "candidates": ("Mw", "Mq")},
    "repair_02": {"base": "rep_02", "param": "Mq", "factor": 0.4,
                  "candidates": ("Mw", "Mq")},
}

# F8 横航向 x=[β p r φ]：A=[[Yb, Yp, -(1-Yr), g/V],[Lβ,Lp,Lr,0],[Nβ,Np,Nr,0],[0,1,0,0]]
# (a11,a12,a13,a14, Lβ,Lp,Lr, Nβ,Np,Nr) —— 最终系数直接写死（规格要求），模态窗验证
LAT: dict[str, tuple] = {
    "lat_01": (-0.08, 0.02, -0.92, 0.048, -3.90, -1.35, -0.05, 0.58, -0.03, -0.30),
    "lat_02": (-0.10, 0.02, -0.90, 0.052, -6.20, -1.45, -0.05, 1.05, -0.04, -0.33),
    "lat_03": (-0.14, 0.02, -0.88, 0.055, -8.50, -1.45, -0.06, 1.55, -0.05, -0.42),
}

# F2 配平：(W_lbf, S_ft2, h_ft, V_fts, CLα, CL0, CD0, k, T0_lbf, V0)
TRIM: dict[str, tuple] = {
    "trim_01": (230000, 2400, 31000, 730, 5.2, 0.15, 0.021, 0.043, 62000, 730),
    "trim_02": (280000, 2730, 35000, 780, 5.6, 0.18, 0.019, 0.045, 68000, 780),
    "trim_03": (175000, 2050, 26000, 690, 4.9, 0.12, 0.023, 0.041, 54000, 690),
}

# F3 静稳定裕度：(CLα, Cmα, W/S psf, c ft, h_cg)
SM: dict[str, tuple] = {
    "sm_01": (5.3, -0.85, 98.0, 17.0, 0.25),
    "sm_02": (4.8, -1.10, 110.0, 19.5, 0.30),
}

# F5 时域指标：(A_cl, B_cl, C 输出行) —— 全部欠阻尼（overshoot>3%），指标非退化
TDM: dict[str, tuple] = {
    "tdm_01": (((-0.55, 1.0), (-3.90, -1.30)), ((0.0,), (1.0,)), ((1.0, 0.0),)),
    "tdm_02": (((-0.80, 1.0), (-6.20, -1.90)), ((0.0,), (1.0,)), ((1.0, 0.0))),
    "tdm_03": (((-0.60, 1.00, 0.10), (-4.40, -1.60, 0.20), (1.00, 0.50, -4.00)),
               ((0.0,), (1.0,), (0.5,)), ((1.0, 0.0, 0.0))),
}

DT, T_END = 0.01, 30.0     # F5 钉死仿真口径


# ================================================================ 数值内核 + 自检

def lon_A(p: tuple) -> np.ndarray:
    V, Xu, Xw, Zu, Zw, Mw, Mq = p
    return np.array([[Xu, Xw, 0.0, -G], [Zu, Zw, V, 0.0],
                     [0.0, Mw, Mq, 0.0], [0.0, 0.0, 1.0, 0.0]])


def lat_A(p: tuple) -> np.ndarray:
    a11, a12, a13, a14, Lb, Lp, Lr, Nb, Np, Nr = p
    return np.array([[a11, a12, a13, a14], [Lb, Lp, Lr, 0.0],
                     [Nb, Np, Nr, 0.0], [0.0, 1.0, 0.0, 0.0]])


def eig_pairs_reals(A: np.ndarray):
    """特征值分为共轭对 [(ωn,ζ)…按 ωn 降序] 与实根 [升序]；结构异常返回 (None, None)。"""
    ev = np.linalg.eigvals(A)
    pairs, reals, used = [], [], np.zeros(len(ev), bool)
    for i in range(len(ev)):
        if used[i]:
            continue
        if abs(ev[i].imag) > 1e-7 * max(1.0, abs(ev[i])):
            for j in range(i + 1, len(ev)):
                if not used[j] and abs(ev[j] - np.conj(ev[i])) < 1e-8:
                    lam = ev[i]
                    pairs.append((abs(lam), -lam.real / abs(lam)))
                    used[i] = used[j] = True
                    break
            else:
                return None, None
        else:
            reals.append(ev[i].real)
            used[i] = True
    return sorted(pairs, key=lambda q: -q[0]), sorted(reals)


def _win(v, lo, hi, what, tag):
    assert lo <= v <= hi, f"{tag}: {what}={v:.6f} 不在 [{lo},{hi}]"


def _lon_modes(A: np.ndarray, tag: str) -> dict:
    pairs, reals = eig_pairs_reals(A)
    assert pairs is not None and len(pairs) == 2 and not reals, \
        f"{tag}: 非两对共轭极点 ({pairs}, {reals})"
    (wsp, zsp), (wph, zph) = pairs
    return dict(omega_sp=wsp, zeta_sp=zsp, omega_ph=wph, zeta_ph=zph)


def v_lon(A: np.ndarray, tag: str) -> dict:
    m = _lon_modes(A, tag)
    _win(m["omega_sp"], *SP_WN, "SP wn", tag); _win(m["zeta_sp"], *SP_Z, "SP zeta", tag)
    _win(m["omega_ph"], *PH_WN, "PH wn", tag); _win(m["zeta_ph"], *PH_Z, "PH zeta", tag)
    return m


def v_lat(A: np.ndarray, tag: str) -> dict:
    pairs, reals = eig_pairs_reals(A)
    assert pairs is not None and len(pairs) == 1 and len(reals) == 2, \
        f"{tag}: 非一对 DR+两实根 ({pairs}, {reals})"
    wdr, zdr = pairs[0]
    roll, spiral = reals[0], reals[1]
    _win(wdr, *DR_WN, "DR wn", tag); _win(zdr, *DR_Z, "DR zeta", tag)
    _win(roll, *ROLL_L, "roll lambda", tag); _win(spiral, *SPIRAL_L, "spiral lambda", tag)
    return dict(dutch_roll_omega=wdr, dutch_roll_zeta=zdr,
                roll_mode_lambda=roll, spiral_mode_lambda=spiral)


def _bisect(f, lo, hi, it=200):
    flo, fhi = f(lo), f(hi)
    assert flo * fhi < 0, f"no bracket f({lo})={flo} f({hi})={fhi}"
    for _ in range(it):
        mid = 0.5 * (lo + hi)
        fm = f(mid)
        if flo * fm <= 0:
            hi, fhi = mid, fm
        else:
            lo, flo = mid, fm
    return 0.5 * (lo + hi)


def _dom_wn(A: np.ndarray) -> float:
    """主导（最大模）特征值的模——恒为短周期对。"""
    return float(max(abs(e) for e in np.linalg.eigvals(A)))


def _dom_zeta(A: np.ndarray) -> float:
    ev = np.linalg.eigvals(A)
    lam = ev[np.argmax(np.abs(ev))]
    return float(-lam.real / abs(lam))


_LON_IDX = {"Xu": 1, "Xw": 2, "Zu": 3, "Zw": 4, "Mw": 5, "Mq": 6}
_REPAIR_GRID = {"Mw": (-0.012, -0.0005, 0.00025), "Mq": (-2.4, -0.05, 0.005)}


def _scan_roots(f, grid) -> list:
    """网格扫描全部 1-D 根（含恰落在网格点上的零点；变号段二分加密）。"""
    roots = []
    prev_x, prev_f = float(grid[0]), f(float(grid[0]))
    if prev_f == 0.0:
        roots.append(prev_x)
    for x in grid[1:]:
        x = float(x)
        fx = f(x)
        if fx == 0.0:
            roots.append(x)
        elif prev_f * fx < 0:
            roots.append(_bisect(f, prev_x, x))
        prev_x, prev_f = x, fx
    return roots

def v_repair(tid: str) -> dict:
    """F6 自检：(a) 损坏矩阵 SP 模态明显偏离参考；(b) 候选参数中唯一可复原。

    判别口径 = 求解模型的自然路径：对每个候选 c，在物理邻域网格扫描对参考 SP
    ωn（或 ζ）求 1-D 根，再查另一指标是否同时复现——要求仅真参数能做到。
    """
    spec = REPAIR[tid]
    p = LON[spec["base"]]
    idx = _LON_IDX[spec["param"]]
    true_m = v_lon(lon_A(p), f"{tid}/true")
    corrupted = spec["factor"] * p[idx]

    def A_with(cand: str, val: float) -> np.ndarray:
        q = list(p)
        q[_LON_IDX[cand]] = val
        if cand != spec["param"]:            # 被测模型看到的是损坏矩阵
            q[idx] = corrupted
        return lon_A(tuple(q))

    # (a) 损坏后 SP 模态显著偏离参考（ωn/ζ 至少一项 >5%；Mq 损坏天然主要动 ζ）
    bad_m = _lon_modes(A_with(spec["param"], corrupted), f"{tid}/bad")   # 损坏态允许出窗
    devs = {k: abs(bad_m[k] - true_m[k]) / abs(true_m[k]) for k in ("omega_sp", "zeta_sp")}
    assert max(devs.values()) > 0.05, f"{tid}: 损坏后 SP 模态偏离不足 {devs}"

    # (b) 候选唯一性
    full_match: dict[str, list[float]] = {c: [] for c in spec["candidates"]}
    for cand in spec["candidates"]:
        lo, hi, step = _REPAIR_GRID[cand]
        grid = np.arange(lo, hi + step / 2, step)
        for tgt_key, other_key in (("omega_sp", "zeta_sp"), ("zeta_sp", "omega_sp")):
            def f(v: float, *, cand=cand, tk=tgt_key) -> float:
                A = A_with(cand, v)
                m = _dom_wn(A) if tk == "omega_sp" else _dom_zeta(A)
                return m - true_m[tk]
            for root in _scan_roots(f, grid):
                other = _dom_zeta(A_with(cand, root)) if tgt_key == "omega_sp" \
                    else _dom_wn(A_with(cand, root))
                if abs(other - true_m[other_key]) / abs(true_m[other_key]) < 0.02:
                    full_match[cand].append(round(root, 8))
    tpar = spec["param"]
    assert full_match[tpar], f"{tid}: 真参数 {tpar} 复原失败"
    assert all(abs(r - p[idx]) / abs(p[idx]) < 1e-3 for r in full_match[tpar]), \
        f"{tid}: 真参数复原值偏离真值: {full_match[tpar]} vs {p[idx]}"
    for c in spec["candidates"]:
        if c != tpar:
            assert not full_match[c], \
                f"{tid}: 候选 {c} 也能同时复现 ωn/ζ（判别歧义）: {full_match[c]}"
    return dict(true_modes=true_m, bad_modes=bad_m, corrupted=corrupted,
                true_value=p[idx], param=tpar)


def _expm(A: np.ndarray) -> np.ndarray:
    try:
        from scipy.linalg import expm as _s
        return _s(A)
    except Exception:  # noqa: BLE001 — scipy 缺席时用可对角化近似（本任务矩阵均非亏损）
        w, V = np.linalg.eig(A)
        assert np.linalg.cond(V) < 1e8, "expm 回退不可用（矩阵近亏损）"
        return (V * np.exp(w)) @ np.linalg.inv(V)


def np_tdm(A, B, C) -> dict:
    """F5 钉死口径的 numpy 复算（与 gold MATLAB 同公式）。"""
    n = A.shape[0]
    N = int(round(T_END / DT))
    Ad = _expm(A * DT)
    Bd = np.linalg.solve(A, (Ad - np.eye(n)) @ B)
    x = np.zeros((n, 1))
    y = [float((C @ x).item())]
    for _ in range(N):
        x = Ad @ x + Bd
        y.append(float((C @ x).item()))
    y = np.array(y)
    t = np.arange(N + 1) * DT
    yinf = float((-(C @ np.linalg.solve(A, B))).item())
    assert abs(yinf) > 1e-9

    def cross(fr):
        thr = fr * yinf
        for k in range(len(y) - 1):
            if (y[k] - thr) * (y[k + 1] - thr) <= 0 and y[k + 1] != y[k]:
                return t[k] + DT * (thr - y[k]) / (y[k + 1] - y[k])
        return None

    t10, t90 = cross(0.1), cross(0.9)
    assert t10 is not None and t90 is not None, "10%/90% 穿越未出现"
    viol = np.where(np.abs(y - yinf) > 0.02 * abs(yinf))[0]
    assert len(viol) and viol[-1] < 0.9 * N, "2% 带末次违例过晚（T=30s 不够）"
    os_pct = max(0.0, (y.max() - yinf) / abs(yinf) * 100)
    assert os_pct > 3.0, "overshoot 退化（<3%）"
    return dict(rise_time_s=t90 - t10, overshoot_pct=os_pct,
                settling_time_s=float(t[viol[-1]]))


def np_trim(p) -> dict:
    W, S, h, V, CLa, CL0, CD0, k, _T0, _V0 = p
    rho = RHO0 * np.exp(-h / 23800.0)
    qbar = 0.5 * rho * V * V
    CL = W / (qbar * S)
    alpha = np.degrees((CL - CL0) / CLa)
    T = qbar * S * (CD0 + k * CL * CL)
    assert 0.5 < alpha < 8 and 5000 < T < 40000 and 0.2 < CL < 0.9
    return dict(alpha_trim_deg=float(alpha), thrust_lbf=float(T))


def np_sm(p) -> dict:
    CLa, Cma, _WS, _c, hcg = p
    sm = -Cma / CLa
    assert 0.05 < sm < 0.35
    return dict(static_margin=float(sm), h_n=float(hcg + sm))


# ================================================================ 文本渲染

def fmt(v: float) -> str:
    """确定性数字字面量（repr 最短往返；MATLAB/Python 解析为同一 double）。"""
    return repr(float(v))


def m_prompt_matrix(M) -> str:
    return "\n".join("  [ " + ", ".join(fmt(v) for v in row) + " ]" for row in M)


def m_matlab(name: str, M) -> str:
    return f"{name} = [" + "; ".join(" ".join(fmt(v) for v in row) for row in M) + "];"


_PROTO = """Output contract: write `result.json` to the current working directory — a MATLAB
`jsonencode` of a top-level struct with exactly the keys listed above. Numeric keys are
graded at 1% relative tolerance; string keys must match exactly.
Execution: your script is saved as `model.m` and executed with `matlab -batch model` in an
isolated working directory (MATLAB R2026a, Control System Toolbox available). Stay
self-contained (no shell, network, or filesystem escape).
Respond with a single ```matlab code block and nothing else."""


# ---------------------------------------------------------------- F1/F7/F8

_GOLD_HEAD = "%% gold 解（gtm.transport_control / {tid}）——判分参考预计算用，模型不可见。\n" \
             "% 自包含确定性脚本：以 model.m 在隔离目录 matlab -batch model 执行，cwd 写 result.json。\n"

_GOLD_TAIL = ("fid = fopen('result.json', 'w');\n"
              "fwrite(fid, jsonencode(r));\n"
              "fclose(fid);\n")


def _gold_lon_modes(tid: str, A: np.ndarray) -> str:
    body = f"""{m_matlab('A', A)}
ev = eig(A);
lam = ev(imag(ev) > 0);            % 每对共轭取一个（结构已验证：恰两对）
[~, ord] = sort(abs(lam), 'descend');
lam = lam(ord);                    % 大模=短周期，小模=长周期
wn = abs(lam); ze = -real(lam) ./ wn;
r = struct('omega_sp', wn(1), 'zeta_sp', ze(1), 'omega_ph', wn(2), 'zeta_ph', ze(2));"""
    return _GOLD_HEAD.format(tid=tid) + body + "\n" + _GOLD_TAIL


def _prompt_lon(tid: str, A: np.ndarray) -> tuple[str, list[str]]:
    keys = ["omega_sp", "zeta_sp", "omega_ph", "zeta_ph"]
    prompt = f"""# Longitudinal modal analysis — cruise linear model ({tid})

A transport aircraft (NASA CR-2144 DC-8 class) is linearized about a steady cruise
condition. The longitudinal state is x = [u, w, q, theta] (ft/s, ft/s, rad/s, rad),
body axes, with xdot = A x and

A =
{m_prompt_matrix(A)}

The matrix has two classical complex-conjugate mode pairs. Compute the natural
frequency (rad/s) and damping ratio of each: the short-period pair and the phugoid
pair.

Write result.json with keys: omega_sp, zeta_sp (short period), omega_ph, zeta_ph
(phugoid). Numeric tolerance 1%.

{_PROTO}"""
    return prompt, keys


def _gold_env(tid: str) -> str:
    mats = [lon_A(fc[1:]) for fc in ENV[tid]]
    body = "".join(m_matlab(f"A{i}", M) + "\n" for i, M in enumerate(mats, 1))
    body += """for jj = 1:3
  if jj == 1, Acur = A1; elseif jj == 2, Acur = A2; else, Acur = A3; end
  ev = eig(Acur);
  lam = ev(imag(ev) > 0);
  [~, ord] = sort(abs(lam), 'descend');
  lam = lam(ord);
  wnv(jj) = abs(lam(1)); zev(jj) = -real(lam(1)) / abs(lam(1));
end
r = struct('omega_sp_1', wnv(1), 'zeta_sp_1', zev(1), ...
           'omega_sp_2', wnv(2), 'zeta_sp_2', zev(2), ...
           'omega_sp_3', wnv(3), 'zeta_sp_3', zev(3));"""
    return _GOLD_HEAD.format(tid=tid) + body + "\n" + _GOLD_TAIL


def _prompt_env(tid: str) -> tuple[str, list[str]]:
    keys = ["omega_sp_1", "zeta_sp_1", "omega_sp_2", "zeta_sp_2",
            "omega_sp_3", "zeta_sp_3"]
    lines = [f"""# Envelope robustness — short-period modes across three flight conditions

The same transport airframe is linearized ({tid}) about three cruise flight
conditions of its operating envelope. The longitudinal state is x = [u, w, q, theta]
(ft/s, ft/s, rad/s, rad), xdot = A x, with"""]
    for i in (1, 2, 3):
        fc = ENV[tid][i - 1]
        alt, V = fc[:2]
        lines.append(f"""
FC{i}: altitude {alt} ft, true airspeed {V} ft/s
A{i} =
{m_prompt_matrix(lon_A(fc[1:]))}""")
    lines.append(f"""
Compute the short-period natural frequency (rad/s) and damping ratio at each flight
condition.

Write result.json with keys: omega_sp_1, zeta_sp_1, omega_sp_2, zeta_sp_2,
omega_sp_3, zeta_sp_3. Numeric tolerance 1%.

{_PROTO}""")
    return "".join(lines), keys


def _gold_lat(tid: str, A: np.ndarray) -> str:
    body = f"""{m_matlab('A', A)}
ev = eig(A);
cpx = ev(imag(ev) > 0);            % 荷兰滚对（结构已验证：恰一对）
rl  = ev(abs(imag(ev)) < 1e-9);    % 两个实根（结构已验证）
lam = cpx(1);
wn_dr = abs(lam); z_dr = -real(lam) / wn_dr;
roll_lam = min(real(rl)); spiral_lam = max(real(rl));
r = struct('dutch_roll_omega', wn_dr, 'dutch_roll_zeta', z_dr, ...
           'roll_mode_lambda', roll_lam, 'spiral_mode_lambda', spiral_lam);"""
    return _GOLD_HEAD.format(tid=tid) + body + "\n" + _GOLD_TAIL


def _prompt_lat(tid: str, A: np.ndarray) -> tuple[str, list[str]]:
    keys = ["dutch_roll_omega", "dutch_roll_zeta", "roll_mode_lambda", "spiral_mode_lambda"]
    prompt = f"""# Lateral-directional modal analysis ({tid})

The lateral-directional state of a transport aircraft at cruise is
x = [beta, p, r, phi] (rad, rad/s, rad/s, rad) with xdot = A x and

A =
{m_prompt_matrix(A)}

The matrix has one complex-conjugate pair (Dutch roll) and two real roots (roll
convergence and spiral). Compute: dutch_roll_omega (rad/s) and dutch_roll_zeta for
the Dutch roll pair; roll_mode_lambda and spiral_mode_lambda — the REAL eigenvalues
themselves (not time constants; roll convergence is the more negative root).

Write result.json with keys: dutch_roll_omega, dutch_roll_zeta, roll_mode_lambda,
spiral_mode_lambda. Numeric tolerance 1%.

{_PROTO}"""
    return prompt, keys


# ---------------------------------------------------------------- F2/F3

def _gold_trim(tid: str) -> str:
    W, S, h, V, CLa, CL0, CD0, k, _T0, _V0 = TRIM[tid]
    body = f"""W = {fmt(W)}; S = {fmt(S)}; h = {fmt(h)}; V = {fmt(V)};
CLa = {fmt(CLa)}; CL0 = {fmt(CL0)}; CD0 = {fmt(CD0)}; kk = {fmt(k)};
rho0 = {fmt(RHO0)};
rho = rho0 * exp(-h / 23800.0);
qbar = 0.5 * rho * V^2;
CLfun = @(al) CL0 + CLa * al;          % alpha in rad
al = fzero(@(a) qbar * S * CLfun(a) - W, deg2rad(2.0));   % L = W
CL = CLfun(al);
CD = CD0 + kk * CL^2;
Thr = qbar * S * CD;                   % 定直平飞 D = T
r = struct('alpha_trim_deg', rad2deg(al), 'thrust_lbf', Thr);"""
    return _GOLD_HEAD.format(tid=tid) + body + "\n" + _GOLD_TAIL


def _prompt_trim(tid: str) -> tuple[str, list[str]]:
    W, S, h, V, CLa, CL0, CD0, k, T0, V0 = TRIM[tid]
    keys = ["alpha_trim_deg", "thrust_lbf"]
    prompt = f"""# Steady level-flight trim — transport aircraft ({tid})

Given (transport cruise class):
  weight W = {fmt(W)} lbf; wing area S = {fmt(S)} ft^2; altitude h = {fmt(h)} ft;
  true airspeed V = {fmt(V)} ft/s;
  lift curve CL = CL0 + CLalpha * alpha with CL0 = {fmt(CL0)}, CLalpha = {fmt(CLa)} /rad
  (alpha in rad); parabolic drag polar CD = CD0 + k * CL^2 with CD0 = {fmt(CD0)},
  k = {fmt(k)};
  simple exponential atmosphere: rho(h) = rho0 * exp(-h/23800), rho0 = {fmt(RHO0)}
  slug/ft^3, so dynamic pressure qbar = 0.5 * rho * V^2;
  engine model: thrust available T(V) = T0 * (V/V0)^0.8 * delta_t with T0 = {fmt(T0)} lbf
  at V0 = {fmt(V0)} ft/s and throttle delta_t adjustable in [0, 1].

Solve the steady level-flight trim (lift equals weight, drag equals thrust) for the
two unknowns: angle of attack and required thrust.

Write result.json with keys: alpha_trim_deg (trim angle of attack, degrees),
thrust_lbf (required thrust, lbf). Numeric tolerance 1%.

{_PROTO}"""
    return prompt, keys


def _gold_sm(tid: str) -> str:
    CLa, Cma, _WS, _c, hcg = SM[tid]
    body = f"""CLa = {fmt(CLa)}; Cma = {fmt(Cma)}; hcg = {fmt(hcg)};
sm = -Cma / CLa;          % 静稳定裕度（无量纲，弦长分数）
hn = hcg + sm;            % 中性点位置
r = struct('static_margin', sm, 'h_n', hn);"""
    return _GOLD_HEAD.format(tid=tid) + body + "\n" + _GOLD_TAIL


def _prompt_sm(tid: str) -> tuple[str, list[str]]:
    CLa, Cma, WS, c, hcg = SM[tid]
    keys = ["static_margin", "h_n"]
    prompt = f"""# Static margin and neutral point ({tid})

A transport aircraft configuration is defined by:
  lift-curve slope CLalpha = {fmt(CLa)} /rad; pitching-moment slope Cmalpha = {fmt(Cma)} /rad;
  wing loading W/S = {fmt(WS)} lbf/ft^2; mean aerodynamic chord c = {fmt(c)} ft;
  center-of-gravity position h_cg = {fmt(hcg)} (fraction of mean aerodynamic chord).

Using the classical linear relation for static longitudinal stability,
static margin = -Cmalpha / CLalpha, and neutral point h_n = h_cg + static_margin:

Write result.json with keys: static_margin (dimensionless), h_n (neutral point,
fraction of MAC). Numeric tolerance 1%.

{_PROTO}"""
    return prompt, keys


# ---------------------------------------------------------------- F4

def _gold_kdesign(tid: str) -> str:
    Zde, Mde, wn_cl, z_cl = KD_B[tid]
    A = lon_A(LON[tid])
    B = np.array([[0.0], [Zde], [Mde], [0.0]])
    body = f"""{m_matlab('A', A)}
{m_matlab('B', B)}
wn_cl = {fmt(wn_cl)}; z_cl = {fmt(z_cl)};
ev = eig(A);
lam = ev(imag(ev) > 0);
[~, ord] = sort(abs(lam), 'descend');
lam = lam(ord);
ph = lam(2);                                   % 长周期对（保持不动）
sp_cl = -z_cl * wn_cl + 1i * wn_cl * sqrt(1 - z_cl^2);
K = place(A, B, [ph; conj(ph); sp_cl; conj(sp_cl)]);
evcl = eig(A - B * K);
lamcl = evcl(imag(evcl) > 0);
[~, ordc] = sort(abs(lamcl), 'descend');
lamcl = lamcl(ordc);
wn1 = abs(lamcl(1)); ze1 = -real(lamcl(1)) / wn1;
r = struct('cl_omega_sp', wn1, 'cl_zeta_sp', ze1);"""
    return _GOLD_HEAD.format(tid=tid) + body + "\n" + _GOLD_TAIL


def _prompt_kdesign(tid: str) -> tuple[str, list[str]]:
    Zde, Mde, wn_cl, z_cl = KD_B[tid]
    A = lon_A(LON[tid])
    B = np.array([[0.0], [Zde], [Mde], [0.0]])
    keys = ["cl_omega_sp", "cl_zeta_sp"]
    prompt = f"""# Short-period pole placement by elevator state feedback ({tid})

A transport aircraft longitudinal model x = [u, w, q, theta] (ft/s, ft/s, rad/s, rad)
has xdot = A x + B delta_e with elevator input and

A =
{m_prompt_matrix(A)}

B =
{m_prompt_matrix(B)}

Design a full-state feedback u = -K x placing the CLOSED-LOOP short-period poles at
natural frequency wn = {fmt(wn_cl)} rad/s with damping zeta = {fmt(z_cl)}, while keeping
the phugoid poles at their open-loop values.

Any gain K that achieves the target closed-loop poles scores — grading uses the
closed-loop eigenvalues, not K. Compute the achieved closed-loop short-period pair
from eig(A - B*K).

Write result.json with keys: cl_omega_sp (achieved closed-loop short-period natural
frequency, rad/s), cl_zeta_sp (achieved damping). Numeric tolerance 1%.

{_PROTO}"""
    return prompt, keys


# ---------------------------------------------------------------- F5

def _gold_tdm(tid: str) -> str:
    At, Bt, Ct = TDM[tid]
    A = np.array(At, float)
    B = np.array(Bt, float).reshape(-1, 1)
    C = np.array(Ct, float).reshape(1, -1)
    n = A.shape[0]
    body = f"""{m_matlab('A', A)}
{m_matlab('B', B)}
{m_matlab('C', C)}
dt = {fmt(DT)}; Tend = {fmt(T_END)}; N = round(Tend / dt);
Ad = expm(A * dt);
Bd = A \\ ((Ad - eye({n})) * B);
x = zeros({n}, 1); y = zeros(N + 1, 1); y(1) = C * x;
for kk = 1:N
  x = Ad * x + Bd;
  y(kk + 1) = C * x;
end
yinf = -(C * (A \\ B)); yinf = yinf(1);
t = (0:N)' * dt;
t10 = NaN; t90 = NaN;
for kk = 1:N
  if isnan(t10) && (y(kk) - 0.1 * yinf) * (y(kk + 1) - 0.1 * yinf) <= 0 && y(kk + 1) ~= y(kk)
    t10 = t(kk) + dt * (0.1 * yinf - y(kk)) / (y(kk + 1) - y(kk));
  end
  if isnan(t90) && (y(kk) - 0.9 * yinf) * (y(kk + 1) - 0.9 * yinf) <= 0 && y(kk + 1) ~= y(kk)
    t90 = t(kk) + dt * (0.9 * yinf - y(kk)) / (y(kk + 1) - y(kk));
  end
end
overshoot = (max(y) - yinf) / abs(yinf) * 100;
band = 0.02 * abs(yinf);
viol = find(abs(y - yinf) > band);
tset = t(viol(end));
r = struct('rise_time_s', t90 - t10, 'overshoot_pct', overshoot, 'settling_time_s', tset);"""
    return _GOLD_HEAD.format(tid=tid) + body + "\n" + _GOLD_TAIL


def _prompt_tdm(tid: str) -> tuple[str, list[str]]:
    At, Bt, Ct = TDM[tid]
    A = np.array(At, float)
    B = np.array(Bt, float).reshape(-1, 1)
    C = np.array(Ct, float).reshape(1, -1)
    keys = ["rise_time_s", "overshoot_pct", "settling_time_s"]
    prompt = f"""# Closed-loop step-response metrics ({tid})

A closed-loop pitch-axis tracking loop is given by xdot = A_cl x + B_cl u, y = C_cl x
(x(0) = 0), with a unit step input u = 1 applied at t = 0.

A_cl =
{m_prompt_matrix(A)}

B_cl =
{m_prompt_matrix(B)}

C_cl =
{m_prompt_matrix(C)}

Compute rise time (10%-90%), percent overshoot, and 2% settling time of y(t) using
EXACTLY this pinned simulation protocol (so results are unique):
  - exact zero-order-hold discretization: Ad = expm(A_cl*dt), Bd = A_cl \\ ((Ad - I)*B_cl),
    x[k+1] = Ad*x[k] + Bd (u = 1 for all steps), dt = 0.01 s, T = 30 s;
  - y_inf = -C_cl * (A_cl \\ B_cl) (DC value);
  - rise_time_s: from the first 10% to the first 90% crossing of y_inf, with linear
    interpolation between grid samples;
  - overshoot_pct = (max(y) - y_inf)/|y_inf| * 100;
  - settling_time_s: time of the LAST grid sample where |y - y_inf| > 0.02*|y_inf|.

Write result.json with keys: rise_time_s (s), overshoot_pct (%), settling_time_s (s).
Numeric tolerance 1%.

{_PROTO}"""
    return prompt, keys


# ---------------------------------------------------------------- F6

def _gold_repair(tid: str) -> str:
    spec = REPAIR[tid]
    p = LON[spec["base"]]
    idx = _LON_IDX[spec["param"]]
    A_true = lon_A(p)
    val = p[idx]
    ref = v_lon(A_true, tid)
    body = f"""% 真机构纵向模型（修复后）；损坏参数 {spec['param']} 的正确值 = {fmt(val)}。
{m_matlab('A_true', A_true)}
ev = eig(A_true);
lam = ev(imag(ev) > 0);
[~, ord] = sort(abs(lam), 'descend');
lam = lam(ord);
wn = abs(lam); ze = -real(lam) ./ wn;
% 复核：修复后 SP 模态与题面参考一致（wn(1)=omega_sp, ze(1)=zeta_sp）
assert(abs(wn(1) - {fmt(ref['omega_sp'])}) < 1e-6);
assert(abs(ze(1) - {fmt(ref['zeta_sp'])}) < 1e-6);
r = struct('corrupted_param', '{spec["param"]}', 'restored_value', {fmt(val)});"""
    return _GOLD_HEAD.format(tid=tid) + body + "\n" + _GOLD_TAIL


def _prompt_repair(tid: str) -> tuple[str, list[str]]:
    spec = REPAIR[tid]
    p = LON[spec["base"]]
    idx = _LON_IDX[spec["param"]]
    q = list(p)
    q[idx] = spec["factor"] * p[idx]
    A_bad = lon_A(tuple(q))
    tm = v_lon(lon_A(p), f"{tid}/prompt")
    keys = ["corrupted_param", "restored_value"]
    prompt = f"""# Corrupted stability derivative repair ({tid})

A longitudinal linear model x = [u, w, q, theta] (ft/s, ft/s, rad/s, rad),
xdot = A x, was assembled for a transport at cruise, but exactly ONE of the stability
derivatives Mw or Mq was corrupted (its value was scaled by a constant factor). The
matrix as assembled is

A_corrupt =
{m_prompt_matrix(A_bad)}

(The physical row structure is udot = Xu*u + Xw*w - g*theta, wdot = Zu*u + Zw*w + V*q,
qdot = Mw*w + Mq*q, theta_dot = q, g = 32.174 ft/s^2 — so Mw is the (3,2) entry and
Mq the (3,3) entry.)

An independent modal-identification test of the TRUE (uncorrupted) aircraft gave:
  short period: omega_sp = {tm['omega_sp']:.6g} rad/s, zeta_sp = {tm['zeta_sp']:.6g};
  phugoid:      omega_ph = {tm['omega_ph']:.6g} rad/s, zeta_ph = {tm['zeta_ph']:.6g}.

Determine which parameter (Mw or Mq) was corrupted and its correct value (the value
that restores the reference modal data).

Write result.json with keys: corrupted_param (exact string 'Mw' or 'Mq'),
restored_value (the correct value of that parameter). corrupted_param is graded by
exact string match; restored_value at 1% relative tolerance.

{_PROTO}"""
    return prompt, keys


# ================================================================ 任务装配

TASK_ORDER = (
    [f"lon_{i:02d}" for i in range(1, 6)]
    + [f"trim_{i:02d}" for i in range(1, 4)]
    + [f"sm_{i:02d}" for i in range(1, 3)]
    + [f"kdesign_{i:02d}" for i in range(1, 5)]
    + [f"tdm_{i:02d}" for i in range(1, 4)]
    + [f"repair_{i:02d}" for i in range(1, 3)]
    + [f"env_{i:02d}" for i in range(1, 4)]
    + [f"lat_{i:02d}" for i in range(1, 4)]
)

FAMILY_OF = {**{f"lon_{i:02d}": "F1" for i in range(1, 6)},
             **{f"trim_{i:02d}": "F2" for i in range(1, 4)},
             **{f"sm_{i:02d}": "F3" for i in range(1, 3)},
             **{f"kdesign_{i:02d}": "F4" for i in range(1, 5)},
             **{f"tdm_{i:02d}": "F5" for i in range(1, 4)},
             **{f"repair_{i:02d}": "F6" for i in range(1, 3)},
             **{f"env_{i:02d}": "F7" for i in range(1, 4)},
             **{f"lat_{i:02d}": "F8" for i in range(1, 4)}}


def build_task(tid: str) -> dict:
    """返回 {tid, family, keys, exact_keys, prompt, gold, np_ref}（全部确定性）。"""
    fam = FAMILY_OF[tid]
    if fam == "F1":
        A = lon_A(LON[tid])
        prompt, keys = _prompt_lon(tid, A)
        gold = _gold_lon_modes(tid, A)
        np_ref = v_lon(A, tid)
    elif fam == "F2":
        prompt, keys = _prompt_trim(tid)
        gold = _gold_trim(tid)
        np_ref = np_trim(TRIM[tid])
    elif fam == "F3":
        prompt, keys = _prompt_sm(tid)
        gold = _gold_sm(tid)
        np_ref = np_sm(SM[tid])
    elif fam == "F4":
        prompt, keys = _prompt_kdesign(tid)
        gold = _gold_kdesign(tid)
        Zde, Mde, wn_cl, z_cl = KD_B[tid]
        A, B = lon_A(LON[tid]), np.array([[0.0], [Zde], [Mde], [0.0]])
        ctrb = np.hstack([B, A @ B, np.linalg.matrix_power(A, 2) @ B,
                          np.linalg.matrix_power(A, 3) @ B])
        assert np.linalg.matrix_rank(ctrb) == 4, f"{tid}: (A,B) 不可控"
        try:    # scipy 可用时以 place_poles 复核目标可达（gold 实跑以 MATLAB place 为准）
            from scipy.signal import place_poles as _pp
            v_lon(A, tid)
            ev = np.linalg.eigvals(A)
            ph = ev[np.imag(ev) > 0]
            ph = ph[np.argsort(np.abs(ph))[::-1]][1]
            tgt = np.array([ph, np.conj(ph),
                            -z_cl * wn_cl + 1j * wn_cl * np.sqrt(1 - z_cl ** 2),
                            -z_cl * wn_cl - 1j * wn_cl * np.sqrt(1 - z_cl ** 2)])
            K = _pp(A, B, tgt).gain_matrix
            evcl = np.linalg.eigvals(A - B @ K)
            sp = evcl[np.imag(evcl) > 0]
            sp = sp[np.argsort(np.abs(sp))[::-1]][0]
            np_ref = dict(cl_omega_sp=float(abs(sp)), cl_zeta_sp=float(-sp.real / abs(sp)))
            assert abs(np_ref["cl_omega_sp"] - wn_cl) < 1e-6, f"{tid}: place 复核 ωn 偏离目标"
            assert abs(np_ref["cl_zeta_sp"] - z_cl) < 1e-6, f"{tid}: place 复核 ζ 偏离目标"
        except ImportError:
            np_ref = dict(cl_omega_sp=wn_cl, cl_zeta_sp=z_cl)
    elif fam == "F5":
        prompt, keys = _prompt_tdm(tid)
        gold = _gold_tdm(tid)
        At, Bt, Ct = TDM[tid]
        np_ref = np_tdm(np.array(At, float),
                        np.array(Bt, float).reshape(-1, 1),
                        np.array(Ct, float).reshape(1, -1))
    elif fam == "F6":
        prompt, keys = _prompt_repair(tid)
        gold = _gold_repair(tid)
        rep = v_repair(tid)
        np_ref = dict(corrupted_param=rep["param"], restored_value=rep["true_value"])
    elif fam == "F7":
        prompt, keys = _prompt_env(tid)
        gold = _gold_env(tid)
        np_ref = {}
        for i in (1, 2, 3):
            m = v_lon(lon_A(ENV[tid][i - 1][1:]), f"{tid}/fc{i}")
            np_ref[f"omega_sp_{i}"] = m["omega_sp"]
            np_ref[f"zeta_sp_{i}"] = m["zeta_sp"]
    elif fam == "F8":
        A = lat_A(LAT[tid])
        prompt, keys = _prompt_lat(tid, A)
        gold = _gold_lat(tid, A)
        np_ref = v_lat(A, tid)
    else:
        raise ValueError(fam)
    exact_keys = ["corrupted_param"] if fam == "F6" else []
    assert set(np_ref) == set(keys), f"{tid}: np_ref 键 {sorted(np_ref)} != keys {sorted(keys)}"
    return dict(tid=tid, family=fam, keys=keys, exact_keys=exact_keys,
                prompt=prompt, gold=gold, np_ref=np_ref)


# ================================================================ gold 预计算

def run_gold(code: str) -> tuple[dict, float]:
    """与判分 oracle 完全同路径：临时目录写 model.m，matlab -batch model。"""
    from .solvers.matlab import run_matlab
    with tempfile.TemporaryDirectory(prefix="gtm_gold_") as td:
        (Path(td) / "model.m").write_text(code, encoding="utf-8")
        rr = run_matlab(td, "model", GOLD_TIMEOUT_S)
        if rr["timeout"] or rr["exit"] != 0:
            raise RuntimeError(f"gold 失败 exit={rr['exit']} timeout={rr['timeout']}\n"
                               f"{rr['stdout_tail'][-800:]}")
        refs = json.loads((Path(td) / "result.json").read_text(encoding="utf-8"))
    return refs, rr["duration_s"]


# ================================================================ YAML / PROVENANCE

def build_spec(t: dict, refs: dict) -> dict:
    return {
        "id": f"gtm_{t['tid']}",
        "registry_id": REGISTRY_ID,
        "domain": "flight_control",
        "task_type": "simulation_agent",
        "model_profile": "plain_llm",
        "assets_revision": ASSETS_REVISION,
        "environment_digest": "computed-at-runtime",
        "hidden": False,
        "allowed_tools": ["matlab"],
        "input": {
            "prompt_file": f"tasks/gtm.transport_control/gtm_{t['tid']}.md",
            "prompt_sha256": hashlib.sha256(t["prompt"].encode()).hexdigest(),
            "assets": [],
        },
        "output_contract": ["result.json"],
        "reference": {
            "source": "gold 脚本预计算（MATLAB R2026a -batch，确定性；自建任务）",
            "revision": ASSETS_REVISION,
            "values": {k: refs[k] for k in t["keys"]},
            "rel_tol": REL_TOL,
            "uncertainty_note": "确定性特征值/钉死协议口径计算；容差覆盖数值口径差",
        },
        "grader": {
            "answer_format": "matlab",
            "exec_kind": "gtm_matlab",
            "validity_gate": True,
            "result_keys": t["keys"],
            "numeric_rel_tol": REL_TOL,
            "exact_keys": t["exact_keys"],
            "solver_backend": "matlab-batch-r2026a",
            "oracle_source": f"data/gtm/transport_control/gold/{t['tid']}.m",
            "sandbox": {"banned": "shell/network/process", "isolated_interpreter": True},
        },
        "scoring": {
            "weights": {"physics": 0.5, "requirements": 0.5,
                        "objective": 0.0, "robustness": 0.0},
            "note": "physics=数值字段命中均值（1% 容差）；requirements=result.json 键完备",
        },
        "limits": {"cpu": 1, "memory_gb": 4, "wall_clock_s": 900, "attempts": 3},
        "license_provenance": {
            "source": "自建（受 NASA GTM 定位启发，未镜像 GTM_DesignSim）",
            "license": "self-built",
            "status": "confirmed-selfbuilt",
            "mirror_allowed": True,
            "revision": ASSETS_REVISION,
        },
    }


_PROVENANCE = """# gtm.transport_control 数据溯源（PROVENANCE，自建任务集）

> assets_revision: `gtm-flight@selfbuilt-2026-08-22+matlabR2026a`
> 建集日期: 2026-08-22 · batch-2 会话（dev 终端）

## 自建声明

- **未镜像 GTM_DesignSim**：其本体是 Simulink 工程（工程级依赖）且整体许可
  needs-verification 未核——本任务集不复制其任何文件、参数表或题面。仅"运输机飞控
  定位"受其启发（registry `self_built: true`）。
- **稳定性导数量级取自公开运输机文献典型值**（Heffley NASA CR-2144 DC-8 类巡航量级：
  V 600-820 ft/s、Xu∈[-0.02,-0.005]、Xw∈[0.02,0.06]、Zu∈[-0.05,-0.01]、Zw∈[-0.9,-0.5]、
  Mw∈[-0.008,-0.002]、Mq∈[-1.2,-0.5]；横航向按模态窗口反解最终系数）。任务文本、
  参数组合、判分口径全部自建。
- **判分 100% 本地数值可复现**：每题参考值 = 自建 gold MATLAB 脚本（`gold/<tid>.m`）
  以 `matlab -batch model` 预计算落盘 `references/<tid>.json` 并内嵌任务 YAML；
  numpy 侧独立复算（<1e-6 相对差）防口径漂移。无 LLM judge。

## 环境事实（2026-08-22 实测）

- MATLAB `/Applications/MATLAB_R2026a.app/bin/matlab`（R2026a Update 3，Sponsored
  License）；batch 启动 ~28s/次（任务规格给定事实；本机建集实测单次调用
  10-30s 量级，含许可横幅写 stderr，不影响退出码）。
- 依赖函数面：`eig`/`expm`/`fzero`/`jsonencode` 核心函数 + `place`/`ctrb`
  （Control System Toolbox）。无 Optimization Toolbox 依赖（fsolve 不用）。
- 判分管线：runners/simulation_agent.py `grader.exec_kind=gtm_matlab` 分支
  （模型代码以 model.m 隔离目录执行，写 result.json 判分，口径同 aviary 分支：
  result_keys + numeric_rel_tol=0.01 + exact_keys）。

## 任务族清单（8 族 25 题，`tasks/gtm.transport_control/`）

| 族 | 数量 | tid | 判分键 |
| --- | --- | --- | --- |
| F1 纵向模态 | 5 | lon_01..05 | omega_sp/zeta_sp/omega_ph/zeta_ph |
| F2 配平 | 3 | trim_01..03 | alpha_trim_deg/thrust_lbf |
| F3 静稳定裕度 | 2 | sm_01..02 | static_margin/h_n |
| F4 控制律设计 | 4 | kdesign_01..04 | cl_omega_sp/cl_zeta_sp（判闭环极点不判 K） |
| F5 时域指标 | 3 | tdm_01..03 | rise_time_s/overshoot_pct/settling_time_s |
| F6 模型修复 | 2 | repair_01..02 | corrupted_param(exact)/restored_value(1%) |
| F7 包线鲁棒 | 3 | env_01..03 | 每飞行条件 omega_sp_i/zeta_sp_i（6 键） |
| F8 横航向模态 | 3 | lat_01..03 | dutch_roll_omega/zeta + roll/spiral λ |

## 模态自检与记录在案的偏差

- 生成器对写出的每个 A 强制自验（numpy eig）：纵向恰两对共轭极点、SP
  ωn∈[1.2,2.8] ζ∈[0.25,0.65]；横航向荷兰滚 ωn∈[0.8,1.8] ζ∈[0.05,0.25]、滚转
  实根∈[-2.5,-1.2]、螺旋实根∈[-0.10,-0.05]（全稳定）。
- **phugoid ωn 窗口偏差**：任务规格要求 [0.08,0.25] 且同时给定参数盒——但本结构
  char(0)=g·Zu·Mw ⇒ wn_sp·wn_ph=√(g·|Zu·Mw|)，二者数学不相容（参数盒全域 +
  SP 窗下 wn_ph≤0.06，4 万点 LHS 扫描 max 0.0496）。按"保持规格参数量级"优先，
  自检窗取物理可达包络 [0.025,0.06]（周期 105-250s），模态分离比 >40×，判分
  稳定性不受影响。F8 之 Lβ 量级（-3.9..-8.5）为满足全稳定螺旋窗所需，超出
  文献典型值——规格明示"最终系数直接写死、生成器验证模态"，模态窗口优先。
- F6 判别唯一性逐题验证：对每个候选参数在物理邻域扫 1-D 根（匹配参考 SP ωn 或
  ζ），仅真参数的复原值能同时复现参考 SP ωn 与 ζ。
- F4 判分口径（规格明示）：判闭环极点不判 K——cl_omega_sp/cl_zeta_sp 参考即
  目标值本身（place 精确配置后 eig 复核误差 <1e-6）。

## gold 预计算协议

- `python3 -m runners.gen_tasks_gtm`：渲染 gold/<tid>.m → 逐题
  `runners/solvers/matlab.py::run_matlab`（与判分 oracle 完全同路径：临时目录
  model.m + `matlab -batch model`，串行）→ result.json 即 references/<tid>.json
  → YAML reference.values 内嵌。numpy 复算逐键断言 <1e-6 相对差。
- 幂等：`--check` 对 gold/YAML/MD/references 存在性/PROVENANCE 全量逐字节比对。
- 题面仿真口径（F5）：精确零阶保持离散 Ad=expm(A·dt)、Bd=A\\((Ad−I)B)、
  dt=0.01 s、T=30 s；10-90% 上升时间线性插值、2% 带取末次违例采样时刻。

## 重取/复算

```bash
cd benchmarks && python3 -m runners.gen_tasks_gtm --check   # 幂等校验
# 参考重算（--force-refs）：重跑生成器即新评测周期
```
"""


# ================================================================ main

def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--check", action="store_true")
    ap.add_argument("--force-refs", action="store_true")
    args = ap.parse_args()

    (DATA / "gold").mkdir(parents=True, exist_ok=True)
    (DATA / "references").mkdir(parents=True, exist_ok=True)
    TASKS_DIR.mkdir(parents=True, exist_ok=True)

    t_start = time.time()
    tasks = [build_task(tid) for tid in TASK_ORDER]
    shas = [hashlib.sha256(t["prompt"].encode()).hexdigest() for t in tasks]
    assert len(set(shas)) == len(tasks), "题面重复（各任务题面必须互异）"
    # gold 静态检查（判分同款）：gold 自身绝不能触发 sandbox_escape_attempt
    from .solvers.matlab import matlab_static_check
    for t in tasks:
        viol = matlab_static_check(t["gold"])
        assert not viol, f"{t['tid']}: gold 触发静态检查 {viol}"

    if args.check:
        drift = []
        for t in tasks:
            for path, want in (
                (DATA / "gold" / f"{t['tid']}.m", t["gold"]),
                (TASKS_DIR / f"gtm_{t['tid']}.md", t["prompt"]),
            ):
                if not path.exists() or path.read_text(encoding="utf-8") != want:
                    drift.append(path.name)
            ref_path = DATA / "references" / f"{t['tid']}.json"
            if not ref_path.exists():
                drift.append(ref_path.name)
                continue
            refs = json.loads(ref_path.read_text(encoding="utf-8"))
            spec = build_spec(t, refs)
            yp = TASKS_DIR / f"gtm_{t['tid']}.yaml"
            if not yp.exists() or yp.read_text(encoding="utf-8") != \
                    yaml.safe_dump(spec, sort_keys=False, allow_unicode=True):
                drift.append(yp.name)
        prov = DATA / "PROVENANCE.md"
        if not prov.exists() or prov.read_text(encoding="utf-8") != _PROVENANCE:
            drift.append("PROVENANCE.md")
        if drift:
            print(f"[check] 不一致: {sorted(set(drift))}")
            return 1
        print(f"[check] {len(tasks)} 个任务 + PROVENANCE 全部一致")
        return 0

    n_run, durations = 0, []
    for t in tasks:
        (DATA / "gold" / f"{t['tid']}.m").write_text(t["gold"], encoding="utf-8")
        ref_path = DATA / "references" / f"{t['tid']}.json"
        if args.force_refs or not ref_path.exists():
            refs, dur = run_gold(t["gold"])
            n_run += 1
            durations.append(dur)
            ref_path.write_text(json.dumps(refs, indent=1, sort_keys=True) + "\n",
                                encoding="utf-8")
        refs = json.loads(ref_path.read_text(encoding="utf-8"))
        assert set(refs) == set(t["keys"]), \
            f"{t['tid']}: gold 输出键 {sorted(refs)} != {sorted(t['keys'])}"
        for k in t["keys"]:
            nv, gv = t["np_ref"][k], refs[k]
            if isinstance(nv, str):
                assert nv == gv, f"{t['tid']}.{k}: {gv!r} != {nv!r}"
            else:
                rel = abs(float(gv) - nv) / max(abs(nv), 1e-12)
                assert rel < 1e-6, f"{t['tid']}.{k}: MATLAB {gv} vs numpy {nv} rel={rel:.2e}"
        (TASKS_DIR / f"gtm_{t['tid']}.md").write_text(t["prompt"], encoding="utf-8")
        (TASKS_DIR / f"gtm_{t['tid']}.yaml").write_text(
            yaml.safe_dump(build_spec(t, refs), sort_keys=False, allow_unicode=True),
            encoding="utf-8")
        print(f"[gen] gtm_{t['tid']} ({t['family']}): {len(t['keys'])} keys ok")

    (DATA / "PROVENANCE.md").write_text(_PROVENANCE, encoding="utf-8")

    if n_run:
        print(f"[gold] {n_run} 题预计算 {sum(durations):.1f}s "
              f"(min {min(durations):.1f} / max {max(durations):.1f} / "
              f"mean {sum(durations)/len(durations):.1f})")
    print(f"[gen] {len(tasks)} tasks -> {TASKS_DIR}  (total {time.time()-t_start:.1f}s)")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
