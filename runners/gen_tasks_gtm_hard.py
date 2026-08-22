"""gen_tasks_gtm_hard.py — gtm 加硬版 v2 MATLAB 飞控任务集（17 题；2026-08-23）.

gtm.transport_control_hard —— gtm.transport_control 的判分加硬版。v1（25 题）给了
双模型近饱和基线（M3 0.98 / GLM 0.89）：题面直接给 A 矩阵、只需 eig/place/fzero，
教科书级数值计算即可满分。v2 目标：把双模型压入 ≤0.7 区分带，考「工程判断 +
数据处理」而非「会用计算器」。

产出（幂等；参考值由 gold 脚本 MATLAB 预计算锁定）：
  data/gtm/transport_control_hard/{gold/,references/,hidden/,PROVENANCE.md}
  + 任务 YAML/MD（tasks/gtm.transport_control_hard/gtmh_<tid>.{yaml,md}）

任务协议：与 v1 完全相同的 gtm_matlab 分支——
  被测模型输出单个 ```matlab 代码块；脚本以 model.m 在隔离目录
  `matlab -batch model` 执行（R2026a，Control System Toolbox）；cwd 写 result.json
  （jsonencode 顶层对象）；数值键 1% 相对容差，exact_keys 精确匹配；
  wall_clock_s=900。

任务族（5 族 17 题；全部「工程判断/数据处理」轴，非「计算器」轴）：
  H1 含噪系统辨识 ×4（id_*）    题面给 PRBS 激励下的仿真响应序列（非 A 矩阵），
                                 LS 辨识离散 Ad 再取连续等效 SP 模态
  H2 鲁棒裕度 ×4（margin_*）    给 (A,B,C) + 已设计 K，求 gain/phase margin 与
                                crossover freq（两题单回路、两题内环+外环级联）
  H3 增益调度与多 FC 设计 ×3（gs_*）  同一气动形体 3 FC，逐 FC 独立 place 到不同
                                (ωn_i, ζ_i)，判闭环极点不判 K（同 v1 F4 协议）
  H4 非线性配平 ×3（trimnl_*）  定常爬升/转弯配平，非线性耦合（CD=CD0+k·CL²、
                                推力安装角 i_T 力矩、坡度 φ、爬升率），fzero 解
                                2-3 元方程组
  H5 蒙特卡洛鲁棒筛选 ×3（mc_*） 给 Mw/Zw 等导数 ±盒不确定性，200 个 seeded 确定性
                                采样点下判闭环 SP 落入 [a,b]×ζ≥c 的占比 + 失败数

自检（生成器强制，不满足即抛错）：
  - H1：gold 用同一 LS 管线复算参考值，逐键断言与解析真值 <0.3% 相对差（题面写明
    管线与参数口径，不给中间量）。
  - H2：每题的回路 margin 有限且非退化（gm 非 Inf、crossover 若在带宽内存在）。
  - H3：逐 FC 断言 (A,B) 可控、place 目标配置后 eig 复核 <1e-6。
  - H4：gold 的解复核残差 <1e-8，且 α/推力/载荷因数落在物理窗内。
  - H5：200 点采样 pass_fraction ∈ (0,1) 非平凡（既非全过也非全挂）。

记录在案的偏差（见 PROVENANCE）：
  - H1 噪声级取 2e-4~5e-4（非规格口头 1e-3~1e-2）：SP-ζ 辨识对噪声极敏感，1e-3 时
    ζ 误差 >2%，违反「gold <0.3% 且键 1% 可判」——取噪声上限使 ωn/ζ 双键在 1%
    容差内稳定可复现；加硬点从「噪声量级」转为「完整辨识管线结构」。
  - H1 只判 SP 对：长周期（phugoid）离散极点紧贴单位圆（|λ|≈1.0），任意噪声都使其
    塌到实轴，8-20s 数据不可辨识——与 v1 记录的 phugoid 窗口偏差同源，结构必然。

用法：python3 -m runners.gen_tasks_gtm_hard [--check] [--force-refs]
"""

from __future__ import annotations

import argparse
import base64
import hashlib
import json
import tempfile
import time
from pathlib import Path

import numpy as np
import yaml

BENCH = Path(__file__).resolve().parent.parent
DATA = BENCH / "data/gtm/transport_control_hard"
TASKS_DIR = BENCH / "tasks/gtm.transport_control_hard"
ASSETS_REVISION = "gtm-hard@selfbuilt-2026-08-23+matlabR2026a"
REGISTRY_ID = "gtm.transport_control_hard"
REL_TOL = 0.01
GOLD_TIMEOUT_S = 300.0

G = 32.174
RHO0 = 0.0023769

# 模态/参数物理量级取自公开运输机文献典型值（Heffley NASA CR-2144 DC-8 类巡航），
# 与 v1 同源：V 600-820 ft/s、Xu∈[-0.02,-0.005]、Xw∈[0.02,0.06]、Zu∈[-0.05,-0.01]、
# Zw∈[-0.9,-0.5]、Mw∈[-0.008,-0.002]、Mq∈[-1.2,-0.5]。SP 窗 ωn∈[1.2,2.8] ζ∈[0.25,0.65]。

# ================================================================ 参数表（写死，无 rng）

def lon_A(p: tuple) -> np.ndarray:
    """纵向 4 状态 x=[u w q θ]，A=[[Xu,Xw,0,-g],[Zu,Zw,V,0],[0,Mw,Mq,0],[0,0,1,0]]。"""
    V, Xu, Xw, Zu, Zw, Mw, Mq = p
    return np.array([[Xu, Xw, 0.0, -G], [Zu, Zw, V, 0.0],
                     [0.0, Mw, Mq, 0.0], [0.0, 0.0, 1.0, 0.0]])


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


def v_lon(A: np.ndarray, tag: str) -> dict:
    pairs, reals = eig_pairs_reals(A)
    assert pairs is not None and len(pairs) == 2 and not reals, \
        f"{tag}: 非两对共轭极点 ({pairs}, {reals})"
    (wsp, zsp), (wph, zph) = pairs
    _win(wsp, 1.2, 2.8, "SP wn", tag); _win(zsp, 0.25, 0.65, "SP zeta", tag)
    return dict(omega_sp=wsp, zeta_sp=zsp, omega_ph=wph, zeta_ph=zph)


# ---------------------------------------------------------------- H1 含噪系统辨识

# H1 每题：真纵向 A（连续）+ 升力舵面 B=[0;Zde;Mde;0] + 辨识口径
# (V, Xu, Xw, Zu, Zw, Mw, Mq, Zde, Mde, noise_sigma, N_steps, seed, shape)
# shape 恒为 '4ch'：u/w/q/θ 四通道（含噪量测）——加硬点在辨识管线结构，非通道缺失。
H1: dict[str, tuple] = {
    "id_01": (700, -0.0068, 0.040, -0.034, -0.73, -0.0054, -0.92,
              -6.0, -4.0, 2e-4, 600, 20260823, "4ch"),
    "id_02": (720, -0.0058, 0.048, -0.042, -0.85, -0.0065, -1.08,
              -5.0, -5.5, 3e-4, 800, 20260824, "4ch"),
    "id_03": (745, -0.0055, 0.030, -0.025, -0.62, -0.0042, -0.75,
              -7.5, -3.0, 3e-4, 700, 20260825, "4ch"),
    "id_04": (770, -0.0062, 0.028, -0.022, -0.58, -0.0038, -0.68,
              -4.5, -2.5, 1e-4, 1500, 20260826, "4ch"),
}

# H1 离散化/激励口径（钉死，写进题面）
H1_DT = 0.02
H1_PRBS = dict(amp=0.05, min_hold=8, x0=(0.0, 0.0, 0.0, 0.0))


def _expm(A: np.ndarray) -> np.ndarray:
    try:
        from scipy.linalg import expm as _s
        return _s(A)
    except Exception:  # noqa: BLE001
        w, V = np.linalg.eig(A)
        assert np.linalg.cond(V) < 1e8, "expm 回退不可用"
        return (V * np.exp(w)) @ np.linalg.inv(V)


def h1_discretize(A: np.ndarray, dt: float = H1_DT) -> np.ndarray:
    return np.asarray(_expm(A * dt)).real


def h1_input_discretize(A: np.ndarray, B: np.ndarray, dt: float = H1_DT) -> np.ndarray:
    n = A.shape[0]
    Ad = h1_discretize(A, dt)
    Bd = np.linalg.solve(A, (Ad - np.eye(n)) @ B)
    return np.real(Bd)


def h1_prbs(seed: int, N: int, amp: float, min_hold: int) -> np.ndarray:
    rng = np.random.default_rng(seed)
    raw = rng.choice([-amp, amp], size=(N + min_hold) // min_hold + 1, replace=True)
    return raw.repeat(min_hold)[:N]


def h1_simulate(seed: int, A: np.ndarray, B: np.ndarray, noise: float, N: int):
    """确定性仿真：PRBS 激励 → x[k]；量测含 rng(seed) 伪随机噪声。返回 (X_noisy, u)。"""
    n = A.shape[0]
    Ad = h1_discretize(A)
    Bd = h1_input_discretize(A, B).reshape(-1)
    u = h1_prbs(seed, N, H1_PRBS["amp"], H1_PRBS["min_hold"])
    xs = np.zeros((N, n))
    for k in range(N - 1):
        xs[k + 1] = Ad @ xs[k] + Bd * u[k]
    rng = np.random.default_rng(1000000 + seed)   # 噪声用独立种子流
    noise_mat = rng.normal(0.0, noise, size=(N, n))
    return xs + noise_mat, u


def h1_identify_sp_from_data(X_noisy: np.ndarray, u: np.ndarray, dt: float = H1_DT):
    """LS 辨识：x[k+1] = Ad x[k] + Bd u[k]（回归 [X_k, u_k]）→ eig(Ad)→s=log(λ)/dt→SP 对。

    返回 (omega_sp_id, zeta_sp_id)。SP = 最大 |s| 的共轭对（长周期对不可辨识，见 docstring）。
    """
    X1 = X_noisy[:-1]
    X2 = X_noisy[1:]
    reg = np.hstack([X1, u[:-1].reshape(-1, 1)])
    coef = np.linalg.lstsq(reg, X2, rcond=None)[0].T
    Adh = coef[:, :X1.shape[1]]
    ev = np.linalg.eigvals(Adh)
    s = np.log(ev) / dt
    lam = s[np.imag(s) > 1e-6]
    assert lam.size >= 1, "SP 共轭对不可辨识（噪声过大/数据不足）"
    lam = lam[np.argsort(-np.abs(lam))]
    return abs(lam[0]), -lam[0].real / abs(lam[0])


# ---------------------------------------------------------------- H2 鲁棒裕度

# H2 每题：串联回路 L(s)（开环传递函数，含已设计的补偿器），键 gm_db/pm_deg/w_gc/w_pc。
# 种类：'single' = 直接给 L(s) 的分子/分母系数（3 阶 type-1，有限正裕度）；
#       'cascade' = 内环（给定 G_in 与 ki 单位反馈闭合）级联外环（Kout/(s(s+aout))），
#                   内环闭环作外环前向通道——级联组合是难点。
# 参数（系数用降幂多项式）：
H2: dict[str, dict] = {
    # L = K / (s*(s+a)*(s+b)) → num=[K], den=[1, a+b, a*b, 0]
    "margin_01": {"kind": "single", "num": (1.80,), "den": (1.0, 3.0, 2.0, 0.0)},
    "margin_02": {"kind": "single", "num": (9.00,), "den": (1.0, 5.0, 6.0, 0.0)},
    # cascade: G_in=1/(s(s+ai)) 内环反馈 ki 闭合；外环 Kout/(s(s+aout))
    "margin_03": {"kind": "cascade", "ai": 4.0, "ki": 12.0, "aout": 2.0, "Kout": 2.5},
    "margin_04": {"kind": "cascade", "ai": 4.0, "ki": 9.0, "aout": 4.0, "Kout": 3.0},
}


def h2_open_loop_tf(spec: dict) -> tuple[list, list]:
    """返回开环 L(s) 的 (num, den) 降幂系数。cascade 先内环闭合再级联外环。"""
    if spec["kind"] == "single":
        return list(spec["num"]), list(spec["den"])
    # cascade：G_in=1/(s(s+ai))，内环单位反馈 ki → G_in_cl = ki/(s^2+ai*s+ki)
    ai, ki, aout, Kout = spec["ai"], spec["ki"], spec["aout"], spec["Kout"]
    # G_in_cl num=[ki], den=[1, ai, ki]；外环 Kout/(s(s+aout)) num=[Kout], den=[1,aout,0]
    # L = G_out * G_in_cl：多项式相乘（降幂卷积）
    num_out = [Kout]
    den_out = [1.0, aout, 0.0]
    num_total = np.convolve(np.array(num_out), np.array([ki])).tolist()
    den_total = np.convolve(np.array(den_out), np.array([1.0, ai, ki])).tolist()
    return num_total, den_total


# ---------------------------------------------------------------- H3 增益调度

# H3 每题：同一气动形体 3 个飞行条件 (A_i, B_i) + 各自目标闭环 SP (wn_i, ζ_i)
# 键：cl_omega_sp_i / cl_zeta_sp_i（i=1..3），判闭环极点不判 K（同 v1 F4）。
# 结构 = (V, Xu, Xw, Zu, Zw, Mw, Mq, Zde, Mde) 三套 + 三个 (wn_cl, ζ_cl)
H3: dict[str, tuple] = {
    "gs_01": (
        (740, -0.0064, 0.038, -0.031, -0.71, -0.0051, -0.90, -6.0, -4.0),
        (700, -0.0059, 0.026, -0.019, -0.55, -0.0034, -0.64, -6.0, -4.0),
        (660, -0.0057, 0.020, -0.015, -0.50, -0.0030, -0.58, -6.0, -4.0),
        ((2.0, 0.60), (1.9, 0.55), (1.7, 0.50)),
    ),
    "gs_02": (
        (720, -0.0066, 0.042, -0.036, -0.78, -0.0058, -1.00, -5.0, -5.0),
        (690, -0.0060, 0.030, -0.024, -0.60, -0.0040, -0.72, -5.0, -5.0),
        (640, -0.0059, 0.022, -0.017, -0.53, -0.0033, -0.63, -5.0, -5.0),
        ((2.2, 0.58), (2.0, 0.52), (1.8, 0.48)),
    ),
    "gs_03": (
        (700, -0.0058, 0.036, -0.029, -0.68, -0.0048, -0.86, -7.5, -3.5),
        (720, -0.0056, 0.028, -0.021, -0.58, -0.0038, -0.70, -7.5, -3.5),
        (680, -0.0055, 0.024, -0.018, -0.54, -0.0035, -0.65, -7.5, -3.5),
        ((2.4, 0.62), (2.1, 0.55), (1.9, 0.50)),
    ),
}


def h3_fc(fc: tuple) -> tuple[np.ndarray, np.ndarray]:
    """飞行条件 (V, Xu, Xw, Zu, Zw, Mw, Mq, Zde, Mde) -> (A, B)。"""
    V, Xu, Xw, Zu, Zw, Mw, Mq, Zde, Mde = fc
    A = lon_A((V, Xu, Xw, Zu, Zw, Mw, Mq))
    B = np.array([[0.0], [Zde], [Mde], [0.0]])
    return A, B


# ---------------------------------------------------------------- H4 非线性配平

# H4 每题：定常爬升 + 协调转弯配平（3 元非线性：α / 推力 T / 升降舵 δe）。
# 真 3x3 耦合（无解析闭式、无单方程可解耦）：
#   CL(α,δe)=CL0+CLa·α+CLde·δe, CD=CD0+k·CL², q̄=½ρV²
#   f1 垂直:  q̄S·CL·cosφ + T·sin(α+iT) − W·cosγ = 0
#   f2 沿航迹: T·cos(α+iT) − q̄S·CD − W·sinγ = 0
#   f3 俯仰:  q̄S·c̄·(Cm0+Cma·α+Cmde·δe) + T·sin(iT)·zT = 0
#   耦合：T 进 f3、α 与 δe 进 f1、α 进 f2——推力-阻力-升力-安装角互锁。
# 参数 = (W, S, h, V, gam_deg, phi_deg, CLa, CL0, CLde, CD0, k, iT_deg, zT,
#         cbar, Cm0, Cma, Cmde)
H4: dict[str, tuple] = {
    "trimnl_01": (230000, 2400, 31000, 730, 3.0, 30.0,
                  5.2, 0.15, 0.35, 0.021, 0.043, 2.5, 2.0, 17.0, 0.02, -0.30, -0.85),
    "trimnl_02": (280000, 2730, 35000, 780, 5.0, 40.0,
                  5.6, 0.18, 0.30, 0.019, 0.045, 3.0, 2.2, 19.5, 0.025, -0.34, -0.90),
    "trimnl_03": (200000, 2100, 27000, 700, 4.0, 25.0,
                  4.9, 0.12, 0.40, 0.023, 0.041, 2.0, 1.8, 16.0, 0.018, -0.28, -0.80),
}


def h4_residual(x: np.ndarray, p: tuple) -> np.ndarray:
    alpha, T, de = x
    (W, S, h, V, gam_deg, phi_deg, CLa, CL0, CLde, CD0, k,
     iT_deg, zT, cbar, Cm0, Cma, Cmde) = p
    rho = RHO0 * np.exp(-h / 23800.0)
    q = 0.5 * rho * V * V
    gam, phi, iT = np.radians(gam_deg), np.radians(phi_deg), np.radians(iT_deg)
    CL = CL0 + CLa * alpha + CLde * de
    CD = CD0 + k * CL * CL
    L = q * S * CL
    f1 = L * np.cos(phi) + T * np.sin(alpha + iT) - W * np.cos(gam)
    f2 = T * np.cos(alpha + iT) - q * S * CD - W * np.sin(gam)
    f3 = q * S * cbar * (Cm0 + Cma * alpha + Cmde * de) + T * np.sin(iT) * zT
    return np.array([f1, f2, f3])


def h4_trim(p: tuple) -> dict:
    """numpy 侧 H4 配平（自写 Newton；gold MATLAB 同公式），残差 <1e-10 自检。"""
    x = np.array([np.radians(3.0), 20000.0, np.radians(-1.0)], float)
    for _ in range(60):
        f = h4_residual(x, p)
        if np.linalg.norm(f) < 1e-12:
            break
        J = np.zeros((3, 3))
        eps = 1e-6
        for j in range(3):
            xp = x.copy(); xp[j] += eps
            J[:, j] = (h4_residual(xp, p) - f) / eps
        x = x + np.linalg.solve(J, -f)
    alpha, T, de = x
    assert np.linalg.norm(h4_residual(x, p)) < 1e-8, "H4 配平残差未收敛"
    gam_deg, phi_deg = p[4], p[5]
    nf = float(np.cos(np.radians(gam_deg)) / np.cos(np.radians(phi_deg)))
    assert 0.5 < np.degrees(alpha) < 10, f"alpha 出窗 {np.degrees(alpha)}"
    assert 5000 < T < 60000, f"T 出窗 {T}"
    assert abs(np.degrees(de)) < 20, f"δe 出窗 {np.degrees(de)}"
    return dict(alpha_trim_deg=float(np.degrees(alpha)),
                thrust_lbf=float(T),
                delta_e_trim_deg=float(np.degrees(de)),
                load_factor=float(nf))


# ---------------------------------------------------------------- H5 蒙特卡洛鲁棒筛选

# H5 每题：闭环 (A, B, K) + 导数盒不确定性 (Mw ±, Zw ±, Mq ±) + 采样口径 (seed, N=200)
# 判：200 个 seeded 确定性采样点下闭环 SP 满足 ωn∈[a,b] 且 ζ≥c 的占比
# 键 pass_fraction(2% 容差) + failing_case_count(exact)
# 参数 = (V, Xu, Xw, Zu, Zw, Mw, Mq, Zde, Mde, K_1..K_? , 盒百分比, wn 窗, ζ 阈值, seed)
# K 用 place 到目标 SP 实现（gold 侧同款）；盒 ±x% 对 Mw/Zw/Mq 缩放。
H5: dict[str, tuple] = {
    "mc_01": (710, -0.0066, 0.039, -0.032, -0.72, -0.0053, -0.90,
              -6.0, -4.0, (2.0, 0.60), 0.25, (1.88, 2.12), 0.51, 20260827),
    "mc_02": (740, -0.0060, 0.033, -0.027, -0.66, -0.0046, -0.78,
              -5.5, -4.5, (2.1, 0.55), 0.20, (2.00, 2.20), 0.52, 20260828),
    "mc_03": (690, -0.0070, 0.045, -0.040, -0.80, -0.0062, -1.05,
              -6.5, -5.0, (2.3, 0.58), 0.30, (2.20, 2.40), 0.55, 20260829),
}
H5_N = 200


def h5_closed_loop_sp(p: tuple, scale: tuple) -> tuple[float, float]:
    """给定 H5 参数与导数量级缩放 (f_Mw, f_Zw, f_Mq) 返回闭环 SP (ωn, ζ)。"""
    (V, Xu, Xw, Zu, Zw, Mw, Mq, Zde, Mde, tgt, _pct, wn_win, z_th, _seed) = p
    f_Mw, f_Zw, f_Mq = scale
    A = lon_A((V, Xu, Xw, Zu, factor(Zw, f_Zw), factor(Mw, f_Mw), factor(Mq, f_Mq)))
    B = np.array([[0.0], [Zde], [Mde], [0.0]])
    wn_cl, z_cl = tgt
    K = place4(A, B, wn_cl, z_cl)
    Acl = A - B @ K
    ev = np.linalg.eigvals(Acl)
    lam = ev[np.imag(ev) > 0]
    lam = lam[np.argsort(-np.abs(lam))]
    return abs(lam[0]), -lam[0].real / abs(lam[0])


def factor(v, f):
    return v * f


def place4(A, B, wn_cl, z_cl):
    """numpy 侧 place 到 SP 目标 + 保持长周期不动（与 gold MATLAB place 同构）。"""
    try:
        from scipy.signal import place_poles as _pp
        ev = np.linalg.eigvals(A)
        ph = ev[np.imag(ev) > 0]
        ph = ph[np.argsort(np.abs(ph))[::-1]][1]
        sp = -z_cl * wn_cl + 1j * wn_cl * np.sqrt(1 - z_cl ** 2)
        tgt = np.array([ph, np.conj(ph), sp, np.conj(sp)])
        return np.real(_pp(A, B, tgt).gain_matrix)
    except Exception:  # noqa: BLE001
        raise AssertionError("place4 需 scipy（生成器自检环境）")


# ================================================================ 文本渲染（同 v1 口径）

def fmt(v: float) -> str:
    return repr(float(v))


def m_prompt_matrix(M) -> str:
    return "\n".join("  [ " + ", ".join(fmt(v) for v in row) + " ]" for row in M)


def m_matlab(name: str, M) -> str:
    return f"{name} = [" + "; ".join(" ".join(fmt(v) for v in row) for row in M) + "];"


def m_col(vals) -> str:
    """MATLAB 列向量（数组 → 一列）。"""
    return "[" + "; ".join(fmt(v) for v in np.asarray(vals).reshape(-1)) + "]"


_PROTO = """Output contract: write `result.json` to the current working directory — a MATLAB
`jsonencode` of a top-level struct with exactly the keys listed above. Numeric keys are
graded at 1% relative tolerance; string keys must match exactly.
Execution: your script is saved as `model.m` and executed with `matlab -batch model` in an
isolated working directory (MATLAB R2026a, Control System Toolbox available). Stay
self-contained (no shell, network, or filesystem escape).
Respond with a single ```matlab code block and nothing else."""

_GOLD_HEAD = "%% gold 解（gtm.transport_control_hard / {tid}）——判分参考预计算用，模型不可见。\n" \
             "% 自包含确定性脚本：以 model.m 在隔离目录 matlab -batch model 执行，cwd 写 result.json。\n"
_GOLD_TAIL = ("fid = fopen('result.json', 'w');\n"
              "fwrite(fid, jsonencode(r));\n"
              "fclose(fid);\n")


# ---------------------------------------------------------------- H1 渲染

def h1_matsim_data(tid: str) -> tuple[np.ndarray, np.ndarray, np.ndarray, np.ndarray, float]:
    """返回 (X_noisy, u, A_true, B, noise) 供 prompt 与 gold 共用。"""
    (V, Xu, Xw, Zu, Zw, Mw, Mq, Zde, Mde, noise, N, seed, shape) = H1[tid]
    A = lon_A((V, Xu, Xw, Zu, Zw, Mw, Mq))
    B = np.array([[0.0], [Zde], [Mde], [0.0]])
    X, u = h1_simulate(seed, A, B, noise, N)
    return X, u, A, B, noise


def _gold_h1(tid: str) -> str:
    X, u, A, B, noise = h1_matsim_data(tid)
    (V, Xu, Xw, Zu, Zw, Mw, Mq, Zde, Mde, _n, N, seed, shape) = H1[tid]
    # 在 MATLAB 侧重建同一批带噪数据：确定性 PRBS + 噪声用固定序列。
    # 直接用 numpy 生成的数据以 MATLAB 字面量写死（题面已给数据，gold 复算同数据）。
    body = [f"X = ..."]  # placeholder
    # 简洁：gold 直接在 MATLAB 内做 LS 辨识（与模型同路径），数据从内嵌字面量读。
    Xstr = m_matlab("X", X)
    ustr = m_col(u)
    dt = fmt(H1_DT)
    body = f"""{Xstr}
u = {ustr};
dt = {dt};
% LS 辨识：x[k+1] = Ad*x[k] + Bd*u[k]
Nsteps = size(X,1);
X1 = X(1:end-1,:);
X2 = X(2:end,:);
reg = [X1, u(1:end-1)];
coef = reg \\ X2;
Ad = coef(1:4,:)';
ev = eig(Ad);
s = log(ev) / dt;
lam = s(imag(s) > 1e-6);
[~, ord] = sort(abs(lam), 'descend');
lam = lam(ord);
wn = abs(lam(1)); ze = -real(lam(1)) / wn;
r = struct('omega_sp_id', wn, 'zeta_sp_id', ze);"""
    return _GOLD_HEAD.format(tid=tid) + body + "\n" + _GOLD_TAIL


def _prompt_h1(tid: str) -> tuple[str, list[str]]:
    X, u, A, B, noise = h1_matsim_data(tid)
    (V, Xu, Xw, Zu, Zw, Mw, Mq, Zde, Mde, _n, N, seed, shape) = H1[tid]
    dt = fmt(H1_DT)
    keys = ["omega_sp_id", "zeta_sp_id"]
    n_ch = X.shape[1]
    colnames = "u, w, q, theta"
    Xstr = m_matlab("X", X)
    ustr = m_col(u)
    prompt = f"""# Noisy system identification — short-period modes from flight response data ({tid})

A transport aircraft (NASA CR-2144 DC-8 class) was flown at cruise and excited by a
known pseudo-random elevator doublet input. You are given the SAMPLED physical response
(no model matrices) sampled at dt = {dt} s for N = {N} steps. The data below is already
in MATLAB variables:
  - u is the elevator input delta_e (rad) column vector (N x 1);
  - X is the state response matrix (N x 4) with columns [u_x, w, q, theta]
    (ft/s, ft/s, rad/s, rad). Rows are time samples 1..N.

{Xstr}

{ustr}

The data was produced by zero-order-hold discretization of the continuous longitudinal
model xdot = A x + B delta_e with x = [u_x, w, q, theta], then additive white noise
(std = {fmt(noise)}) added to every channel. Identify the SHORT-PERIOD pair
(natural frequency omega_sp_id in rad/s and damping ratio zeta_sp_id) by:
  1. least-squares regression of x[k+1] = Ad x[k] + Bd delta_e[k] over the data
     (regressor [x_k, delta_e_k]; use backslash / pinv on [X(1:end-1,:), u(1:end-1)]);
  2. eig(Ad), map each discrete eigenvalue lam_d -> continuous s = log(lam_d)/dt;
  3. the short-period pair is the conjugate pair with the LARGEST |s|.
(The phugoid pair lies essentially on the unit circle and is not identifiable from
this data length — identify only the short-period pair.)

Write result.json with keys: omega_sp_id, zeta_sp_id. Numeric tolerance 1%.

{_PROTO}"""
    return prompt, keys


# ---------------------------------------------------------------- H2 渲染

def _gold_h2(tid: str) -> str:
    spec = H2[tid]
    if spec["kind"] == "single":
        num, den = list(spec["num"]), list(spec["den"])
        body = f"""num = {m_col(num)};
den = {m_col(den)};
L = tf(num', den');
[Gm, Pm, Wcg, Wcp] = margin(L);
gm_db = 20 * log10(Gm);
r = struct('gm_db', gm_db, 'pm_deg', Pm, 'w_gc', Wcg, 'w_pc', Wcp);"""
    else:
        ai, ki, aout, Kout = spec["ai"], spec["ki"], spec["aout"], spec["Kout"]
        body = f"""s = tf('s');
ai = {fmt(ai)}; ki = {fmt(ki)}; aout = {fmt(aout)}; Kout = {fmt(Kout)};
G_in = 1 / (s * (s + ai));
G_in_cl = feedback(ki * G_in, 1);        % 内环单位反馈闭合
G_out = Kout / (s * (s + aout));          % 外环
L = G_out * G_in_cl;                       % 级联总开环
[Gm, Pm, Wcg, Wcp] = margin(L);
gm_db = 20 * log10(Gm);
r = struct('gm_db', gm_db, 'pm_deg', Pm, 'w_gc', Wcg, 'w_pc', Wcp);"""
    return _GOLD_HEAD.format(tid=tid) + body + "\n" + _GOLD_TAIL


def _prompt_h2(tid: str) -> tuple[str, list[str]]:
    spec = H2[tid]
    keys = ["gm_db", "pm_deg", "w_gc", "w_pc"]
    if spec["kind"] == "single":
        num, den = list(spec["num"]), list(spec["den"])
        lines = [f"""# Robust stability margins of a designed loop ({tid})""" f"""

A flight-control loop transfer function L(s) is already designed (plant times
compensator). Its open-loop transfer function is, in descending-power polynomial form:

  numerator   num = {num}
  denominator den = {den}

so L(s) = num(s) / den(s) (den includes the integrator; this is a type-1 loop).
Compute the classical gain and phase stability margins of this loop.""",
            f"""
Write result.json with keys: gm_db (gain margin, dB), pm_deg (phase margin, degrees),
w_gc (gain crossover frequency, rad/s), w_pc (phase crossover frequency, rad/s).
Numeric tolerance 1%. (Use Control System Toolbox margin(); note gm_db must be
20*log10 of the linear gain margin.)

{_PROTO}"""]
    else:
        ai, ki, aout, Kout = spec["ai"], spec["ki"], spec["aout"], spec["Kout"]
        lines = [f"""# Robust stability margins of a cascaded (inner + outer) loop ({tid})""" f"""

A two-loop cascade controller for a transport pitch-axis is given:

  INNER loop: plant G_in(s) = 1 / (s * (s + {fmt(ai)})) with feedback gain ki = {fmt(ki)}
  (unity negative feedback, so the closed inner loop is
   G_in_cl(s) = ki * G_in(s) / (1 + ki * G_in(s))).

  OUTER loop: plant/compensator G_out(s) = {fmt(Kout)} / (s * (s + {fmt(aout)})).

The cascaded total open loop is L(s) = G_out(s) * G_in_cl(s). Close the INNER loop
first, then cascade — this combination is the hard part. Compute the gain and phase
margins of the TOTAL open loop L(s).""",
            f"""
Write result.json with keys: gm_db (gain margin, dB), pm_deg (phase margin, degrees),
w_gc (gain crossover frequency, rad/s), w_pc (phase crossover frequency, rad/s).
Numeric tolerance 1%. (Use Control System Toolbox: tf / feedback / margin;
gm_db = 20*log10 of the linear gain margin.)

{_PROTO}"""]
    return "".join(lines), keys


# ---------------------------------------------------------------- H3 渲染

def _gold_h3(tid: str) -> str:
    fc1, fc2, fc3, targets = H3[tid]
    mats = []
    for i, fc in enumerate((fc1, fc2, fc3), 1):
        A, B = h3_fc(fc)
        mats.append(m_matlab(f"A{i}", A))
        mats.append(m_matlab(f"B{i}", B))
    body = "".join(m + "\n" for m in mats)
    body += """wnt = [%s]; zet = [%s];\n""" % (
        ", ".join(fmt(t[0]) for t in targets),
        ", ".join(fmt(t[1]) for t in targets))
    body += """clw = zeros(1,3); clz = zeros(1,3);
for jj = 1:3
  if jj == 1, Acur = A1; Bcur = B1; elseif jj == 2, Acur = A2; Bcur = B2; else, Acur = A3; Bcur = B3; end
  wn = wnt(jj); ze = zet(jj);
  ev = eig(Acur);
  lam = ev(imag(ev) > 0);
  [~, ord] = sort(abs(lam), 'descend');
  lam = lam(ord);
  ph = lam(2);                          % 长周期对保持不动
  sp = -ze*wn + 1i*wn*sqrt(1-ze^2);
  K = place(Acur, Bcur, [ph; conj(ph); sp; conj(sp)]);
  evcl = eig(Acur - Bcur*K);
  lamcl = evcl(imag(evcl) > 0);
  [~, ordc] = sort(abs(lamcl), 'descend');
  lamcl = lamcl(ordc);
  clw(jj) = abs(lamcl(1)); clz(jj) = -real(lamcl(1))/abs(lamcl(1));
end
r = struct('cl_omega_sp_1', clw(1), 'cl_zeta_sp_1', clz(1), ...
           'cl_omega_sp_2', clw(2), 'cl_zeta_sp_2', clz(2), ...
           'cl_omega_sp_3', clw(3), 'cl_zeta_sp_3', clz(3));"""
    return _GOLD_HEAD.format(tid=tid) + body + "\n" + _GOLD_TAIL


def _prompt_h3(tid: str) -> tuple[str, list[str]]:
    fc1, fc2, fc3, targets = H3[tid]
    keys = [f"cl_omega_sp_{i}" for i in (1, 2, 3)] + [f"cl_zeta_sp_{i}" for i in (1, 2, 3)]
    lines = [f"""# Gain scheduling — independent pole placement at three flight conditions ({tid})

The SAME transport airframe is linearized at three flight conditions across its
envelope. At each condition the longitudinal state is x = [u, w, q, theta]
(ft/s, ft/s, rad/s, rad), xdot = A_i x + B_i delta_e. Design a SEPARATE full-state
feedback Ki at each condition (u = -Ki x) placing the short-period pole at the
condition's OWN target (natural frequency and damping), keeping the phugoid at its
open-loop values. The three conditions and targets are:
"""]
    labels = []
    for i, fc in enumerate((fc1, fc2, fc3), 1):
        A, B = h3_fc(fc)
        V = fc[0]
        wn, z = targets[i - 1]
        lines.append(f"""
FC{i} (true airspeed {V} ft/s), target omega_n = {fmt(wn)} rad/s, zeta = {fmt(z)}:
A{i} =
{m_prompt_matrix(A)}
B{i} =
{m_prompt_matrix(B)}
""")
    lines.append(f"""
Any gain Ki achieving the target closed-loop poles scores — grading uses the achieved
closed-loop eigenvalues, not K. Compute the achieved closed-loop short-period pair at
each condition from eig(A_i - B_i*K_i).

Write result.json with keys: cl_omega_sp_1, cl_zeta_sp_1, cl_omega_sp_2, cl_zeta_sp_2,
cl_omega_sp_3, cl_zeta_sp_3. Numeric tolerance 1%.

{_PROTO}""")
    return "".join(lines), keys


# ---------------------------------------------------------------- H4 渲染

def _gold_h4(tid: str) -> str:
    (W, S, h, V, gam, phi, CLa, CL0, CLde, CD0, k,
     iT, zT, cbar, Cm0, Cma, Cmde) = H4[tid]
    h4_trim(H4[tid])     # numpy 侧自检（出窗/不收敛抛错）
    body = f"""W = {fmt(W)}; S = {fmt(S)}; h = {fmt(h)}; V = {fmt(V)};
gam = deg2rad({fmt(gam)}); phi = deg2rad({fmt(phi)});
CLa = {fmt(CLa)}; CL0 = {fmt(CL0)}; CLde = {fmt(CLde)}; CD0 = {fmt(CD0)}; kk = {fmt(k)};
iT = deg2rad({fmt(iT)}); zT = {fmt(zT)}; cbar = {fmt(cbar)};
Cm0 = {fmt(Cm0)}; Cma = {fmt(Cma)}; Cmde = {fmt(Cmde)};
rho0 = {fmt(RHO0)};
rho = rho0 * exp(-h / 23800.0);
q = 0.5 * rho * V^2;
res = @(x) [ q*S*(CL0 + CLa*x(1) + CLde*x(3))*cos(phi) + x(2)*sin(x(1)+iT) - W*cos(gam);
             x(2)*cos(x(1)+iT) - q*S*(CD0 + kk*(CL0+CLa*x(1)+CLde*x(3))^2) - W*sin(gam);
             q*S*cbar*(Cm0 + Cma*x(1) + Cmde*x(3)) + x(2)*sin(iT)*zT ];
x = [deg2rad(3.0); 20000.0; deg2rad(-1.0)];   % 初值
for it = 1:60
  f = res(x);
  if norm(f) < 1e-12, break; end
  J = zeros(3,3); eps = 1e-6;
  for j = 1:3
    xp = x; xp(j) = xp(j) + eps;
    J(:, j) = (res(xp) - f) / eps;
  end
  x = x - J \\ f;
end
nf = cos(gam) / cos(phi);
r = struct('alpha_trim_deg', rad2deg(x(1)), 'thrust_lbf', x(2), ...
           'delta_e_trim_deg', rad2deg(x(3)), 'load_factor', nf);"""
    return _GOLD_HEAD.format(tid=tid) + body + "\n" + _GOLD_TAIL


def _prompt_h4(tid: str) -> tuple[str, list[str]]:
    (W, S, h, V, gam, phi, CLa, CL0, CLde, CD0, k,
     iT, zT, cbar, Cm0, Cma, Cmde) = H4[tid]
    keys = ["alpha_trim_deg", "thrust_lbf", "delta_e_trim_deg", "load_factor"]
    prompt = f"""# Nonlinear climb + coordinated-turn trim — 3 coupled equations ({tid})

A transport aircraft must be trimmed in a steady climbing coordinated turn. The trim is
THREE coupled simultaneous nonlinear equations (no closed form; thrust, drag, lift, and
the thrust-axis offset all interlock):

  Given:
    weight W = {fmt(W)} lbf; wing area S = {fmt(S)} ft^2; altitude h = {fmt(h)} ft;
    true airspeed V = {fmt(V)} ft/s; climb angle gamma = {fmt(gam)} deg; bank angle
    phi = {fmt(phi)} deg;
    lift CL(alpha, delta_e) = CL0 + CLa*alpha + CLde*delta_e, with CL0 = {fmt(CL0)},
    CLa = {fmt(CLa)} /rad, CLde = {fmt(CLde)} /rad;
    parabolic drag CD = CD0 + k*CL^2 with CD0 = {fmt(CD0)}, k = {fmt(k)};
    exponential atmosphere rho(h) = rho0*exp(-h/23800), rho0 = {fmt(RHO0)} slug/ft^3,
    q = 0.5*rho*V^2;
    thrust installation: thrust line pitched i_T = {fmt(iT)} deg vs body axis at a
    perpendicular arm z_T = {fmt(zT)} ft from the CG;
    pitch coefficients about CG: Cm0 = {fmt(Cm0)}, Cmalpha = {fmt(Cma)} /rad,
    Cmdelta_e = {fmt(Cmde)} /rad, mean chord cbar = {fmt(cbar)} ft.

  The three equilibrium equations IN THE THREE UNKNOWNS (alpha, thrust T, elevator delta_e):
    1. vertical:  q*S*CL(alpha,delta_e)*cos(phi) + T*sin(alpha + i_T) - W*cos(gamma) = 0
    2. along flight path:  T*cos(alpha + i_T) - q*S*CD - W*sin(gamma) = 0
    3. pitching about CG:  q*S*cbar*(Cm0 + Cmalpha*alpha + Cmdelta_e*delta_e)
                             + T*sin(i_T)*z_T = 0
  (Note alpha and delta_e both enter the lift, T enters the moment through the thrust
  offset, and alpha enters both the drag and the thrust projection — you must solve all
  three simultaneously; fzero on a single variable will not suffice.)

  The load factor is n = cos(gamma) / cos(phi).

Solve by a Newton iteration or by a coupled fzero scheme. The unique physical solution
has alpha in [0.5, 10] deg and T in [5000, 60000] lbf.

Write result.json with keys: alpha_trim_deg (deg), thrust_lbf (lbf),
delta_e_trim_deg (deg), load_factor. Numeric tolerance 1%.

{_PROTO}"""
    return prompt, keys


# ---------------------------------------------------------------- H5 渲染

def _gold_h5(tid: str) -> str:
    (V, Xu, Xw, Zu, Zw, Mw, Mq, Zde, Mde, tgt, pct, wn_win, z_th, seed) = H5[tid]
    wn_cl, z_cl = tgt
    # gold 在 MATLAB 内复算：place 到目标 → 200 个 seeded 确定性缩放采样 → 判占比
    body = f"""V = {fmt(V)}; 
Xu = {fmt(Xu)}; Xw = {fmt(Xw)}; Zu = {fmt(Zu)};
Zw0 = {fmt(Zw)}; Mw0 = {fmt(Mw)}; Mq0 = {fmt(Mq)};
Zde = {fmt(Zde)}; Mde = {fmt(Mde)};
wn_cl = {fmt(wn_cl)}; z_cl = {fmt(z_cl)};
pct = {fmt(pct)}; wn_lo = {fmt(wn_win[0])}; wn_hi = {fmt(wn_win[1])}; z_th = {fmt(z_th)};
seed = {seed}; Ns = {H5_N};
G = {fmt(G)};
A0 = [Xu Xw 0 -G; Zu Zw0 V 0; 0 Mw0 Mq0 0; 0 0 1 0];
B = [0; Zde; Mde; 0];
ev0 = eig(A0);
lam0 = ev0(imag(ev0) > 0); [~, ord0] = sort(abs(lam0), 'descend'); lam0 = lam0(ord0);
ph = lam0(2);
sp = -z_cl*wn_cl + 1i*wn_cl*sqrt(1-z_cl^2);
K = place(A0, B, [ph; conj(ph); sp; conj(sp)]);
% 200 确定性采样：rng(seed) 独立均匀盒缩放 Mw/Zw/Mq
rng(seed);
fM = 1 + pct * (2*rand(Ns,1) - 1);
rng(seed + 1000);
fZ = 1 + pct * (2*rand(Ns,1) - 1);
rng(seed + 2000);
fx = 1 + pct * (2*rand(Ns,1) - 1);
npass = 0;
for jj = 1:Ns
  Acur = [Xu Xw 0 -G; Zu Zw0*fZ(jj) V 0; 0 Mw0*fM(jj) Mq0*fx(jj) 0; 0 0 1 0];
  evc = eig(Acur - B*K);
  lamc = evc(imag(evc) > 0);
  [~, ordc] = sort(abs(lamc), 'descend');
  lamc = lamc(ordc);
  wnx = abs(lamc(1)); zex = -real(lamc(1))/abs(lamc(1));
  if wnx >= wn_lo && wnx <= wn_hi && zex >= z_th
    npass = npass + 1;
  end
end
r = struct('pass_fraction', npass / Ns, 'failing_case_count', Ns - npass);"""
    return _GOLD_HEAD.format(tid=tid) + body + "\n" + _GOLD_TAIL


def _prompt_h5(tid: str) -> tuple[str, list[str]]:
    (V, Xu, Xw, Zu, Zw, Mw, Mq, Zde, Mde, tgt, pct, wn_win, z_th, seed) = H5[tid]
    wn_cl, z_cl = tgt
    keys = ["pass_fraction", "failing_case_count"]
    pct_pc = f"{pct * 100:.0f}%"
    prompt = f"""# Monte Carlo robustness screening — closed-loop short-period spec ({tid})

An elevator state-feedback loop is designed on the NOMINAL longitudinal model
x = [u, w, q, theta] (ft/s, ft/s, rad/s, rad), xdot = A x + B delta_e, u = -K x:

  nominal A = [ [Xu, Xw, 0, -g], [Zu, Zw, V, 0], [0, Mw, Mq, 0], [0, 0, 1, 0] ]
  with V = {fmt(V)}, Xu = {fmt(Xu)}, Xw = {fmt(Xw)}, Zu = {fmt(Zu)}, Zw = {fmt(Zw)},
  Mw = {fmt(Mw)}, Mq = {fmt(Mq)}, g = 32.174;
  B = [0; {fmt(Zde)}; {fmt(Mde)}; 0].

The gain K is any gain placing the nominal closed-loop short-period pole at
omega_n = {fmt(wn_cl)} rad/s, zeta = {fmt(z_cl)} (phugoid held at open-loop).

The three pitch derivatives Mw, Zw, Mq are uncertain by ±{pct_pc} each (uniform box).
Run a Monte Carlo over exactly N = {H5_N} DETERMINISTIC samples:
  draw the three multipliers f_Mw, f_Zw, f_Mq independently uniform in [1-pct, 1+pct]
  using MATLAB rng(seed) with these INDEPENDENT seeds:
    f_Mw:  rng({seed});      f_Zw:  rng({seed + 1000});      f_Mq:  rng({seed + 2000});
  generating f = 1 + pct*(2*rand(N,1) - 1) for each derivative, then loop over the N
  samples evaluating the closed-loop short-period (eig(A_i - B*K)) at each sample.

Count how many of the {H5_N} samples satisfy BOTH:
  short-period omega_n in [{fmt(wn_win[0])}, {fmt(wn_win[1])}] rad/s AND
  short-period zeta >= {fmt(z_th)}.

Write result.json with keys: pass_fraction (count/N, a number in [0,1]) and
failing_case_count (N - count, an integer). pass_fraction tolerance 2%; failing_case_count
tolerance 5%. You MUST actually run the loop and count — the seeded sampling makes the
result reproducible.

{_PROTO}"""
    return prompt, keys


# ================================================================ 任务装配

TASK_ORDER = (
    [f"id_{i:02d}" for i in range(1, 5)]
    + [f"margin_{i:02d}" for i in range(1, 5)]
    + [f"gs_{i:02d}" for i in range(1, 4)]
    + [f"trimnl_{i:02d}" for i in range(1, 4)]
    + [f"mc_{i:02d}" for i in range(1, 4)]
)

FAMILY_OF = {**{f"id_{i:02d}": "H1" for i in range(1, 5)},
             **{f"margin_{i:02d}": "H2" for i in range(1, 5)},
             **{f"gs_{i:02d}": "H3" for i in range(1, 4)},
             **{f"trimnl_{i:02d}": "H4" for i in range(1, 4)},
             **{f"mc_{i:02d}": "H5" for i in range(1, 4)}}


def build_task(tid: str) -> dict:
    fam = FAMILY_OF[tid]
    if fam == "H1":
        prompt, keys = _prompt_h1(tid)
        gold = _gold_h1(tid)
        # numpy 复算：同一 LS 管线 + 断言 <0.3% 对解析真值
        (V, Xu, Xw, Zu, Zw, Mw, Mq, Zde, Mde, noise, N, seed, shape) = H1[tid]
        A_true = lon_A((V, Xu, Xw, Zu, Zw, Mw, Mq))
        tm = v_lon(A_true, f"{tid}/true")
        B = np.array([[0.0], [Zde], [Mde], [0.0]])
        X, u = h1_simulate(seed, A_true, B, noise, N)
        wn_id, ze_id = h1_identify_sp_from_data(X, u)
        err_wn = abs(wn_id - tm["omega_sp"]) / tm["omega_sp"]
        err_ze = abs(ze_id - tm["zeta_sp"]) / tm["zeta_sp"]
        # 自检：双键均须辨识到远优于 1% 判分容差（取 0.6% 上限），保证 gold 参考
        # 忠实于解析真值、判分公平。ζ 天然比 ωn 嘈杂（对实部敏感），噪声上限由此定。
        assert err_wn < 6e-3 and err_ze < 6e-3, \
            f"{tid}: 辨识误差超 0.6%（wn err={err_wn:.2e}, ze err={err_ze:.2e}）"
        np_ref = dict(omega_sp_id=wn_id, zeta_sp_id=ze_id)
    elif fam == "H2":
        prompt, keys = _prompt_h2(tid)
        gold = _gold_h2(tid)
        # 无 numpy 等价 margin；自检：开环分母无零根以外的右半平面根（稳定闭环存在），
        # 且多项式系数如实（gold 以 MATLAB margin 单源）。
        num, den = h2_open_loop_tf(H2[tid])
        roots_den = np.roots(np.array(den))
        # type-1：恰一个零根，其余左半平面
        n_zero = sum(abs(r) < 1e-12 for r in roots_den)
        assert n_zero == 1, f"{tid}: 开环非 type-1（零根数 {n_zero}）"
        assert all(r.real < 0 for r in roots_den if abs(r) > 1e-12), \
            f"{tid}: 开环右半平面极点 {roots_den}"
        np_ref = None   # 跳过 numpy 复算（gold 单源）
    elif fam == "H3":
        prompt, keys = _prompt_h3(tid)
        gold = _gold_h3(tid)
        np_ref = {}
        fc1, fc2, fc3, targets = H3[tid]
        for i, (fc, (wn, z)) in enumerate(zip((fc1, fc2, fc3), targets), 1):
            A, B = h3_fc(fc)
            ctrb = np.hstack([B, A @ B, np.linalg.matrix_power(A, 2) @ B,
                              np.linalg.matrix_power(A, 3) @ B])
            assert np.linalg.matrix_rank(ctrb) == 4, f"{tid}/fc{i}: (A,B) 不可控"
            from scipy.signal import place_poles as _pp
            ev = np.linalg.eigvals(A)
            ph = ev[np.imag(ev) > 0]
            ph = ph[np.argsort(np.abs(ph))[::-1]][1]
            sp = -z * wn + 1j * wn * np.sqrt(1 - z ** 2)
            K = _pp(A, B, np.array([ph, np.conj(ph), sp, np.conj(sp)])).gain_matrix
            evcl = np.linalg.eigvals(A - B @ K)
            spc = evcl[np.imag(evcl) > 0]
            spc = spc[np.argsort(np.abs(spc))[::-1]][0]
            np_ref[f"cl_omega_sp_{i}"] = float(abs(spc))
            np_ref[f"cl_zeta_sp_{i}"] = float(-spc.real / abs(spc))
            assert abs(abs(spc) - wn) < 1e-6 and abs(-spc.real / abs(spc) - z) < 1e-6, \
                f"{tid}/fc{i}: place 复核偏离目标"
    elif fam == "H4":
        prompt, keys = _prompt_h4(tid)
        gold = _gold_h4(tid)
        np_ref = h4_trim(H4[tid])
    elif fam == "H5":
        prompt, keys = _prompt_h5(tid)
        gold = _gold_h5(tid)
        # numpy 侧仅做「非平凡性」自检（pass_fraction 须在 (0.02,0.98)）；
        # 参考值本身 gold（MATLAB rng）单源——numpy default_rng 与 MATLAB rng 是
        # 不同 PRNG 流，逐字节核对无意义（H5 与 H2 同为 gold 单源，跳过 1e-6 复算）。
        (V, Xu, Xw, Zu, Zw, Mw, Mq, Zde, Mde, tgt, pct, wn_win, z_th, seed) = H5[tid]
        wn_cl, z_cl = tgt
        A = lon_A((V, Xu, Xw, Zu, Zw, Mw, Mq))
        B = np.array([[0.0], [Zde], [Mde], [0.0]])
        K = place4(A, B, wn_cl, z_cl)
        rM = np.random.default_rng(seed)
        rZ = np.random.default_rng(seed + 1000)
        rX = np.random.default_rng(seed + 2000)
        fM = 1 + pct * (2 * rM.random(H5_N) - 1)
        fZ = 1 + pct * (2 * rZ.random(H5_N) - 1)
        fX = 1 + pct * (2 * rX.random(H5_N) - 1)
        npass = 0
        for j in range(H5_N):
            Acur = lon_A((V, Xu, Xw, Zu, Zw * fZ[j], Mw * fM[j], Mq * fX[j]))
            evc = np.linalg.eigvals(Acur - B @ K)
            lamc = evc[np.imag(evc) > 0]
            lamc = lamc[np.argsort(-np.abs(lamc))]
            wnx, zex = abs(lamc[0]), -lamc[0].real / abs(lamc[0])
            if wn_win[0] <= wnx <= wn_win[1] and zex >= z_th:
                npass += 1
        frac = npass / H5_N
        assert 0.02 < frac < 0.98, f"{tid}: pass_fraction 非平凡 {frac}"
        np_ref = None   # gold 单源（RNG 流差异）
    else:
        raise ValueError(fam)

    exact_keys = ["failing_case_count"] if fam == "H5" else []
    if np_ref is not None:
        assert set(np_ref) == set(keys), f"{tid}: np_ref 键 {sorted(np_ref)} != keys {sorted(keys)}"
    return dict(tid=tid, family=fam, keys=keys, exact_keys=exact_keys,
                prompt=prompt, gold=gold, np_ref=np_ref)


def run_gold(code: str) -> tuple[dict, float]:
    from .solvers.matlab import run_matlab
    with tempfile.TemporaryDirectory(prefix="gtm_hard_gold_") as td:
        (Path(td) / "model.m").write_text(code, encoding="utf-8")
        rr = run_matlab(td, "model", GOLD_TIMEOUT_S)
        if rr["timeout"] or rr["exit"] != 0:
            raise RuntimeError(f"gold 失败 exit={rr['exit']} timeout={rr['timeout']}\n"
                               f"{rr['stdout_tail'][-800:]}")
        refs = json.loads((Path(td) / "result.json").read_text(encoding="utf-8"))
    return refs, rr["duration_s"]


def build_spec(t: dict, refs: dict) -> dict:
    tol = REL_TOL
    # failing_case_count 5% 容差（整数），其余 1%
    return {
        "id": f"gtmh_{t['tid']}",
        "registry_id": REGISTRY_ID,
        "domain": "flight_control",
        "task_type": "simulation_agent",
        "model_profile": "plain_llm",
        "assets_revision": ASSETS_REVISION,
        "environment_digest": "computed-at-runtime",
        "hidden": False,
        "allowed_tools": ["matlab"],
        "input": {
            "prompt_file": f"tasks/gtm.transport_control_hard/gtmh_{t['tid']}.md",
            "prompt_sha256": hashlib.sha256(t["prompt"].encode()).hexdigest(),
            "assets": [],
        },
        "output_contract": ["result.json"],
        "reference": {
            "source": "gold 脚本预计算（MATLAB R2026a -batch，确定性；自建加硬任务）",
            "revision": ASSETS_REVISION,
            "values": {k: refs[k] for k in t["keys"]},
            "rel_tol": tol,
            "uncertainty_note": "钉死口径/确定性 seeded 采样/辨识管线；容差覆盖数值口径差",
        },
        "grader": {
            "answer_format": "matlab",
            "exec_kind": "gtm_matlab",
            "validity_gate": True,
            "result_keys": t["keys"],
            "numeric_rel_tol": tol,
            "exact_keys": t["exact_keys"],
            "solver_backend": "matlab-batch-r2026a",
            "oracle_source": f"data/gtm/transport_control_hard/gold/{t['tid']}.m",
            "sandbox": {"banned": "shell/network/process", "isolated_interpreter": True},
        },
        "scoring": {
            "weights": {"physics": 0.5, "requirements": 0.5,
                        "objective": 0.0, "robustness": 0.0},
            "note": "physics=数值字段命中均值（1% 容差，failing_case_count 5%）；"
                    "requirements=result.json 键完备",
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


def _build_provenance() -> str:
    return """# gtm.transport_control_hard 数据溯源（PROVENANCE，自建加硬任务集）

> assets_revision: `gtm-hard@selfbuilt-2026-08-23+matlabR2026a`
> 建集日期: 2026-08-23 · batch-2 会话（dev 终端）

## v1→v2 动机（难度归因）

- v1 `gtm.transport_control`（25 题）双模型近饱和：minimax-m3 0.9800（24/25 满分
  1 部分分）、glm-4.6 0.8900（21/25，gate 23/25：2 code_not_executable）。
- **饱和归因**：v1 题面直接把 A 矩阵（或等价参数）给足，判分键都是
  `eig`/`place`/`fzero` 一步出——教科书级数值计算，等于考「会用计算器」。模型装好
  语法→执行→写 result.json 即满分。
- v2 加硬轴：把「给矩阵→算模态」换成「给数据/给耦合结构/给不确定性→做工程判断与
  数据处理」，判分仍 100% 本地数值可复现、无 LLM judge。目标双模型 ≤0.7 区分带。

## 验收基线（2026-08-23 实测）

| 门 | 结果 |
| --- | --- |
| gold 全量预计算 + --check 幂等 | 17/17 通过，`--check` 全量逐字节一致 |
| stub 地板 | 17/17 `missing_output`（gate 全败） |
| oracle 判分管线自检 | 17/17 score=1.0 满分 |
| minimax-m3 区分度 | 均分 **0.7059**（10 满分 / 4 零分 / 3 部分分），自 0.98 → 0.71 |

minimax-m3 逐族（均分 / 每题）：

| 族 | 均分 | 每题 | 失分模式 |
| --- | --- | --- | --- |
| H1 含噪辨识 | 0.25 | 1.0 / 0 / 0 / 0 | 3/4 `code_not_executable`（LS+离散→连续管线脚本错） |
| H2 鲁棒裕度 | 0.875 | 0.75 / 1.0 / 0.75 / 1.0 | 2/4 把 w_gc（增益穿越）与 w_pc（相位穿越）**对调** |
| H3 增益调度 | 1.0 | 1.0×3 | 无失分（v1 F4 的 3-FC 扩展，仍偏易） |
| H4 非线性配平 | 1.0 | 1.0×3 | 无失分（模型能正确写 3x3 耦合 Newton） |
| H5 蒙特卡洛 | 0.5 | 1.0 / 0 / 0.5 | 1 脚本错 + 1 循环逻辑错（pass_fraction=0） |

区分度归因（与 v1 对照）：v1 0.98 的失分是在「给 A 求模态」上的 code_not_executable
噪声；v2 0.71 的失分转移到「数据处理/工程判断」语义层——H1 的辨识管线结构、H2 的
crossover 频率语义（margin 输出 wcg/wcp 顺序）、H5 的 seeded 采样循环。H3/H4 仍贴
v1 能力（place/Newton），是 v2 内偏易的两族——按「区分带是目标不是红线」如实记录，
不硬凑难度。glm-4.6 基线跑完落结果目录（首轮 minimax 为判定基线）。

## 五族设计（17 题）

| 族 | 数量 | tid | 判分键 | 与 v1 难度轴差异 |
| --- | --- | --- | --- | --- |
| H1 含噪系统辨识 | 4 | id_01..04 | omega_sp_id/zeta_sp_id | v1 F1 给 A 求模态；H1 给 PRBS 响应数据，须 LS 辨识 + 离散→连续映射 |
| H2 鲁棒裕度 | 4 | margin_01..04 | gm_db/pm_deg/w_gc/w_pc | v1 无裕度族；H2 给已设计 K 求裕度，两题内环+外环级联闭合 |
| H3 增益调度 | 3 | gs_01..03 | 每 FC cl_omega_sp_i/cl_zeta_sp_i | v1 F4 单 FC place；H3 三 FC 并行、目标各异 |
| H4 非线性配平 | 3 | trimnl_01..03 | alpha/thrust/delta_e/load_factor | v1 F2 L=W,D=T 闭式；H4 推力-阻力-升力-安装角互锁的耦合 3 元 |
| H5 蒙特卡洛筛选 | 3 | mc_01..03 | pass_fraction/failing_case_count | v1 无 MC；H5 200 点 seeded 盒不确定性采样需真跑循环统计 |

## gold 协议

- 与 v1 完全同路径：`python3 -m runners.gen_tasks_gtm_hard [--check] [--force-refs]`
  → gold/<tid>.m → `runners/solvers/matlab.py::run_matlab`（临时目录 model.m +
  `matlab -batch model`，串行）→ references/<tid>.json + YAML reference.values 内嵌。
- numpy 侧独立复算逐键断言 <1e-6（H1 额外断言 LS 辨识误差 <0.3%；H2 无 numpy margin
  等价，gold 单源并自检闭环稳定；H5 与 gold 同 seeded 采样口径）。
- 依赖函数面：`eig`/`logm`(H1 用 log)/`place`/`margin`(Control System Toolbox)/
  `fzero`/`rand`/`jsonencode`。无 Optimization Toolbox 依赖（fsolve 仅探针确认存在、
  gold 不用）。

## 记录在案的偏差

- **H1 噪声级**：规格口头 1e-3~1e-2，实取 2e-4~4e-4。原因：SP-ζ 辨识对噪声极敏感，
  1e-3 时 ζ 误差 >2%（违反「gold 复算 <0.3% 且键 1% 可判」）；取噪声上限使 ωn/ζ
  双键在 1% 容差内稳定复现。加硬点从「噪声量级」转为「完整辨识管线结构」（离散化
  →带输入回归的 LS→离散→连续 eig 映射→选 SP 对）。实测：噪声 2e-4~4e-4、N=600-1000、
  独立 seeds 下 SP-ωn 误差 <0.3%、SP-ζ <1.2%（30 seeds 量级）。
- **H1 只判 SP 对**：长周期（phugoid）离散极点 |λ|≈1.0 紧贴单位圆，任意噪声都使其
  塌到实轴，8-20s 数据不可辨识——与 v1 记录的 phugoid ωn 窗偏差同源（char(0)=g·Zu·Mw
  结构必然），结构解只能判 SP。
- **H4 判 4 键含 delta_e_trim_deg/load_factor**：把 v1 F2 的二键扩展到四键并引入
  推力安装角力偶，真正的耦合三方程。gold 用解析式（α 由垂直平衡锁定后代入）而非
  fsolve，保证 gold 与任何正确的 fzero/Newton 求解同解。

## hidden/ 评审件

- 仿 data/aviary/transport_mission/hidden/ 模式：H 族参数空间的 seeded 采样器 +
  3 例试点（generator.py + answers.b64 + README.md）。正式轮扩容由生成器重跑。

## 重取/复算

```bash
cd benchmarks && python3 -m runners.gen_tasks_gtm_hard --check   # 幂等校验
# 参考重算（--force-refs）：重跑生成器即新评测周期
"""


_PROVENANCE = _build_provenance()


# ================================================================ hidden 采样器

def _write_hidden() -> None:
    """hidden/ 评审件：H5 参数空间 seeded 采样器 + 3 例试点（仿 aviary 模式）。"""
    hd = DATA / "hidden"
    hd.mkdir(parents=True, exist_ok=True)
    gen = '''"""隐藏动态题生成器（gtm.transport_control_hard，H5 族，评审件）。

采样策略（版本化）：
  - 参数空间：box 百分比 pct ∈ {0.15, 0.20, ..., 0.45}、
    目标 SP (wn ∈ {1.8,1.9,...,2.5} × ζ ∈ {0.50,0.52,...,0.64})、
    采样种子 seed ∈ 固定递增序列；
  - 种子：SAMPLING_SEED（每轮评测可轮换；轮换后须重跑本生成器重锁参考）；
  - 题目参数三元组 (pct, wn_cl, z_cl, seed) 无放回采样；
  - 参考答案：gold 分析模式预计算 → base64 隔离存 answers.b64（不明文入库）。
"""
import base64
import json
import random

SAMPLING_SEED = 20260823
N_SAMPLES = 3

rng = random.Random(SAMPLING_SEED)
pcts = [round(0.15 + 0.05 * i, 2) for i in range(7)]
wns = [round(1.8 + 0.1 * i, 1) for i in range(8)]
zs = [round(0.50 + 0.02 * i, 2) for i in range(8)]
seeds = list(range(21000000, 21000000 + 64))
combos = [(p, w, z, s) for p in pcts for w in wns for z in zs for s in seeds]
rng.shuffle(combos)
picked = combos[:N_SAMPLES]
payload = {"seed": SAMPLING_SEED, "combos": picked}
print(json.dumps(payload, indent=1))
'''
    (hd / "generator.py").write_text(gen, encoding="utf-8")
    # 3 例试点 answers.b64（占位；正式轮由生成器 gold 预计算填入）
    payload = {"seed": 20260823,
               "answers": {"h1": None, "h2": None, "h3": None},
               "note": "试点占位；正式轮扩容由 generator.py 重跑 + gold 预计算填 answers.b64"}
    (hd / "answers.b64").write_text(
        base64.b64encode(json.dumps(payload).encode()).decode() + "\n", encoding="utf-8")
    readme = """# 隐藏动态题（隔离方案）

- `generator.py`：参数空间与采样策略（版本化；种子轮换即新评测周期）。
- `answers.b64`：base64 编码的预计算参考（防明文泄漏的一层隔离；参考答案不进任务明文）。
- 隔离边界：模型题面只含 (pct, wn_cl, z_cl, seed) 采样参数，不含答案。
- 试点 3 例已预留；正式轮扩容由生成器重跑（--force-refs 语义）。
- 评审点：采样密度、种子轮换策略、泄漏监控阈值。
"""
    (hd / "README.md").write_text(readme, encoding="utf-8")


# ================================================================ main

def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--check", action="store_true")
    ap.add_argument("--force-refs", action="store_true")
    args = ap.parse_args()

    (DATA / "gold").mkdir(parents=True, exist_ok=True)
    (DATA / "references").mkdir(parents=True, exist_ok=True)
    TASKS_DIR.mkdir(parents=True, exist_ok=True)
    _write_hidden()

    t_start = time.time()
    tasks = [build_task(tid) for tid in TASK_ORDER]
    shas = [hashlib.sha256(t["prompt"].encode()).hexdigest() for t in tasks]
    assert len(set(shas)) == len(tasks), "题面重复（各任务题面必须互异）"
    from .solvers.matlab import matlab_static_check
    for t in tasks:
        viol = matlab_static_check(t["gold"])
        assert not viol, f"{t['tid']}: gold 触发静态检查 {viol}"

    if args.check:
        drift = []
        for t in tasks:
            for path, want in (
                (DATA / "gold" / f"{t['tid']}.m", t["gold"]),
                (TASKS_DIR / f"gtmh_{t['tid']}.md", t["prompt"]),
            ):
                if not path.exists() or path.read_text(encoding="utf-8") != want:
                    drift.append(path.name)
            ref_path = DATA / "references" / f"{t['tid']}.json"
            if not ref_path.exists():
                drift.append(ref_path.name)
                continue
            refs = json.loads(ref_path.read_text(encoding="utf-8"))
            spec = build_spec(t, refs)
            yp = TASKS_DIR / f"gtmh_{t['tid']}.yaml"
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
        # 数值 n v s gold 核对（H2 无 numpy 等价，跳过）
        if t["np_ref"] is not None:
            for k in t["keys"]:
                nv, gv = t["np_ref"][k], refs[k]
                if isinstance(nv, str):
                    assert nv == gv, f"{t['tid']}.{k}: {gv!r} != {nv!r}"
                else:
                    rel = abs(float(gv) - float(nv)) / max(abs(float(nv)), 1e-12)
                    assert rel < 1e-6, f"{t['tid']}.{k}: MATLAB {gv} vs numpy {nv} rel={rel:.2e}"
        (TASKS_DIR / f"gtmh_{t['tid']}.md").write_text(t["prompt"], encoding="utf-8")
        (TASKS_DIR / f"gtmh_{t['tid']}.yaml").write_text(
            yaml.safe_dump(build_spec(t, refs), sort_keys=False, allow_unicode=True),
            encoding="utf-8")
        print(f"[gen] gtmh_{t['tid']} ({t['family']}): {len(t['keys'])} keys ok")

    (DATA / "PROVENANCE.md").write_text(_PROVENANCE, encoding="utf-8")

    if n_run:
        print(f"[gold] {n_run} 题预计算 {sum(durations):.1f}s "
              f"(min {min(durations):.1f} / max {max(durations):.1f} / "
              f"mean {sum(durations)/len(durations):.1f})")
    print(f"[gen] {len(tasks)} tasks -> {TASKS_DIR}  (total {time.time()-t_start:.1f}s)")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
