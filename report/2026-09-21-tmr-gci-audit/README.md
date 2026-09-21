# TMR flat plate 网格收敛审计（阶段一）：此前 GCI 结论作废

日期：2026-09-21（晚场） ｜ 分支：`codex/trusted-resume-and-formula`（接 `cb6a95fa`）
前置证据：`report/2026-09-21-tmr-flatplate-converged/`（该报告的核心结论在本轮被推翻）

## 0. 一句话

**`report/2026-09-21-tmr-flatplate-converged` 里"粗网格系统性 -17%"的结论是错的。**
真因是 STAR-CCM+ 的迭代上限设置**静默失效**（所有 run 只跑了默认 1000 步），细网格的
k 方程远未收敛。把 137×97 档跑到 6000 步，完全湍流区偏差从 **-17.4% 收敛到 -8.1%**，
尾缘从 -16.4% 收到 **-1.9%**——偏差是「没跑够」，不是「网格粗」。

## 1. 触发线索：a4 与 a4t 逐字节相同

排查时先发现两件「不该发生的事」：

| 证据 | 结果 | 含义 |
| --- | --- | --- |
| `md5sum tau_a4.daten tau_a4t.daten` | **完全相同** | a4t 那次 run 什么都没改 |
| `diff` 两份日志的残差块 | **空** | 两 run 逐位一致 → a4t 是 no-op |

根因：a4t 用了错误的中文键（`湍流规范`），两段 `try` 都抛
`Named object ... does not exist in manager` 被吞掉，宏照常 `EXIT=0`。
**宏静默失败是本轮所有误判的共同形态。**

## 2. 三条 R8 macro 静默失效陷阱（反射探查实证）

### 2.1 迭代上限：只有 typed setter 生效

```java
msc.set("MaximumSteps", 1500);        // ❌ ClientServerObject.set(String,int) = 静默 no-op
((StepStoppingCriterion) msc).setMaximumNumberSteps(6000);   // ✅
```

实测回读：`LR-BEFORE-MAXSTEPS 1000` → `LR-AFTER-MAXSTEPS 6000`。
此前 a3/a4/a5/a4t2 **全部只有 1000 步**（默认值），而宏里"设了 1500"是无效果的。
`SimulationIterator` 也没有 `MaximumIterations` 键。

### 2.2 方法选择器与数值 profile 是两个对象

- 湍流方法选择器的键名是 **`湍流指定`**（`star.kwturb.KwTurbSpecOption`），选项枚举
  `star.kwturb.KwTurbSpecOption$Type` = `K_OMEGA` / `INTENSITY_LENGTH_SCALE` /
  `INTENSITY_VISCOSITY_RATIO`。**不存在 `湍流规范` 这个键。**
- 入口与初始条件的默认选择器**都已经是 `INTENSITY_VISCOSITY_RATIO`**，默认
  Ti = 1 %、TVR = 10。
  ⇒ **此前"细网格崩塌是因为入口湍流规格缺失"的诊断是错的**（a4t2 反而把入口 k 降了 100×）。

### 2.3 场函数按 function name 查，不是显示名

`getFunction("Turbulent Kinetic Energy")` 静默返回 `null` → 报告报
`Field function is not set`。必须用 `TurbulentKineticEnergy` / `SpecificDissipationRate` /
`TurbulentViscosityRatio` / `WallYplus` 等英文无空格的 function name。
（`Centroid`/`Velocity`/`WallShearStress` 恰好同名，所以以前没暴露这个问题。）

## 3. 「Tke 残差 82 = 发散」也是误判

a4t2 的 Tke@1000 = 82.2，看着像发散。逐迭代对照后发现它与 a4（默认 Ti=1 %）
**轨迹形状完全相同、比例恰好 ≈100×**：

| iter | a4 / long273（Ti=1 %） | a4t2（Ti=0.1 %） | 比值 |
| --- | --- | --- | --- |
| 51 | 4.8869e-01 | 5.1447e+01 | 105 |
| 301 | 6.4896e-01 | 6.7283e+01 | 104 |
| 501 | 5.7665e-01 | 5.7819e+01 | 100 |
| 755 | 6.6451e-01 | 6.7115e+01 | 101 |

`k_inlet ∝ Ti²`，Ti 差 10× ⇒ k 场差 100× ⇒ **残差按 k 量级归一化，整体缩放 100×**。

> **纪律**：湍流残差的绝对量级不可跨算例比较。同一 273 网格，Ti=1 % 时 Tke@1000
> 其实是 **0.826**，不是 82.2。

## 4. 阶段一核心结果：多迭代带来的收敛（137×97 档）

`long137`（6000 步，`tau_l137.daten`）对比 `allin3`（1000 步）：

| 区域 | @1000 步 | **@6000 步** |
| --- | --- | --- |
| 完全湍流区 [0.5, 2.0] 插值均值 | −17.41 % | **−8.12 %** |
| 尾缘 [1.75, 2.0) | −16.4 % | **−1.9 %** |
| 前缘 [0, 0.25) | −37.0 % | −35.7 %（TMR 已知转捩/前缘奇异区，非网格收敛量） |

分 bin 模型 Cf（6000 步）：0.002588 → 0.002512 → 0.002480 → 0.002459 → 0.002442 →
0.002430 → 0.002419 → 0.002411 —— **教科书式单调递减的湍流 Cf 形态**。

残差：`long137` 通过收敛门，最近 300 步 Tke 漂移 **−0.02 %**（`allin3` 为 −36 %）。

## 5. 收敛门判据（已实现为仓库件）

`runners/tmr_cf.py::convergence_report` = continuity/momentum 阈值 + 最近窗内湍流残差
不得系统性回升（默认窗 300 步、允许回升 5 %）。对历史日志回测：

| 日志 | 判定 | 最近窗 Tke 漂移 |
| --- | --- | --- |
| `allin3`（137 @1000） | PASS | −36.05 % |
| `long137`（137 @6000） | **PASS** | **−0.02 %** |
| `allin_a4`（273 @1000） | **FAIL** | **+30.61 %** |
| `allin_a5`（545 @1000） | PASS | −9.27 % |
| `allin_a4t2`（273/Ti0.1% @1000） | FAIL | +28.94 % |

判据成功拦住了产出「伪层流 Cf」的那次 273 run。

### 5.1 但残差门通过 ≠ 解正确

545×385 档残差**平滑下降**（Tke 0.54 → 0.49，单调）却在 1000 步时壁面 τ 崩塌
（Cf ~1e-5，见第 6 节）。**必须叠加场侧 sanity**：壁面 k > 0、μt/μ > 1、Cf 量级对
层流量级（`0.664/√Re_x`）留出合理裕度。

### 5.2 前缘奇异点会把 k 残差"托底"

上游对称面近前缘处的伪湍动能尖峰在 50 m/s 来流下达到 **k ≈ 26–93 m²/s²**：

| 位置 | 137×97 @1000 | 273×193 @1000 | 137×97 @6000 |
| --- | --- | --- | --- |
| 上游对称面 k（x<0, z=0） | 81.3 | 26.3 | 92.7 |
| 入口 k | 0.375 | 0.375 | 0.375 |
| 出口 k | 0.507 | 2.346 | 0.389 |
| 出口 μt/μ | 30.6 | 117.5 | 28.1 |
| 壁面 y+ | 0.107 | 0.058 | 0.112 |

这是个持续的残差源 ⇒ 本 case 的 k 残差可能长期停在 0.1–1 量级而不趋零。
**⇒ `nasa_tmr.verification` 的收敛定义必须落在 QoI（Cf）平稳 + 场侧 sanity，而不是
k 残差阈值。** 否则该任务永远过不了自己设的 gate。

## 6. 细网格「准层流」的定位（@1000 步）

| 档 | 全板偏差 | 完全湍流区 | 壁面 Cf 量级 |
| --- | --- | --- | --- |
| 137×97 | −25.3 % | −17.4 % | 0.00217（湍流级） |
| 273×193 | −71.8 % | −79.4 % | 0.00044 |
| 545×385 | −99.7 % | −99.8 % | ~1e-5（τ 崩塌） |

层流参照：`Cf_lam = 0.664/√Re_x`，x=1 处 Re_x = 3.19e6 → **3.72e-4**。
273 档给出 **4.43e-4 ≈ 1.19× 层流值** ⇒ 该解基本无涡粘，是**初始化/收敛**问题而非网格效应。

### 6.1 已定位的一个具体缺陷：湍流初始条件参考速度

IC 的 k 由 `k = 1.5·(Ti·V_ref)²` 得到，`V_ref` 取自初始条件对象 **`湍流速度比例`**，
**默认只有 1.0 m/s**（与来流 50 m/s 无关）：

- IC k = 1.5·(0.01·1.0)² = **1.5e-4**
- 入口 k = 1.5·(0.01·50)² = **0.375** —— 相差 **2500×**

细网格单元小、k 只能靠对流/扩散从入口输运进来，所以粗网格靠数值扩散"蒙对"、
细网格来不及发育。**修正**：把 IC 的 `湍流速度比例` 设为 50 m/s，实测
`INIT-K-OUT` 从 1.5e-4 变为 **0.375**（与入口一致）、`INIT-OM-OUT` = 2393.7。

## 7. 本轮新增仓库件

- `runners/tmr_cf.py`（提交 `cb6a95fa`）：残差表**表头驱动**解析 + 收敛门 + `.daten`/TMR
  参考解析 + Cf 分 bin/插值偏差 + Richardson/GCI + 误差带评分 + CLI
  （`python -m runners.tmr_cf residual|cf|gci`）。
- `tests/test_tmr_cf.py`：26 例；含「复刻 273 实测 Tke 回升必须 FAIL 收敛门」回归锚。
- 全量基线 **176 例 0 failures**（8 errors 仍为 WinError 1314 symlink 特权，与之前一致）。

## 8. 复现命令

```bash
export JAVA_TOOL_OPTIONS="-Dfile.encoding=UTF-8"
SB="/c/Program Files/Siemens/19.02.009-R8/STAR-CCM+19.02.009-R8/star/bin/starccm+.bat"
"$SB" -new -batch long137.java > long137_out.log 2>&1     # 6000 步，迭代上限真设上

cd /d/comacbench
.venv/Scripts/python.exe -m runners.tmr_cf residual <log>
.venv/Scripts/python.exe -m runners.tmr_cf cf tau_l137.daten ../cf_plate_sstv.dat --bins 8
.venv/Scripts/python.exe -m runners.tmr_cf gci <fine.daten> <medium.daten> <coarse.daten> --reference ../cf_plate_sstv.dat
```

## 9. 阶段二（进行中，尚未写入本报告）

- `long273`（273×193，默认 IC，6000 步）与 `seed273`（273×193，IC 种子化，3000 步）
  正在跑，用于回答「细网格能否收敛到湍流 Cf」以及「IC 种子化能省多少迭代」。
- 待办：545×385 重跑 → 三档 GCI/Richardson 外推（量取 x>0.5 Cf 均值）→ SA 对照 →
  全链封装进 `runners/solvers/starccm.py` → registry `nasa_tmr.verification`
  proposed → staged（并同步修订其收敛定义）。
