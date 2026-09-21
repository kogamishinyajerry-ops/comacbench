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
* **参考文件不是单条曲线**：TMR 的 `cf_plate_sstv.dat` 含两个 zone
  （`zone, t="CFL3D"` 与 `zone, t="FUN3D"`，990 行里 447 个 x 站点各出现两次且 cf 不同）。
  按行拼接会得到一条**混合参考**，插值指标被污染（实测口径差 0.2–0.3 pp）。
  `read_reference` 因此 fail-closed：多 zone 且未显式指定 `zone=` 直接抛错。
  补测（2026-09-21）：两 zone 在 x>=0.25 处一致到 0.01–0.03%，仅前缘差 ~1%，
  所以「必须选 zone」是**口径卫生要求**，不是数值上的主误差源。
* **残差门通过 ≠ 湍流残差已停止漂移**：同是 6000 步，137x97 的 Tke 窗漂移 -0.02%
  （已趴平），273x193 的 -10.46%（仍在缓慢下降）。两者 ``ok`` 都是 True，因为本门
  只抓「回升」。要用 `strict_ok`（叠加 `drift_ok`）或直接看 `qoi_stationary()`。
* **参考 Cf 不是单调曲线**：CFL3D/FUN3D zone 在 x≈0.005–0.01 处有前缘峰
  （Cf≈0.0054–0.0056，约为平台值的 2 倍），随后按 x^-0.14 衰减；壁面 x 网格从
  x=0.001 起。把前缘段混入 GCI 会污染观察阶次，故 `fully_turbulent_mean_cf`
  默认取 x>=0.5。另注：两个 zone 里 x<=0 的 96 个点是**上游对称面**（cf=0），
  按行取均值会把它当成「壁面低 Cf」。
* **必须先确认算例真的跑在它自称的 Re 上**：`field_sanity()` 从二维切片反推
  `nu = k/(omega*TVR)`。2026-09-21 实测：写的是「U=50 / nu=1e-5 -> Re=5e6」，
  但反推得 ν = 1.56659e-5（= STAR-CCM+ 默认空气 μ/ρ，52224 样本离散度 0.01%），
  于是实际 **Re_unit = 3.19e6，比目标低 36%**。修法是 U = 5e6·ν = 78.33 m/s
  （此时 TMR 的 k=1.125U²/Re_L、ω=125U/L 恰好等价于 Ti=3.873e-4、TVR=0.009）。
  这类口径错误**不会**由残差门或 Cf 门发现，只有场侧反推能抓。
* **Re 对了也不代表板上有边界层**：`diagnose_slice()` 检查「边界层是不是从零起步」。
  2026-09-21 阶段五实测（273x193，12000 步）：前缘第一个站位 δ99 = 19.57 mm，
  而湍流理论值 `0.37·x·Re_x^-0.2` 只有 0.0674 mm —— **290 倍**（137 档 19.00 mm，
  几乎同值，故与网格分辨率无关）。三个独立自洽检查同时否定它：θ(0.5)=3.96 mm
  而应由参考 Cf 积分得到 ~0.9 mm（4.4 倍）；动量积分 `Cf/2 = dθ/dx` 实测给
  0.0010~0.0016 而壁面给 0.0025~0.0026（差约 2 倍）；但 `H = 1.29~1.86` 反而
  「正常」—— 即**剖面形状像边界层、厚度整体荒谬**。
  来源是**上游「伪层」**：上游对称条带（x<0，本该是均匀来流）近壁 u 掉到
  8~20 m/s（16~40 % 来流）、k ≈ 100 m²/s²（Ti ≈ 16 %），一进板面就直接成为板的
  「边界层」。它不是 BC 失效（全场 max|w| = 1.44 m/s = 2.9 % U，条带上 ∂u/∂z ≈ 0，
  法向与切向梯度条件都满足），而是自洽的伪层。
  后果：**入口湍流口径被它完全淹没**（入口 k 差 667 倍，上游读数只动 2 %、
  板的边界层只动 ~1 %）—— 这就是「改入口湍流改不动 Cf 形状」的真因。
  ⇒ 任何后续 run 都必须先过 `diagnose_slice().ok`，再谈 Cf / GCI。
"""

from __future__ import annotations

import math
import re
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
    """残差收敛门结论（validity gate 的「求解收敛」项）。

    两个层级别混淆（2026-09-21 实测教训）：

    * ``ok``        —— 阈值门 + **无系统性回升**。单调下降一律算通过（这是本门的
      设计本意：它抓的是「发散 / 极限环」，不是「还没跑够」）。
    * ``strict_ok`` —— ``ok`` **且**湍流残差已停止漂移（``drift_ok``）。GCI / 外推
      的前置条件应当用这一个，否则会把「仍在缓慢下降」的解当成收敛解来做外推，
      得到伪收敛阶次。

    实测对照（同为 6000 步）：137x97 的 Tke 窗漂移 -0.02%（已趴平）→ ``strict_ok``
    为真；273x193 的 Tke 窗漂移 -10.46%（还差很多）→ ``ok`` 仍为真但 ``strict_ok``
    为假。只看 ``ok`` 无法区分这两者。
    """

    ok: bool
    n_iter: int
    final: ResidualRow | None
    continuity_ok: bool
    momentum_ok: bool
    turbulence_stationary: bool
    reasons: list[str] = field(default_factory=list)
    drift: dict[str, float] = field(default_factory=dict)
    drift_ok: bool = True
    decay_tol: float | None = None

    @property
    def strict_ok(self) -> bool:
        """``ok`` 且湍流残差已停止漂移——GCI / Richardson 外推的推荐前置判据。"""
        return self.ok and self.drift_ok

    def summary(self) -> str:
        state = "PASS" if self.ok else "FAIL"
        head = f"convergence {state} @ iter {self.n_iter}"
        if self.ok and not self.drift_ok:
            head += " (still-drift: strict gate would reject)"
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
    decay_tol: float | None = 0.10,
) -> ConvergenceVerdict:
    """残差收敛判据：阈值 + 最近窗内湍流量「不回升」+（可选）「已停止漂移」。

    与 adapters/README.md §3 的措辞对齐：**残差阈值**（continuity / momentum）
    + **监控量平稳**（湍流残差在最近 window 步内）。「平稳」被拆成两个可独立
    观测的子条件，因为二者的处置完全不同：

    * 回升（rebound）→ ``growth_tol`` 判定，**进 ``ok``**。含义：发散 / 极限环，
      解是坏的。
    * 持续下滑（still-drift）→ ``decay_tol`` 判定，**不进 ``ok``，进 ``drift_ok``**。
      含义：还没跑够，解是好的但没到位。单调下降是健康行为，因此默认不否决 ``ok``
      （既有契约：``test_decaying_residuals_pass``），但 GCI 这类外推必须叠加
      ``strict_ok``。

    Args:
        continuity_tol: 连续性方程残差上限。
        momentum_tol: 各动量分量残差上限（稳态外流常见 1e-3~1e-5，这里留宽）。
        window: 判定「平稳」的回看步数。
        growth_tol: 窗内允许的相对回升（默认 5%）。
        decay_tol: 窗内允许的相对净漂移（两侧都用 ``|drift|``）；``None`` 关闭该项
            （此时 ``drift_ok`` 恒为 True）。

    Note:
        caveat：**本门通过不等于解正确。** 545x385 档残差平滑下降却被观测到壁面 τ
        崩塌，说明还需场侧 sanity（壁面 Cf 量级、k 非零、μt/μ > 1）。调用方负责叠加。
    """
    rows = residual_history(text)
    reasons: list[str] = []
    if not rows:
        return ConvergenceVerdict(
            ok=False, n_iter=0, final=None, continuity_ok=False, momentum_ok=False,
            turbulence_stationary=False, reasons=["no residual table found"],
            drift_ok=False, decay_tol=decay_tol)

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
    drift_ok = True
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
        if decay_tol is not None and abs(drift[key]) > decay_tol * 100.0:
            drift_ok = False
            reasons.append(
                f"{key} still drifting in last {len(series)} iters "
                f"({drift[key]:+.2f}% net, |drift| > {decay_tol * 100.0:.0f}%)")

    ok = continuity_ok and momentum_ok and stationary
    return ConvergenceVerdict(
        ok=ok, n_iter=final.iteration, final=final,
        continuity_ok=continuity_ok, momentum_ok=momentum_ok,
        turbulence_stationary=stationary, reasons=reasons, drift=drift,
        drift_ok=drift_ok, decay_tol=decay_tol)


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


def reference_zones(path: str | Path) -> list[str]:
    """列出 TMR 参考 .dat 里的所有 zone 名（按出现序）；无 zone 行时返回 ``['']``。

    TMR 的 Cf 参考文件常把多个求解器的结果装在同一个文件里，例如
    ``cf_plate_sstv.dat`` 同时含 ``zone, t="CFL3D"`` 与 ``zone, t="FUN3D"``。
    **按行拼接会得到一条混合曲线**——务必先列 zone 再显式选取（见 read_reference）。
    """
    names: list[str] = []
    for raw in Path(path).read_text(encoding="utf-8", errors="replace").splitlines():
        line = raw.strip()
        if not line.lower().startswith("zone"):
            continue
        m = re.search(r't\s*=\s*"([^"]*)"', line)
        if m:
            names.append(m.group(1))
        else:
            m2 = re.search(r't\s*=\s*(\S+)', line)
            names.append(m2.group(1) if m2 else f"zone{len(names)}")
    return names or [""]


def read_reference(
    path: str | Path, *, zone: int | str | None = None
) -> tuple[list[float], list[float]]:
    """读 TMR 参考 .dat（Tecplot 风格 ``variables="x","cf"``）→ (x, cf)，按 x 升序。

    Args:
        zone: 选择 zone（``int`` 索引或 ``str`` 名）。
            ``None`` 时**仅当文件只有一个 zone** 才取它；多 zone 时抛
            ``ValueError``（fail-closed：宁可报错，也不静默拼接成混合参考）。
    """
    text = Path(path).read_text(encoding="utf-8", errors="replace")
    names = reference_zones(path)

    blocks: list[list[tuple[float, float]]] = [[]]
    for raw in text.splitlines():
        line = raw.strip()
        low = line.lower()
        if not line or "variables" in low:
            continue
        if low.startswith("zone"):
            blocks.append([])
            continue
        parts = line.split()
        if len(parts) < 2:
            continue
        try:
            blocks[-1].append((
                float(parts[0].replace("D", "E").replace("d", "e")),
                float(parts[1].replace("D", "E").replace("d", "e")),
            ))
        except ValueError:
            continue
    # 首个 block 是 zone 行之前的散点（某些文件没有 zone 行）
    if blocks[0]:
        data_blocks = blocks
    else:
        data_blocks = blocks[1:]

    if not data_blocks or all(not b for b in data_blocks):
        raise ValueError(f"no data rows parsed from {path}")

    if zone is None:
        nonempty = [b for b in data_blocks if b]
        if len(nonempty) > 1:
            raise ValueError(
                f"{Path(path).name} 含 {len(nonempty)} 个 zone {names}；"
                "必须用 zone= 显式指定，避免拼接成混合参考")
        rows = nonempty[0]
    else:
        if isinstance(zone, int):
            if not (0 <= zone < len(data_blocks)) or not data_blocks[zone]:
                raise ValueError(f"zone 索引 {zone} 越界或为空（共 {len(data_blocks)} 个）")
            rows = data_blocks[zone]
        else:
            if zone not in names:
                raise ValueError(f"zone 名 {zone!r} 不存在；可选 {names}")
            rows = data_blocks[names.index(zone)]

    xs = [r[0] for r in rows]
    cfs = [r[1] for r in rows]
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


# --------------------------------------------------------------- QoI 平稳性判据


@dataclass
class QoiVerdict:
    """QoI（壁面 Cf）平稳性结论——细网格上比湍流残差更可信的收敛判据。"""

    ok: bool
    n: int
    first: float
    last: float
    drift_pct: float
    last_step_pcts: list[float] = field(default_factory=list)
    reason: str = ""

    def summary(self) -> str:
        state = "PASS" if self.ok else "FAIL"
        head = (f"QoI stationary {state} | n={self.n} | "
                f"{self.first:.6f} -> {self.last:.6f} (net {self.drift_pct:+.3f}%)")
        if self.reason:
            head += " | " + self.reason
        return head


def qoi_stationary(
    values: Sequence[float], *, tol_pct: float = 1.0, window: int = 3
) -> QoiVerdict:
    """判定 QoI 序列是否已平稳：最后 ``window`` 个相邻相对增量都落在 ``tol_pct`` 内。

    为什么需要这个（2026-09-21 实测）：STAR-CCM+ 的湍流残差按 k 场量级归一化，
    **绝对量级跨算例不可比**（入口 Ti 差 10x → Tke 残差整体差 100x，轨迹形状完全
    相同）。因此「湍流残差数值小」既不是收敛的充分条件也不是必要条件。真正的
    收敛判据应当落在 **目标量本身** 上：把壁面 τ 按迭代分块导出，看 Cf 是否停止
    移动。

    实测对照（273x193，默认 IC）：Cf(x>=0.5) 在 3000 步时 1.69e-3（seed 版）/
    2.4e-3 量级，6000 步明显更高，说明本算例的 τ 是靠**对流把湍流从入口搬进来**
    慢慢建立的，迭代次数是主导变量。

    Args:
        values: 按迭代递增的同一 QoI 序列（如各检查点的 Cf(x>=0.5) 均值）。
        tol_pct: 相邻检查点之间允许的相对变化上限（%）。
        window: 需要连续平稳的检查点增量个数。

    Note:
        - 有效增量不足 ``window`` 个时 fail-closed（``ok=False``）：样本不足以判定。
          分母为 0 的增量（QoI 全零，即 τ 崩塌）**不计为 0% 的平稳**，同样 fail-closed。
        - 只做**增量**判定，不做总体漂移判定：一个线性缓慢上升的序列可能在
          单点对单点上都很小却始终不收敛，此时应增大检查点间隔或看 ``drift_pct``。
    """
    vals = [float(v) for v in values]
    if not vals:
        return QoiVerdict(False, 0, math.nan, math.nan, math.nan, [], reason="空序列")
    drift = (vals[-1] - vals[0]) / vals[0] * 100.0 if vals[0] else math.nan
    steps: list[float] = []
    for a, b in zip(vals, vals[1:]):
        if a == 0.0:
            continue    # 相对增量无定义（分母为 0）；不静默当成 0% 的「平稳」
        steps.append((b - a) / a * 100.0)
    if len(steps) < window:
        return QoiVerdict(
            False, len(vals), vals[0], vals[-1], drift, steps,
            reason=(f"有效增量只有 {len(steps)} 个（需连续 {window} 个）；"
                    f"序列含 0 值时相对增量无定义"))
    tail = steps[-window:]
    worst = max(abs(s) for s in tail)
    if worst > tol_pct:
        return QoiVerdict(False, len(vals), vals[0], vals[-1], drift, steps,
                          reason=(f"最后 {window} 个增量最大 |Δ| = {worst:.3f}% "
                                  f"> {tol_pct:g}%；最近值 {vals[-1]:.6f}"))
    return QoiVerdict(True, len(vals), vals[0], vals[-1], drift, steps)


# --------------------------------------------------------------------- 场侧 sanity


@dataclass(frozen=True)
class FieldRow:
    """二维切片（.daten）的一行：Y=0 平面上的一个面。"""

    x: float
    z: float          # 壁法向（板在 z=0）
    omega: float
    k: float
    tvr: float        # mu_t / mu
    u: float
    w: float = math.nan


def read_field_slice(path: str | Path) -> list[FieldRow]:
    """读 STAR-CCM+ 导出到 .daten 的二维切片（带表头列名）。

    与 ``read_daten``（壁面 tau 导出）不同：这里靠表头**按名字**定位列，
    因为场导出的列集合随宏而变。必须至少含 Centroid[X] / Centroid[Z] /
    Specific Dissipation Rate / Turbulent Kinetic Energy / Turbulent Viscosity Ratio
    / Velocity[i]。
    """
    path = Path(path)
    with path.open("rb") as fh:
        magic = fh.read(2)
    if magic == b"\x1f\x8b":
        raise ValueError(
            f"{path.name} 是 gzip 压缩件；先 `gunzip -k {path.name}` 再读"
            "（本函数只读纯文本 .daten）")
    text = path.read_text(encoding="utf-8", errors="replace")
    header: list[str] | None = None
    rows: list[FieldRow] = []
    for line in text.splitlines():
        s = line.strip()
        if not s:
            continue
        if s.startswith("#"):
            if header is None:
                header = [t.strip() for t in s.lstrip("#").split(",")]
            continue
        if header is None:
            continue
        vals = s.split()
        if len(vals) < len(header):
            continue
        col = {name: i for i, name in enumerate(header)}

        def g(*names: str, default: float = math.nan) -> float:
            for n in names:
                if n in col:
                    try:
                        return float(vals[col[n]])
                    except ValueError:
                        return default
            return default

        rows.append(FieldRow(
            x=g("Centroid[X]"), z=g("Centroid[Z]"),
            omega=g("Specific Dissipation Rate"),
            k=g("Turbulent Kinetic Energy"),
            tvr=g("Turbulent Viscosity Ratio"),
            u=g("Velocity[i]"), w=g("Velocity[k]"),
        ))
    return rows


@dataclass
class FieldSanity:
    """场侧 sanity 结论 —— 守恒门（残差）与 QoI 门（Cf）之外的第三道读数。

    它回答两个**不依赖参考数据**的问题：

    1. 这份场自洽吗？（SST 的 μt = ρk/ω 蕴含 ``nu = k/(omega*TVR)`` 必须是常数。
       若反推出的 ν 离散度大，说明场/导出有问题，任何 Cf 比较都不必谈。）
    2. **算例真的跑在它自称的雷诺数上吗？** 用反推的 ν 算出 ``Re_unit = U/nu``，
       与目标 Re 比对。2026-09-21 实测：跑了几十轮的「Re=5e6」算例其实是
       ``U=50, nu=1.5666e-5 -> Re_unit=3.19e6``，低了 36%（详见报告 §11）。
    """

    n_faces: int
    nu_median: float
    nu_spread_pct: float
    k_max: float
    tvr_max: float
    tvr_far: float
    tvr_near_max: float
    re_unit: float
    re_target: float
    re_gap_pct: float
    reasons: list[str] = field(default_factory=list)

    @property
    def nu_consistent(self) -> bool:
        return not any(r.startswith("nu") for r in self.reasons)

    @property
    def ok(self) -> bool:
        return not self.reasons

    @property
    def tvr_contrast(self) -> float:
        """近壁/前段涡粘性相对远场的对比度（>1 表示近壁被涡粘性占据）。"""
        return self.tvr_near_max / self.tvr_far if self.tvr_far else math.nan

    def summary(self) -> str:
        state = "PASS" if self.ok else "FAIL"
        head = (f"field sanity {state} | n={self.n_faces} | "
                f"nu={self.nu_median:.6e} (spread {self.nu_spread_pct:.3f}%) | "
                f"Re_unit={self.re_unit:.4g} vs target {self.re_target:.4g} "
                f"({self.re_gap_pct:+.1f}%)")
        if self.reasons:
            head += " | " + "; ".join(self.reasons)
        return head


def field_sanity(
    rows: Sequence[FieldRow], *,
    u_inf: float = 50.0,
    re_target: float = 5.0e6,
    nu_tol_pct: float = 2.0,
    re_tol_pct: float = 2.0,
) -> FieldSanity:
    """从二维切片算场侧 sanity（ν 反推 + Re 一致性 + 近壁污染指标）。

    Args:
        rows: ``read_field_slice`` 的结果。
        u_inf: 来流速度（用于 Re_unit = u_inf/nu）。
        re_target: TMR 口径要求的目标 Re_unit（按单位长度）。传 0 或 None 跳过检查。
        nu_tol_pct: ``nu = k/(omega*TVR)`` 的允许离散度（用 p05–p95 相对中位数）。
        re_tol_pct: Re_unit 与目标的允许偏差。

    Note:
        - 只对 ``k>0`` 且 ``omega>0`` 且 ``tvr>0`` 的面做 ν 反推（贴壁/SST 的
          ω 壁面值会到 1e9 量级，此时 tvr→0，比值仍成立但数值噪声大）。
        - ``tvr_far`` 取 z 最大的 20 % 那一档的中位数（自由来流）；
          ``tvr_near_max`` 取 z 最小的 2 % 那一档的最大值（近壁/前段）。
    """
    reasons: list[str] = []
    if not rows:
        return FieldSanity(0, math.nan, math.nan, math.nan, math.nan,
                           math.nan, math.nan, math.nan, re_target, math.nan,
                           ["空切片"])

    nu = [r.k / (r.omega * r.tvr)
          for r in rows if r.k > 0.0 and r.omega > 0.0 and r.tvr > 0.0]
    nu_sorted = sorted(nu)

    def pct(seq: Sequence[float], q: float) -> float:
        if not seq:
            return math.nan
        i = min(len(seq) - 1, max(0, int(round(q * (len(seq) - 1)))))
        return seq[i]

    nu_med = pct(nu_sorted, 0.5)
    spread = ((pct(nu_sorted, 0.95) - pct(nu_sorted, 0.05)) / nu_med * 100.0
              if nu_med else math.nan)
    if not nu:
        reasons.append("nu: 无可用样本（k/omega/tvr 需全为正）")
    elif spread > nu_tol_pct:
        reasons.append(f"nu 离散度 {spread:.2f}% > {nu_tol_pct:g}%"
                       f"（场不自洽或导出口径不一致）")

    z_max = max(r.z for r in rows)
    far = sorted(r.tvr for r in rows if r.z >= 0.8 * z_max)
    near = [r.tvr for r in rows if r.z <= 0.02 * z_max]
    tvr_far = pct(sorted(far), 0.5) if far else math.nan
    tvr_near_max = max(near) if near else math.nan

    re_unit = u_inf / nu_med if nu_med else math.nan
    if re_target and not math.isnan(re_unit):
        re_gap = (re_unit - re_target) / re_target * 100.0
        if abs(re_gap) > re_tol_pct:
            reasons.append(
                f"Re_unit {re_unit:.4g} 偏离目标 {re_target:.4g} {re_gap:+.1f}%"
                f"（nu={nu_med:.6e}, U={u_inf:g} -> 需要 U={re_target * nu_med:.3f}）")
    else:
        re_gap = math.nan

    return FieldSanity(
        n_faces=len(rows), nu_median=nu_med, nu_spread_pct=spread,
        k_max=max(r.k for r in rows), tvr_max=max(r.tvr for r in rows),
        tvr_far=tvr_far, tvr_near_max=tvr_near_max,
        re_unit=re_unit, re_target=re_target, re_gap_pct=re_gap,
        reasons=reasons)


@dataclass
class SliceDiagnosis:
    """二维切片诊断：**板面上的边界层是不是从零起步的**（2026-09-21 阶段五新增）。

    动机：``field_sanity`` 只回答「这份场跑在它自称的 Re 上吗」，抓不出另一类错误——
    Re 正确、Cf 量级也「正常」，但板面上承载的根本不是一条从 x=0 起步的边界层。

    实测（273x193，12000 步，U=50，Re_unit=3.19e6）：

    * 前缘第一个站位 x=0.001 处 ``d99 = 19.57 mm``，湍流理论值 ``0.37*x*Re_x^-0.2``
      只有 ``0.074 mm`` —— **相差 260 倍**；
    * 上游对称条带（x<0，本该是均匀来流）近壁 ``u`` 掉到 ``8.2 m/s``（16 % U），
      ``k ~ 100 m^2/s^2``（Ti ~ 16 %）；
    * 该「伪层」进入板面后直接成为板的边界层，使 ``Cf(x)`` 被压成近常数
      （斜率 -0.03 对参考 -0.14），GCI 无从收口。

    判据（任一触发即 ``ok = False``）：

    1. ``lead_ratio = d99(前缘首站) / 0.37*x*Re_x^-0.2 > lead_tol``（默认 5）
    2. ``up_u_ratio_min < up_tol``（默认 0.9）—— 上游条带本该是均匀来流

    与 ``field_sanity`` 一样 fail-closed：数据不足以判定时报 ``ok=False``。
    """

    n_faces: int
    n_stations: int
    n_upstream: int
    up_u_ratio_min: float
    up_k_max: float
    lead_x: float
    lead_delta99_mm: float
    lead_theory_mm: float
    lead_ratio: float
    stations: list[tuple[float, float, float, float, float]] = field(default_factory=list)
    reasons: list[str] = field(default_factory=list)

    @property
    def ok(self) -> bool:
        return not self.reasons

    def summary(self) -> str:
        head = ("slice PASS" if self.ok
                else "slice FAIL") + f" | {self.n_stations} 站位 / {self.n_faces} 面"
        bits = []
        if self.n_upstream:
            bits.append(f"上游 u/U_min={self.up_u_ratio_min:.3f}, k_max={self.up_k_max:.4g}")
        if not math.isnan(self.lead_ratio):
            bits.append(f"前缘 x={self.lead_x:g}: d99={self.lead_delta99_mm:.3f} mm"
                        f" / 理论 {self.lead_theory_mm:.4f} mm = {self.lead_ratio:.1f}x")
        if self.reasons:
            bits.append("; ".join(self.reasons))
        return head + (" | " + " | ".join(bits) if bits else "")


def _bl_station(col: Sequence[FieldRow], u_inf: float) -> tuple[float, float, float]:
    """单站位的 (d99, delta*, theta)，全部用梯形积分（只积到 d99）。"""
    d99 = next((r.z for r in col if r.u >= 0.99 * u_inf), math.nan)
    z_top = d99 if not math.isnan(d99) else col[-1].z
    ds = th = 0.0
    for a, b in zip(col, col[1:]):
        if b.z > z_top:
            break
        h = b.z - a.z
        ds += 0.5 * ((1 - a.u / u_inf) + (1 - b.u / u_inf)) * h
        th += 0.5 * (((a.u / u_inf) * (1 - a.u / u_inf))
                     + ((b.u / u_inf) * (1 - b.u / u_inf))) * h
    return d99, ds, th


def diagnose_slice(
    rows: Sequence[FieldRow], *,
    u_inf: float = 50.0,
    re_target: float = 5.0e6,
    lead_tol: float = 5.0,
    up_tol: float = 0.9,
) -> SliceDiagnosis:
    """从二维切片算「边界层起步厚度 + 上游伪层 + 边界层积分量」。

    Args:
        rows: ``read_field_slice`` 的结果。
        u_inf: 来流速度（δ99 与积分量都以它为基准）。
        re_target: 用于理论 δ 的参考 Re（按单位长度）；0/None 时跳过前缘判据。
        lead_tol: 前缘 δ99 允许是理论湍流值的几倍。
        up_tol: 上游条带近壁 u/u_inf 的下限。

    Note:
        - 前缘站位取「x>0 且 x>=1e-4 的第一个站位」：x→0 时理论 δ→0，比值会发散，
          1e-4 是避免除零的保护阈值（TMR 参考表本身也从 x=0.001 起）。
        - 上游指标取 x<0 各站位近壁（z 最小那行）的**最小值/最大值**：伪层是
          「上游靠近对称面的那一段整体被滞止」，取极值是它的正确度量。
    """
    reasons: list[str] = []
    if not rows:
        return SliceDiagnosis(0, 0, 0, math.nan, math.nan, math.nan,
                              math.nan, math.nan, math.nan, [], ["空切片"])

    by_x: dict[float, list[FieldRow]] = {}
    for r in rows:
        by_x.setdefault(round(r.x, 10), []).append(r)
    stations_sorted = sorted(by_x)
    cols = {xv: sorted(by_x[xv], key=lambda r: r.z) for xv in stations_sorted}
    data = {xv: _bl_station(cols[xv], u_inf) for xv in stations_sorted}

    up = [xv for xv in stations_sorted if xv < -1e-6]
    if up:
        up_u_ratio_min = min(cols[xv][0].u / u_inf for xv in up)
        up_k_max = max(cols[xv][0].k for xv in up)
    else:
        up_u_ratio_min = up_k_max = math.nan

    lead = next((xv for xv in stations_sorted if xv > 0.0 and xv >= 1e-4), None)
    if lead is None:
        lead_x = lead_d99 = lead_th = lead_ratio = math.nan
    else:
        lead_x = lead
        lead_d99 = data[lead][0]
        if re_target:
            re_x = re_target * lead
            lead_th = 0.37 * lead * re_x ** (-0.2)
            lead_ratio = (lead_d99 / lead_th) if lead_th else math.nan
        else:
            lead_th = lead_ratio = math.nan

    if not up:
        reasons.append("切片不含 x<0 站位，无法判定上游条带")
    elif up_u_ratio_min < up_tol:
        reasons.append(
            f"上游条带近壁 u/U 最低 {up_u_ratio_min:.3f} < {up_tol:g}"
            f"（应为均匀来流；k_max={up_k_max:.4g}）—— 存在上游伪层")
    if lead is None:
        reasons.append("切片不含 x>0 站位，无法判定前缘")
    elif re_target and not math.isnan(lead_ratio) and lead_ratio > lead_tol:
        reasons.append(
            f"前缘 d99 {lead_d99 * 1e3:.3f} mm = 理论 {lead_th * 1e3:.4f} mm 的 "
            f"{lead_ratio:.0f}x > {lead_tol:g}x（边界层不是从零起步）")

    return SliceDiagnosis(
        n_faces=len(rows), n_stations=len(stations_sorted), n_upstream=len(up),
        up_u_ratio_min=up_u_ratio_min, up_k_max=up_k_max,
        lead_x=lead_x, lead_delta99_mm=lead_d99 * 1e3, lead_theory_mm=lead_th * 1e3,
        lead_ratio=lead_ratio,
        stations=[(xv, data[xv][0] * 1e3, data[xv][1] * 1e3, data[xv][2] * 1e3,
                   (data[xv][1] / data[xv][2]) if data[xv][2] else math.nan)
                  for xv in stations_sorted],
        reasons=reasons)


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
        - **前置条件：三档解必须都过了 `ConvergenceVerdict.strict_ok`**（不是 `ok`——
          `ok` 允许「仍在单调下降」的解通过）；未收敛的解做 GCI 只得到伪收敛
          （2026-09-21 的教训）。若残差判据不可靠，退而用 `qoi_stationary()` 对 QoI
          序列本身做平稳性判定。
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
    p_res.add_argument("--strict", action="store_true",
                       help="用 strict_ok（ok 且湍流残差已停止漂移）决定退出码")

    p_cf = sub.add_parser("cf", help="导出场 .daten 与 TMR 参考 Cf 比对")
    p_cf.add_argument("daten", type=Path)
    p_cf.add_argument("reference", type=Path)
    p_cf.add_argument("--bins", type=int, default=8)
    p_cf.add_argument("--rho", type=float, default=1.18415)
    p_cf.add_argument("--u", type=float, default=50.0)
    p_cf.add_argument("--x-min", type=float, default=0.0)
    p_cf.add_argument("--x-max", type=float, default=2.0)
    p_cf.add_argument("--label", default="")
    p_cf.add_argument("--zone", default=None,
                      help="参考文件含多 zone 时必填（如 CFL3D / FUN3D）")

    p_qoi = sub.add_parser(
        "qoi",
        help="QoI 平稳性判据：按迭代顺序给一组导出场，看 x>=x_lo 的 Cf 均值是否停住")
    p_qoi.add_argument("daten", nargs="+", type=Path,
                       metavar="DATEN", help="按迭代递增顺序排列的各检查点导出件")
    p_qoi.add_argument("--x-lo", type=float, default=0.5)
    p_qoi.add_argument("--x-hi", type=float, default=2.0)
    p_qoi.add_argument("--tol", type=float, default=1.0, help="相邻检查点容许变化（%）")
    p_qoi.add_argument("--window", type=int, default=3, help="需连续平稳的增量个数")
    p_qoi.add_argument("--rho", type=float, default=1.18415)
    p_qoi.add_argument("--u", type=float, default=50.0)
    p_qoi.add_argument("--reference", type=Path, default=None)
    p_qoi.add_argument("--zone", default=None)

    p_fld = sub.add_parser(
        "field",
        help="二维切片场侧 sanity：反推 nu=k/(omega*TVR) + Re 一致性 + 近壁污染指标")
    p_fld.add_argument("daten", type=Path, help="Y=0 二维切片导出件（带表头列名）")
    p_fld.add_argument("--u", type=float, default=50.0, help="来流速度（用于 Re_unit）")
    p_fld.add_argument("--re-target", type=float, default=5.0e6,
                       help="目标 Re_unit（按单位长度）；给 0 跳过该检查")
    p_fld.add_argument("--nu-tol", type=float, default=2.0, help="nu 反推允许离散度（%%）")
    p_fld.add_argument("--re-tol", type=float, default=2.0, help="Re_unit 允许偏差（%%）")

    p_slc = sub.add_parser(
        "slice",
        help="二维切片诊断：上游伪层 + 前缘 d99 / 理论 + 边界层积分量逐站位表")
    p_slc.add_argument("daten", type=Path, help="Y=0 二维切片导出件（带表头列名）")
    p_slc.add_argument("--u", type=float, default=50.0, help="来流速度（δ99/积分量的基准）")
    p_slc.add_argument("--re-target", type=float, default=5.0e6,
                       help="理论 δ 用的 Re_unit（按单位长度）；给 0 跳过前缘判据")
    p_slc.add_argument("--lead-tol", type=float, default=5.0,
                       help="前缘 d99 允许是理论湍流值的几倍")
    p_slc.add_argument("--up-tol", type=float, default=0.9,
                       help="上游条带近壁 u/U 的下限")

    p_gci = sub.add_parser("gci", help="三档网格 Richardson 外推 + GCI（量取 x>0.5 Cf 均值）")
    p_gci.add_argument("daten", nargs=3, type=Path, metavar=("FINE", "MEDIUM", "COARSE"))
    p_gci.add_argument("--ratios", default="2,2", help="相邻档细化比 r21,r32")
    p_gci.add_argument("--safety", type=float, default=1.25)
    p_gci.add_argument("--x-lo", type=float, default=0.5)
    p_gci.add_argument("--rho", type=float, default=1.18415)
    p_gci.add_argument("--u", type=float, default=50.0)
    p_gci.add_argument("--reference", type=Path, default=None,
                       help="可选：同时打印各档对参考的偏差")
    p_gci.add_argument("--zone", default=None,
                       help="参考文件含多 zone 时必填（如 CFL3D / FUN3D）")

    args = ap.parse_args(argv)

    if args.cmd == "residual":
        rc = 0
        for log in args.logs:
            v = convergence_report(log.read_text(encoding="utf-8", errors="replace"))
            print(f"{log.name}: {v.summary()}")
            print(f"    ok={v.ok} strict_ok={v.strict_ok} "
                  f"(drift_ok={v.drift_ok}, decay_tol={v.decay_tol})")
            for k, d in sorted(v.drift.items()):
                print(f"    drift[{k}] = {d:+.2f}% over window")
            rc |= 0 if (v.strict_ok if args.strict else v.ok) else 1
        return rc

    if args.cmd == "cf":
        xs, taus = read_daten(args.daten)
        xr, cfr = read_reference(args.reference, zone=args.zone)
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

    if args.cmd == "qoi":
        series: list[float] = []
        for p in args.daten:
            xs, taus = read_daten(p)
            cf = cf_from_tau(taus, rho=args.rho, u_inf=args.u)
            q = fully_turbulent_mean_cf(xs, cf, x_lo=args.x_lo, x_hi=args.x_hi)
            series.append(q)
            print(f"{p.name}: mean Cf(x in [{args.x_lo}, {args.x_hi}]) = {q:.6f}")
        v = qoi_stationary(series, tol_pct=args.tol, window=args.window)
        print(v.summary())
        for i, s in enumerate(v.last_step_pcts):
            print(f"    Δ[{i}] = {s:+.4f}%")
        if args.reference is not None:
            xr, cfr = read_reference(args.reference, zone=args.zone)
            ref = fully_turbulent_mean_cf(xr, cfr, x_lo=args.x_lo, x_hi=args.x_hi)
            print(f"reference mean Cf = {ref:.6f}")
            for p, q in zip(args.daten, series):
                print(f"  {p.name}: dev vs reference = {(q - ref) / ref * 100.0:+.2f}%")
        return 0 if v.ok else 1

    if args.cmd == "field":
        try:
            rows = read_field_slice(args.daten)
        except ValueError as exc:
            print(f"error: {exc}")
            return 2
        s = field_sanity(rows, u_inf=args.u, re_target=args.re_target,
                         nu_tol_pct=args.nu_tol, re_tol_pct=args.re_tol)
        print(s.summary())
        print(f"    nu = k/(omega*TVR)  median = {s.nu_median:.6e}  "
              f"(p05-p95 spread {s.nu_spread_pct:.3f}%)")
        print(f"    Re_unit = U/nu     = {s.re_unit:.4g}  "
              f"target = {s.re_target:.4g}  ({s.re_gap_pct:+.2f}%)")
        print(f"    k_max = {s.k_max:.4g}   TVR_max = {s.tvr_max:.4g}")
        print(f"    TVR far (z>=0.8 z_max) = {s.tvr_far:.3f}   "
              f"TVR near max (z<=0.02 z_max) = {s.tvr_near_max:.3f}   "
              f"contrast = {s.tvr_contrast:.1f}x")
        return 0 if s.ok else 1

    if args.cmd == "slice":
        try:
            rows = read_field_slice(args.daten)
        except ValueError as exc:
            print(f"error: {exc}")
            return 2
        fld = field_sanity(rows, u_inf=args.u, re_target=args.re_target,
                           nu_tol_pct=2.0, re_tol_pct=2.0)
        d = diagnose_slice(rows, u_inf=args.u, re_target=args.re_target,
                           lead_tol=args.lead_tol, up_tol=args.up_tol)
        print(fld.summary())
        print(d.summary())
        print(f"    上游 x<0 站位 {d.n_upstream} 个；近壁 u/U 最低 "
              f"{d.up_u_ratio_min:.4f}，k 最高 {d.up_k_max:.4g}")
        print()
        print("     x        d99(mm)   dstar(mm)  theta(mm)    H")
        targets = (-0.30, -0.10, 0.001, 0.01, 0.05, 0.10, 0.25, 0.50, 0.75, 1.00,
                   1.50, 1.99)
        picked: list[tuple[float, float, float, float, float]] = []
        for t in targets:
            cand = [s for s in d.stations if s[0] >= -0.35]
            if not cand:
                continue
            best = min(cand, key=lambda s: abs(s[0] - t))
            if all(abs(best[0] - p[0]) > 1e-9 for p in picked):
                picked.append(best)
        for xv, d99, ds, th, h in sorted(picked):
            print(f"  {xv:8.3f}   {d99:9.4f}   {ds:9.4f}  {th:9.4f}  {h:6.3f}")
        return 0 if (fld.ok and d.ok) else 1

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
        xr, cfr = read_reference(args.reference, zone=args.zone)
        ref = fully_turbulent_mean_cf(xr, cfr, x_lo=args.x_lo)
        print(f"reference mean Cf(x>={args.x_lo}) = {ref:.6f}")
        for p, q in zip(args.daten, qois):
            print(f"  {p.name}: dev vs reference = {(q - ref) / ref * 100.0:+.2f}%")
    return 0 if g.ok else 1


if __name__ == "__main__":  # pragma: no cover - CLI
    raise SystemExit(_main())
