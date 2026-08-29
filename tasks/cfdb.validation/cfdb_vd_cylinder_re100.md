# cfdb validation — Circular Cylinder (Re=100, Unsteady Vortex Shedding)

Unsteady laminar flow past a circular cylinder at Re=100 (Karman vortex shedding), OpenFOAM pimpleFoam, ESI v2312. Setup: D=1 m, U_inf=1 m/s, nu=0.01 -> Re=100; O-grid blockMesh (constant/polyMesh/blockMeshDict), 120 circumferential x 50 radial x 1 = 6000 cells, cylinder at origin, circular freestream boundary at R=20 (20D), freestream BCs. The forceCoeffs function object (system/controlDict) writes the Cl/Cd time series EVERY timestep to postProcessing/forceCoeffs1/0/coefficient.dat (Aref = D x span = 1 x 0.1 = 0.1 m2, lRef = D = 1 m, rhoInf = 1). endTime = 300 s = ~49 shedding cycles (period ~6.1 s at St~0.164); the first 150 s (~25 cycles) are startup transient and must be discarded before statistics — the first full 300 s run (2026-08-11, runs/20260811T115926Z_cylinder_re100_openfoam_c45efbd2, 489 s wall, docker v2312) measured the impulsively started wake still saturating until t~150 s (cl_rms 0.181 for t>=60 vs 0.212 for t>=150, then flat), so the original 60 s discard under-predicted cl_rms by ~15% and was raised to 150 s on that evidence. QoIs derived from that series (post/compute_qoi.py): strouhal = f_peak*D/U from the Goertzel power scan of Cl over t>=150 s (search band 0.05-0.35 Hz); cd_mean = time-mean Cd; cl_rms = std of Cl (mean Cl ~ 0 by symmetry). Full-run verified values (t>=150 s): St = 0.1620 (1.2% err), Cd_mean = 1.3174 (1.0% err), cl_rms = 0.2120 (7.8% err) — all within tolerance, overall_status pass. Reference: literature consensus for 2-D laminar shedding at Re=100 — St = 0.164 (Williamson 1988 St-Re relation gives 0.1643 at Re=100; 2-D simulations 0.1644-0.166), Cd_mean = 1.33 (Park, Kwon & Choi 1998; consensus band 1.32-1.36), Cl_rms = 0.23 (consensus band 0.226-0.235: Park 1998, Mittal 2005, Stalberg 2006, Posdziech & Grundmann 2007). Cross-verified 2026-08-11 against multiple independent secondary sources, see provenance.yaml notes. Tolerances (St 3%, Cd 6%, Cl_rms 15%) reflect the 6000-cell demo mesh and single-core adjustable-Co run — a documented domain decision (coarse demo grid + literature band width), not a hidden fudge.

## 交付形式（严格遵守）
输出**单个 ```python 代码块**：脚本在当前工作目录创建 `case/` 子目录，
写入完整可运行的 OpenFOAM 算例（至少 `0/`、`constant/`、`system/`，含
`system/controlDict` 且其 `application` 条目声明所用求解器；需要 blockMesh
的算例写 `system/blockMeshDict`）。不要自行运行求解器——判分侧会在
OpenFOAM v2312 环境按案例声明的步骤（blockMesh → 求解器 → 后处理）真实执行，
然后用案例冻结的 QoI 脚本从算例产物提取指标并与留出参考值对账。

## 物理与工况
- flow=incompressible, turbulence=none, dim=2d, steady=False
- 工况: reynolds=100.0
- 评测 QoI（判分脚本从你的算例产物提取）: strouhal, cd_mean, cl_rms
- 参考类型: experimental；容差为上游文档化决策（网格/格式耗散），不自报数值。

注意：采样/后处理 functionObject（probes、forces 等）必须按上方描述正确配置，
否则判分脚本将因找不到产物而判 0 分（它不会编造数值）。
