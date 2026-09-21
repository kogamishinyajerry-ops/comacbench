"""tmr_cf.py — NASA TMR flat plate 判分侧：残差收敛门 + 壁面 Cf 误差带统计。

定位（不强加新架构，只补齐 nasa_tmr.verification 缺失的 grader 侧读数件）：

  adapters/README.md §3 simulation_agent 的判分管线要求
    1. validity gate 含「求解收敛（按任务声明的收敛定义：残差阈值 + 监控量平稳）」
    2. physics 为「目标量对参考的误差带评分」
  本模块提供两者的**可复现读数实现**，仍遵「grader 只认产物 + 判据 + 场结果」：
  不启动求解器、不判总分（总分在 adapter 层）。

两类产物
--------
1. STAR-CCM+ 批处理 stdout 的残差表 → residual_history() / convergence_report()
2. 壁面导出 .daten（ShellId, Centroid[X], tau_x, tau_y, tau_z）+ TMR 参考 .dat
   → read_daten() / read_reference() / compare_cf()

关键陷阱（2026-09-21 实测，务必先跑收敛门再谈 Cf）
--------------------------------------------------
* 细网格（273x193 起）在 STAR-CCM+ 默认 1000 步内 **k 方程未收敛**，Tke 残差在窗内
  可能出现系统性回升（273 档实测 0.577@501 → 0.826@1000）；此时壁面 Cf 会呈现
  「准层流」假象（273 档 Cf ≈ 1.2× Blasius 层流值）。任何 TMR Cf 结论必须先过
  convergence_report().ok。
* 迭代上限必须走 `StepStoppingCriterion.setMaximumNumberSteps(int)`；
  `ClientServerObject.set("MaximumSteps", n)` 是**静默 no-op**（会让人误以为跑了 N 步，
  实际仍是默认 1000）。
* **湍流残差的绝对量级不可直接跨算例比较**：残差按 k 场量级归一化，入口湍流强度
  Ti 改 10× 会让 k_inlet 改 100×，Tke 残差随之整体缩放 100×（实测：同一 273 网格，
  Ti=0.1% 时 Tke@1000 = 82.2，Ti=1% 时 = 0.826，轨迹形状完全相同）。
  **只比较同一 k 量级下的残差轨迹**，跨算例比较必须看 Cf/场量而非残差数值。
* 残差门通过 ≠ 解正确：545x385 档残差平滑下降（Tke 单调 0.54→0.49）却出现壁面 τ 崩塌
  （Cf ~1e-5），必须叠加场侧 sanity（见 convergence_report 文档的 caveat）。
"""

from __future__ import annotations

import math
from dataclasses import dataclass, field
from pathlib import Path
from typing import Iterable, Sequence

# --------------------------------------------------------------------------- 残差


@dataclass(frozen=True)
class ResidualRow:
    """一行残差表（列名来自 STAR-CCM+ 表头，不硬编码语言/列序）。"""

    iteration: int
    values: dict[str, float]

    def get(self, key: str) -> float | None:
        return self.values.get(key)


def _norm_key(name: str) -> str:
    return name.strip().lower().replace("-", "_")


def residual_history(text: str) -> list[ResidualRow]:
    """解析 STAR-CCM+ stdout 里的残差表；表头驱动列映射（容忍列序/语言差异）。

    表头形如::

        Iteration  Continuity  X-momentum  Y-momentum  Z-momentum  Energy  Tke  Sdr

    数据行形如::

                     985   1.437500e-06   1.711704e-03 ...

    返回按迭代序的行列表；无表头或无数据行时返回空列表。
    """
    rows: list[ResidualRow] = []
    columns: list[str] | None = None
    for raw in text.splitlines():
        line = raw.strip()
        if not line:
            continue
        head = line.split()
        if columns is None and "iteration" in head[0].lower() and len(head) > 1:
            columns = [_norm_key(c) for c in head[1:]]
            continue
        if columns is None:
            continue
        if not head[0].lstrip("+-").isdigit():
            continue
        if len(head) != len(columns) + 1:
            continue
        try:
            iteration = int(head[0])
            values = {name: float(tok) for name, tok in zip(columns, head[1:])}
        except ValueError:
            continue
        rows.append(ResidualRow(iteration=iteration, values=values))
    return rows


@dataclass
class ConvergenceVerdict:
    """残差收敛门结论（validity gate 的「求解收敛」项）。"""

    ok: bool
    n_iter: int
    final: ResidualRow | None
    continuity_ok: bool
    momentum_ok: bool
    turbulence_stationary: bool
    reasons: list[str] = field(default_factory=list)
    drift: dict[str, float] = field(default_factory=dict)

    def summary(self) -> str:
        state = "PASS" if self.ok else "FAIL"
        head = f"convergence {state} @ iter {self.n_iter}"
        if not self.reasons:
            return head
        return head + " | " + "; ".join(self.reasons)


def convergence_report(
    text: str,
    *,
    continuity_tol: float = 1.0e-4,
    momentum_tol: float = 1.0e-2,
    window: int = 300,
    growth_tol: float = 0.05,
) -> ConvergenceVerdict:
    """残差收敛判据：阈值 + 最近窗内湍流量「平稳」（不允许系统性回升）。

    与 adapters/README.md §3 的措辞对齐：**残差阈值**（continuity / momentum）
    + **监控量平稳**（湍流残差在最近 window 步内不得超出窗首值 growth_tol 以上）。

    Args:
        continuity_tol: 连续性方程残差上限。
        momentum_tol: 各动量分量残差上限（稳态外流常见 1e-3~1e-5，这里留宽）。
        window: 判定「平稳」的回看步数。
        growth_tol: 窗内允许的相对回升（默认 5%）。

    Note:
        caveat：**本门通过不等于解正确。** 545x385 档残差平滑下降却被观测到壁面 τ
        崩塌，说明还需场侧 sanity（壁面 Cf 量级、k 非零、μt/μ > 1）。调用方负责叠加。
    """
    rows = residual_history(text)
    reasons: list[str] = []
    if not rows:
        return ConvergenceVerdict(
            ok=False, n_iter=0, final=None, continuity_ok=False, momentum_ok=False,
            turbulence_stationary=False, reasons=["no residual table found"])

    final = rows[-1]
    cont = final.get("continuity")
    continuity_ok = cont is not None and cont <= continuity_tol
    if not continuity_ok:
        reasons.append(f"continuity {cont!r} > {continuity_tol:g}")

    mom = [v for k, v in final.values.items() if "momentum" in k]
    momentum_ok = bool(mom) and all(v <= momentum_tol for v in mom)
    if not momentum_ok:
        reasons.append(f"momentum max {max(mom) if mom else float('nan'):.4g} > {momentum_tol:g}")

    # 湍流列：k-omega 族的 tke / sdr（列名容忍）
    turb_keys = [k for k in final.values if k in ("tke", "sdr", "k", "omega")]
    tail = rows[-window:] if len(rows) >= window else rows
    drift: dict[str, float] = {}
    stationary = True
    for key in turb_keys:
        series = [r.get(key) for r in tail]
        series = [v for v in series if v is not None]
        if len(series) < 2:
            continue
        first, peak, last = series[0], max(series), series[-1]
        drift[key] = (last - first) / first * 100.0 if first else math.nan
        if peak > first * (1.0 + growth_tol):
            stationary = False
            reasons.append(
                f"{key} non-stationary in last {len(series)} iters "
                f"(peak {peak:.4g} vs window-start {first:.4g}, "
                f"{(peak / first - 1) * 100.0:+.1f}%)")

    ok = continuity_ok and momentum_ok and stationary
    return ConvergenceVerdict(
        ok=ok, n_iter=final.iteration, final=final,
        continuity_ok=continuity_ok, momentum_ok=momentum_ok,
        turbulence_stationary=stationary, reasons=reasons, drift=drift)


# --------------------------------------------------------------------------- Cf


def read_daten(path: str | Path) -> tuple[list[float], list[float]]:
    """读 STAR-CCM+ 表面导出 .daten → (x, tau_x)，按 x 升序。

    文件首行为 ``# Shell Id, Centroid[X], Wall Shear Stress X, ...``，数据行 5 列。
    """
    xs: list[float] = []
    taus: list[float] = []
    for raw in Path(path).read_text(encoding="utf-8", errors="replace").splitlines():
        line = raw.strip()
        if not line or line.startswith("#"):
            continue
        parts = line.split()
        if len(parts) < 3:
            continue
        try:
            xs.append(float(parts[1]))
            taus.append(float(parts[2]))
        except ValueError:
            continue
    if not xs:
        raise ValueError(f"no data rows parsed from {path}")
    order = sorted(range(len(xs)), key=lambda i: xs[i])
    return [xs[i] for i in order], [taus[i] for i in order]


def read_reference(path: str | Path) -> tuple[list[float], list[float]]:
    """读 TMR 参考 .dat（Tecplot 风格 ``variables="x","cf"``）→ (x, cf)，按 x 升序。"""
    xs: list[float] = []
    cfs: list[float] = []
    for raw in Path(path).read_text(encoding="utf-8", errors="replace").splitlines():
        line = raw.strip()
        low = line.lower()
        if not line or "variables" in low or low.startswith("zone"):
            continue
        parts = line.split()
        if len(parts) < 2:
            continue
        try:
            xs.append(float(parts[0].replace("D", "E").replace("d", "e")))
            cfs.append(float(parts[1].replace("D", "E").replace("d", "e")))
        except ValueError:
            continue
    if not xs:
        raise ValueError(f"no data rows parsed from {path}")
    order = sorted(range(len(xs)), key=lambda i: xs[i])
    return [xs[i] for i in order], [cfs[i] for i in order]


def cf_from_tau(tau: Sequence[float], *, rho: float = 1.18415,
                u_inf: float = 50.0) -> list[float]:
    """Cf = tau_w / (0.5 ρ U∞²)。默认值为 TMR flat plate（M=0.2, U∞=50 m/s）下的空气量。"""
    q = 0.5 * rho * u_inf * u_inf
    return [t / q for t in tau]


@dataclass(frozen=True)
class BinStat:
    lo: float
    hi: float
    n: int
    model: float
    reference: float

    @property
    def dev_pct(self) -> float:
        if not self.reference:
            return math.nan
        return (self.model - self.reference) / self.reference * 100.0


@dataclass
class CfComparison:
    """Cf 比对结果：分 bin 统计 + 插值逐点相对偏差 + 误差带得分。"""

    bins: list[BinStat]
    mean_dev_pct: float
    median_dev_pct: float
    n_points: int
    n_model: int
    cf_model_range: tuple[float, float]
    label: str = ""

    @property
    def max_abs_dev_pct(self) -> float:
        vals = [abs(b.dev_pct) for b in self.bins if not math.isnan(b.dev_pct)]
        return max(vals) if vals else math.nan

    def summary(self) -> str:
        return (f"{self.label}: mean {self.mean_dev_pct:+.2f}% | "
                f"median {self.median_dev_pct:+.2f}% | "
                f"bin max|dev| {self.max_abs_dev_pct:.1f}% | n={self.n_model}")


def _interp(x: Sequence[float], y: Sequence[float], q: float) -> float:
    """线性插值（x 升序）；q 越界时钳到端点（与 numpy.interp 同语义）。"""
    if q <= x[0]:
        return y[0]
    if q >= x[-1]:
        return y[-1]
    lo, hi = 0, len(x) - 1
    while hi - lo > 1:
        mid = (lo + hi) // 2
        if x[mid] <= q:
            lo = mid
        else:
            hi = mid
    span = x[hi] - x[lo]
    return y[lo] if span == 0 else y[lo] + (y[hi] - y[lo]) * (q - x[lo]) / span


def compare_cf(
    x_model: Sequence[float],
    cf_model: Sequence[float],
    x_ref: Sequence[float],
    cf_ref: Sequence[float],
    *,
    x_min: float = 0.0,
    x_max: float = 2.0,
    n_bins: int = 8,
    ref_floor: float = 1.0e-6,
    label: str = "",
) -> CfComparison:
    """把模型 Cf 与参考 Cf 比对（平板段 x∈[x_min, x_max]）。

    - 分 bin：两侧各自取 bin 内均值（不插值），给出 dev%
    - 逐点：把参考插值到模型点上，给出 mean/median dev%（参考值低于 ref_floor 的点剔除，
      用于跳过参考里 x<0 的对称段零值）
    """
    pairs = [(x, c) for x, c in zip(x_model, cf_model) if x_min <= x <= x_max]
    if not pairs:
        raise ValueError("no model points inside [x_min, x_max]")
    mx = [p[0] for p in pairs]
    mc = [p[1] for p in pairs]

    bins: list[BinStat] = []
    width = (x_max - x_min) / n_bins
    for i in range(n_bins):
        a, b = x_min + i * width, x_min + (i + 1) * width
        sel_m = [c for x, c in zip(mx, mc) if a <= x < b or (i == n_bins - 1 and x == b)]
        sel_r = [c for x, c in zip(x_ref, cf_ref) if a <= x < b]
        bins.append(BinStat(
            lo=a, hi=b, n=len(sel_m),
            model=sum(sel_m) / len(sel_m) if sel_m else math.nan,
            reference=sum(sel_r) / len(sel_r) if sel_r else math.nan,
        ))

    devs: list[float] = []
    for x, c in zip(mx, mc):
        r = _interp(x_ref, cf_ref, x)
        if r > ref_floor:
            devs.append((c - r) / r * 100.0)
    devs_sorted = sorted(devs)
    mean_dev = sum(devs) / len(devs) if devs else math.nan
    if devs_sorted:
        mid = len(devs_sorted) // 2
        median_dev = (devs_sorted[mid] if len(devs_sorted) % 2
                      else (devs_sorted[mid - 1] + devs_sorted[mid]) / 2)
    else:
        median_dev = math.nan

    return CfComparison(
        bins=bins, mean_dev_pct=mean_dev, median_dev_pct=median_dev,
        n_points=len(devs), n_model=len(mx),
        cf_model_range=(min(mc), max(mc)), label=label)


def dev_band_score(dev_pct: float, band: Iterable[tuple[float, float]]) -> float:
    """误差带评分：band = [(|dev| 上限, 得分), ...]，按 |dev| 升序；超出末档记 0。

    对齐 adapters/README.md §3「目标量对参考的误差带评分」的最小实现
    （参考 foam_nmse 的阈值阶梯风格：阈值区间 -> 分数，不做 LLM judge）。
    """
    a = abs(dev_pct)
    for limit, score in band:
        if a <= limit:
            return score
    return 0.0


def fully_turbulent_mean_cf(
    x: Sequence[float], cf: Sequence[float], *, x_lo: float = 0.5, x_hi: float = 2.0
) -> float:
    """完全湍流段 Cf 均值——TMR flat plate 的 GCI 收敛量推荐取这一区段。

    取 x>0.5 的理由：x<0.5 落在 TMR 公开数据的转捩/前缘奇异区，模型与参考都会
    出现非网格收敛的大偏差（实测：137 档该区 -36%，而 x>0.5 仅 -8%），
    把前缘区混入 GCI 会污染观察阶次。
    """
    sel = [c for xx, c in zip(x, cf) if x_lo <= xx <= x_hi]
    if not sel:
        raise ValueError(f"no points in [{x_lo}, {x_hi}]")
    return sum(sel) / len(sel)


# ------------------------------------------------------------------- GCI / 外推


@dataclass
class GciResult:
    """Roache GCI（三档网格，观察阶次由三档解自洽反推）。"""

    values: tuple[float, float, float]        # (fine, medium, coarse)
    ratios: tuple[float, float]               # (r21, r32)
    observed_order: float | None
    extrapolated: float | None
    fine_relative_error: float | None          # |f1 - f_exact| / |f_exact|
    gci_fine: float | None
    gci_medium: float | None
    oscillatory: bool = False
    reason: str = ""

    @property
    def ok(self) -> bool:
        return self.observed_order is not None and self.extrapolated is not None

    def summary(self) -> str:
        if not self.ok:
            return f"GCI n/a ({self.reason})"
        return (f"p={self.observed_order:.2f} | extrapolated={self.extrapolated:.6g} | "
                f"GCI_fine={self.gci_fine * 100:.2f}% | "
                f"GCI_medium={self.gci_medium * 100:.2f}%")


def richardson_gci(
    values: Sequence[float],
    ratios: Sequence[float] = (2.0, 2.0),
    *,
    safety: float = 1.25,
) -> GciResult:
    """三档网格 Richardson 外推 + GCI（Roache 1994/1998）。

    Args:
        values: **(fine, medium, coarse)** 顺序的同一 QoI（如全板 Cf 均值）。
        ratios: (r21, r32) 相邻档细化比；TMR flat plate 三档按 n→2n-1 加密，
            故 r ≈ 2.0（137→273→545）。
        safety: 安全因子 Fs；三档可用时取 1.25。

    Note:
        - 观察阶次 `p = ln(ε32/ε21) / ln(r)`，要求 ε21、ε32 同号；
          异号 = 振荡收敛，此时 p 无定义，本函数记 oscillatory=True 且不报 GCI。
        - **前置条件：三档解必须都过了 convergence_report().ok**；
          未收敛的解做 GCI 只得到伪收敛（2026-09-21 的教训）。
    """
    if len(values) != 3:
        raise ValueError("需要恰好三档解 (fine, medium, coarse)")
    f1, f2, f3 = (float(v) for v in values)
    r21, r32 = (float(r) for r in ratios)
    eps21, eps32 = f2 - f1, f3 - f2
    if eps21 == 0.0:
        return GciResult((f1, f2, f3), (r21, r32), None, f1, 0.0, 0.0, 0.0,
                         reason="相邻档解完全相同，无法反推阶次")
    if eps32 / eps21 <= 0.0:
        return GciResult((f1, f2, f3), (r21, r32), None, None, None, None, None,
                         oscillatory=True, reason="ε32/ε21 <= 0：振荡收敛")
    p = math.log(eps32 / eps21) / math.log(r21)
    if abs(p) < 1e-12:
        return GciResult((f1, f2, f3), (r21, r32), p, None, None, None, None,
                         reason="观察阶次 ~0，外推不稳定")
    f_exact = f1 + (f1 - f2) / (r21 ** p - 1.0)
    fine_err = abs((f1 - f_exact) / f_exact) if f_exact else math.nan
    gci_fine = safety * abs((f1 - f2) / f1) / abs(r21 ** p - 1.0)
    gci_medium = safety * abs((f2 - f3) / f2) / abs(r32 ** p - 1.0)
    return GciResult((f1, f2, f3), (r21, r32), p, f_exact, fine_err,
                     gci_fine, gci_medium)


# --------------------------------------------------------------------------- CLI


def _main(argv: list[str] | None = None) -> int:  # pragma: no cover - CLI
    import argparse

    ap = argparse.ArgumentParser(
        prog="python -m runners.tmr_cf",
        description="NASA TMR flat plate 判分侧读数：残差收敛门 / Cf 误差带 / GCI 外推")
    sub = ap.add_subparsers(dest="cmd", required=True)

    p_res = sub.add_parser("residual", help="对 STAR-CCM+ 批处理日志跑收敛门")
    p_res.add_argument("logs", nargs="+", type=Path)

    p_cf = sub.add_parser("cf", help="导出场 .daten 与 TMR 参考 Cf 比对")
    p_cf.add_argument("daten", type=Path)
    p_cf.add_argument("reference", type=Path)
    p_cf.add_argument("--bins", type=int, default=8)
    p_cf.add_argument("--rho", type=float, default=1.18415)
    p_cf.add_argument("--u", type=float, default=50.0)
    p_cf.add_argument("--x-min", type=float, default=0.0)
    p_cf.add_argument("--x-max", type=float, default=2.0)
    p_cf.add_argument("--label", default="")

    p_gci = sub.add_parser("gci", help="三档网格 Richardson 外推 + GCI（量取 x>0.5 Cf 均值）")
    p_gci.add_argument("daten", nargs=3, type=Path, metavar=("FINE", "MEDIUM", "COARSE"))
    p_gci.add_argument("--ratios", default="2,2", help="相邻档细化比 r21,r32")
    p_gci.add_argument("--safety", type=float, default=1.25)
    p_gci.add_argument("--x-lo", type=float, default=0.5)
    p_gci.add_argument("--rho", type=float, default=1.18415)
    p_gci.add_argument("--u", type=float, default=50.0)
    p_gci.add_argument("--reference", type=Path, default=None,
                       help="可选：同时打印各档对参考的偏差")

    args = ap.parse_args(argv)

    if args.cmd == "residual":
        rc = 0
        for log in args.logs:
            v = convergence_report(log.read_text(encoding="utf-8", errors="replace"))
            print(f"{log.name}: {v.summary()}")
            for k, d in sorted(v.drift.items()):
                print(f"    drift[{k}] = {d:+.2f}% over window")
            rc |= 0 if v.ok else 1
        return rc

    if args.cmd == "cf":
        xs, taus = read_daten(args.daten)
        xr, cfr = read_reference(args.reference)
        cf = cf_from_tau(taus, rho=args.rho, u_inf=args.u)
        res = compare_cf(xs, cf, xr, cfr, x_min=args.x_min, x_max=args.x_max,
                         n_bins=args.bins, label=args.label or args.daten.stem)
        print(res.summary())
        print(f"{'bin':>18} {'n':>4} {'model':>11} {'reference':>11} {'dev%':>8}")
        for b in res.bins:
            print(f"  [{b.lo:5.2f},{b.hi:5.2f})  {b.n:>4} {b.model:>11.6f} "
                  f"{b.reference:>11.6f} {b.dev_pct:>8.1f}")
        print(f"fully-turbulent mean Cf (x>={args.x_min + 0.5:.2f}): "
              f"{fully_turbulent_mean_cf(xs, cf):.6f}")
        return 0

    fine, medium, coarse = args.daten
    qois: list[float] = []
    for p in (fine, medium, coarse):
        xs, taus = read_daten(p)
        cf = cf_from_tau(taus, rho=args.rho, u_inf=args.u)
        qois.append(fully_turbulent_mean_cf(xs, cf, x_lo=args.x_lo))
        print(f"{p.name}: mean Cf(x>={args.x_lo}) = {qois[-1]:.6f}")
    ratios = tuple(float(t) for t in args.ratios.split(","))
    g = richardson_gci(qois, ratios, safety=args.safety)
    print(f"Richardson/GCI: {g.summary()}")
    if args.reference is not None:
        xr, cfr = read_reference(args.reference)
        ref = fully_turbulent_mean_cf(xr, cfr, x_lo=args.x_lo)
        print(f"reference mean Cf(x>={args.x_lo}) = {ref:.6f}")
        for p, q in zip(args.daten, qois):
            print(f"  {p.name}: dev vs reference = {(q - ref) / ref * 100.0:+.2f}%")
    return 0 if g.ok else 1


if __name__ == "__main__":  # pragma: no cover - CLI
    raise SystemExit(_main())
