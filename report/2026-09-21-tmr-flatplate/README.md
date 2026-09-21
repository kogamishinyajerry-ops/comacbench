# TMR 2D Flat Plate 首算例：StarCCM+ 批处理求解链落地（数值收敛未完成）

日期：2026-09-21 ｜ 分支：codex/trusted-resume-and-formula（接 ef779942 StarCCM 后端）

## 0. 一句话结论

nasa_tmr.verification 首算例（2D flat plate，SST，grid_struct_35x25）的 **StarCCM+ 全自动批处理链路已打通到最后一步**：CGNS 导入 → 角度拆分 → 2D 转换 → 物理连续体（SST 全链 enable）→ x=0 滑流/平板拆分 → 边界类型指派 → 入口速度幅值 50 m/s 设置 → 迭代求解器启动。**求解器真实执行**（wall distance 计算、AMG 代数多重网格运行）但在粗网格上初始迭代发散（AMG Residual 非有限值）——数值稳定性调优（CFL/松弛因子/初始化策略）为下一步，不影响链路正确性结论。

## 1. R8 批处理 API 探明记录（本轮核心资产）

通过 26 个渐进式反射探针宏（probe~probeZ，全部批处理无 GUI），探明 STAR-CCM+ 19.02.009-R8 的可编程面：

| 环节 | API | 备注 |
| --- | --- | --- |
| 网格导入 | `sim.getImportManager().importMeshFiles(String[])` | CGNS 直接支持 |
| 边界拆分(角度) | `sim.getMeshManager().splitBoundariesByAngle(45.0, Collection<Boundary>)` | default→6 面 |
| 边界拆分(函数) | `mm.splitBoundariesByFunction(uff, Collection<Boundary>)` | UFF `$$Centroid[0] > 0.0`（两美元，非三美元；无需单位后缀） |
| 2D 转换 | `mm.convertTo2d(0.1)` | **转换后 Region 重建，旧引用失效**（NPE 陷阱） |
| 物理连续体 | `createContinuum(PhysicsContinuum.class)` + 逐层 `pc.enable(...)` | 分层链：TwoDimensional(metrics)→SingleComponentGas(material)→SegregatedFlow(segregatedflow)→Steady(common)→ConstantDensity(flow)→Isothermal(segregatedenergy)→**Turbulent→RansTurbulence(turbulence)→KOmegaTurbulence(kwturb)→SstKwTurbModel(kwturb)→KwAllYplusWallTreatment(kwturb)** |
| 边界类型 | `b.setBoundaryType(InletBoundary.class)` 等 | Inlet/Outlet/Symmetry/Wall |
| 边界质心 | `AreaAverageReport` + `Centroid.getComponentFunction(0)` + `rep.getParts().setObjects(b)` | 2D 转换后 Y=0 面即四侧 |
| 速度设置 | `pvm.getObject("速度幅值")` → `ScalarProfile.set("Value", 50.0)` | **中文界面名**；`get(VelocityProfile.class)` 不可用（Condition not found——R8 削减） |
| 求解 | `sim.getSimulationIterator().run()` / `run(int)` / `step(int)` | `sim.initialize()/sim.run()` 不存在 |
| 保存 | `sim.saveState(path)` | |

关键失败记录（避免重踩）：`star.flow.FixedProfile`/`ConstantVelocityProfile` 类不存在；`NeoProperty` 需显式 import `star.base.neo.*`；`VelocityProfile.setMethod` 的 method 类不在已加载包；field function 语法 `$$$` 编译错、`$$Centroid[0]` 正确。

## 2. 求解状态（attempt 1）

- 网格：grid_struct_35x25（最粗档，TMR 5 档中 level 5）——35×25 结构网格
- 物理：2D 稳态分离流 + SST（all-y+ 壁面处理）
- BC：入口幅值 50 m/s（流向 +X 默认）、出口压力、顶/滑流对称、平板壁面
- 迭代：`run(0,false)` 初始化 metrics 错（不致命），`run()` 首次迭代 AMG Residual 非有限值 → 发散
- 证据：solve-attempt1.log（含 wall distance 532 cells limited、AMG coarsening halted 警告——粗网格 167 行精度不足）

## 3. 下一步（数值收敛调优清单）

1. 材料属性核对：默认 air（SI）vs 域尺寸（米）——显式设 ρ=1.2? 直接用 ν=2e-5 对应 μ；参考值 Cf 的 ρ∞、U∞ 需与 TMR 归一化一致；
2. 发散对策（按优先级）：降低 CFL/松弛因子（默认 0.4? 改 0.1 起）→ FMG 初始化 → 换 KwLowYplusWallTreatment（粗网格 y+ 大时 all-y+ 更稳，已选对）→ 升级到 137×97 网格（35×25 太粗导致 AMG 精度不足，日志已明示）；
3. Cf 导出链（求解收敛后）：plate 边界 `SkinFrictionCoefficient` 场函数 + XYPlot/表导出 → 与 cf_plate_sstv.dat（CFL3D SST 参考，993 点）比对 → 相对偏差统计；
4. 收敛判据 grader 侧：迭代残差 <1e-6 + Cf 分布双时间步不动性。

## 4. 资产清单（report/2026-09-21-tmr-flatplate/）

- solve-attempt1.log：完整求解尝试日志（发散证据）
- solve-macro.java：终版求解宏（含全部 API 用法）
- cf_plate_sstv.dat / cf_plate_sa.dat：TMR CFL3D SST/SA 参考 Cf 沿板分布（tmbwg.github.io 新站）
- grid_struct_35x25_vol.cgns：TMR 最粗网格（flatplategrids-grids.zip，NASA nasa.gov 2026/02 上传）
- 工作目录 C:/Users/Kogami/cb_dl/tmr/：中间 sim 存档（flatplate_setup/split/full2/ready.sim）+ 26 个探针宏
