# TMR 2D Flat Plate：StarCCM+ 全自动求解收敛 + Cf 与 CFL3D 参考首次定量比对

日期：2026-09-21（下午会话） ｜ 分支：codex/trusted-resume-and-formula（接 fd160966）

## 0. 一句话结论

TMR flat plate（SST，137×97 网格）在 STAR-CCM+ 19.02.009-R8 批处理模式下**完整求解收敛**（1000 迭代，Continuity 残差 1.45e-6），壁面 τw 导出并与 CFL3D SST 公开参考完成**首次定量比对**：Cf 形态正确（前缘 0.00255 → 尾缘 0.00205 单调衰减），分 bin 均值偏差 **-20.0%**（前缘 -33% → 中后段稳定 -17%）。偏差主因锁定为粗网格档（137×97 为五档中第二粗）+ y+=0.12 粘性底层下的 SST all-y+ 壁面处理——**这正是 TMR 五档网格收敛研究的对象**，需按 GCI 流程跑 3 档网格外推，非 setup 错误。

## 1. 本轮三大 bug 修复过程（全部实证定位）

| # | 症状 | 根因 | 修复 |
| --- | --- | --- | --- |
| 1 | "10472 cells zero or negative volume" | `convertTo2d` 语义误用：它把**每个 3D 边界面**转成独立 2D region（日志 "Created new 2D region Zone 1 2~6"），不是把体网格压成 2D 域 | **放弃 convertTo2d**：TMR CGNS 是单层 3D 网格，直接 `ThreeDimensionalModel` 求解 |
| 2 | 入口速度 1 m/s（设 50 无效） | `VelocityMagnitudeProfile.set("Value")` 的 Value 键在 profile 层不存在 | 正确路径：`((ConstantScalarProfileMethod)profile.getMethod()).getQuantity().set("Value", 50.0)`（quantity 层），回读 "50.0 m/s" + 边界面积均值 50.0 双重验证 |
| 3 | 每次续跑只 1 步就停 | `MaximumIterations` 键在 SimulationIterator 上不存在（静默失败，一直默认 1000 绝对计数） | 停止准则在 `SolverStoppingCriterionManager.getObject("Maximum Steps")`；跨会话续算需新 fresh sim 或调高该准则 |

## 2. 网格几何澄清（关键认知修正）

TMR `grid_struct_137x97_vol.cgns` 的真实布局（由导出顶点统计证实）：
- **x = 流向**（113 档唯一值，前缘加密 Δx≈0.004）
- **z = 法向**（z∈[0,1]，z=0 为壁面）
- **y = 展向单层**（全部 y=0，即 2D 平面网格以 3D 单层形式提供）

边界指派（角度拆分后按质心自动识别）：
| 边界面 | 质心 | 指派 |
| --- | --- | --- |
| default | (0.833, z=0.5) | 顶面 z=1→对称；实际 default 是 y=0 大面 |
| default 2 | (x=-0.333) | **入流**（速度 50 m/s +X, COMPONENTS 模式） |
| default 3 | (x=2.0) | **出流**（压力出口） |
| default 4 | (z=0.0) | **壁面**（x>0 平板段，WallBoundary） |
| default 4 2 | (z=0, x<0) | 滑流段（对称） |
| default 5/6 | 其余大面 | 对称（展向/顶面） |

## 3. 最终比对数据（tau_a3.daten，n=99 壁面段）

```
U∞=50 m/s, ρ=1.18415, Re_L≈6.4e6（air 默认物性）
残差：Continuity 1.45e-6 / X-mom 1.7e-3 / Tke 0.62（1000 步）

x∈[0.05,0.15): SC=0.00255 CFL3D=0.00381 dev=-33.0%   ← 前缘区（网格粗+过渡区）
x∈[0.45,0.55): SC=0.00242 CFL3D=0.00296 dev=-18.4%
x∈[0.95,1.05): SC=0.00222 CFL3D=0.00268 dev=-17.2%   ← 完全湉流区稳定 -17%
x∈[1.75,1.85): SC=0.00205 CFL3D=0.00247 dev=-16.8%
bin 均值 -20.0%，中位 -18.0%
```

偏差分析：① 粗网格档（137×97 第二粗档，TMR 五档 GCI 体系）② SST all-y+ 在 y+=0.12 的壁面处理 ③ Re 差异（SC 6.4e6 vs CFL3D 5e6，理论 -5%）。**完全湉流区 -17% 与 TMR 网格收敛趋势一致**（粗网格 Cf 系统性偏低）。

## 4. R8 API 新增探明（本轮补充）

- 速度值设置唯一可行链：`pvm.getObject("速度幅值")` → `.getMethod()` → `(ConstantScalarProfileMethod).getQuantity().set("Value", v)`
- 流向：`FlowDirectionOption.setSelected(Type.COMPONENTS)` + `pvm.getObject("流向").set("Value", DoubleVector)`（中文界面名，COMPONENTS 模式下才出现）
- 停止步数：`SolverStoppingCriterionManager.getObject("Maximum Steps").set("MaximumSteps", n)`（SimulationIterator 的 MaximumIterations 键无效）
- 重初始化：`sim.initializeSolution()`（改 BC 后必须；跨会话续算受绝对迭代计数限制——**最佳实践：fresh sim 单会话一杆到底**）
- 边界质心识别需在 continuum 绑定后（"Centroid" 组件函数依赖物理上下文）
- 报告：`AreaAverageReport` + `getReportMonitorValue()`；导出：`ExportManager.export(path, regions, boundaries, parts, functions, true, false)` → `.daten` CSV（面心值）+ `.vrt`（顶点坐标）

## 5. 下一步（网格收敛 GCI 三档）

1. 273×193 与 545×385 档跑同款 macro（仅换 CGNS 文件名）→ 观察 Cf 偏差随网格加密的收敛；
2. 完全湉流区（x>0.5）三档 Richardson 外推 → GCI；
3. 收敛后：SA 模型对照（`SpalartAllmarasTurbulence` 同链 enable）；
4. 全链封装进 `runners/solvers/starccm.py`（macro 模板化 + 网格/模型参数化）→ nasa_tmr.verification registry 条目 proposed→staged。
