# cfdb validation — Circular Cylinder (Re=100, Unsteady Vortex Shedding)

Unsteady laminar flow past a circular cylinder at Re=100 (Karman vortex shedding), OpenFOAM pimpleFoam, ESI v2312. Setup: D=1 m, U_inf=1 m/s, nu=0.01 -> Re=100; O-grid blockMesh (constant/polyMesh/blockMeshDict), 120 circumferential x 50 radial x 1 = 6000 cells, cylinder at origin, circular freestream boundary at R=20 (20D), freestream BCs. The forceCoeffs function object (system/controlDict) writes the Cl/Cd time series EVERY timestep to postProcessing/forceCoeffs1/0/coefficient.dat (Aref = D x span = 1 x 0.1 = 0.1 m2, lRef = D = 1 m, rhoInf = 1). endTime = 300 s = ~49 shedding cycles (period ~6.1 s at St~0.164); the first 150 s (~25 cycles) are startup transient and must be discarded before statistics — the first full 300 s run (2026-08-11, runs/20260811T115926Z_cylinder_re100_openfoam_c45efbd2, 489 s wall, docker v2312) measured the impulsively started wake still saturating until t~150 s (cl_rms 0.181 for t>=60 vs 0.212 for t>=150, then flat), so the original 60 s discard under-predicted cl_rms by ~15% and was raised to 150 s on that evidence. QoIs derived from that series (post/compute_qoi.py): strouhal = f_peak*D/U from the Goertzel power scan of Cl over t>=150 s (search band 0.05-0.35 Hz); cd_mean = time-mean Cd; cl_rms = std of Cl (mean Cl ~ 0 by symmetry). Full-run verified values (t>=150 s): St = 0.1620 (1.2% err), Cd_mean = 1.3174 (1.0% err), cl_rms = 0.2120 (7.8% err) — all within tolerance, overall_status pass. Reference: literature consensus for 2-D laminar shedding at Re=100 — St = 0.164 (Williamson 1988 St-Re relation gives 0.1643 at Re=100; 2-D simulations 0.1644-0.166), Cd_mean = 1.33 (Park, Kwon & Choi 1998; consensus band 1.32-1.36), Cl_rms = 0.23 (consensus band 0.226-0.235: Park 1998, Mittal 2005, Stalberg 2006, Posdziech & Grundmann 2007). Cross-verified 2026-08-11 against multiple independent secondary sources, see provenance.yaml notes. Tolerances (St 3%, Cd 6%, Cl_rms 15%) reflect the 6000-cell demo mesh and single-core adjustable-Co run — a documented domain decision (coarse demo grid + literature band width), not a hidden fudge.

## 要求
- 求解器族: OpenFOAM（上游基准使用 ESI v2312 语义）；从零搭建完整可运行案例（0/ constant/ system/ + Allrun），真实求解到 case 指定的终止时刻。
- 物理设定: flow=incompressible, turbulence=none, dim=2d, steady=False
- 工况: reynolds=100.0
- 输出 QoI: strouhal, cd_mean, cl_rms
- 参考类型: experimental（容差见任务 YAML reference.tolerances；判分用冻结 QoI 脚本）

## 交付
写 result.json，字段为上述 QoI 名（数值，与 QoI 定义单位一致）。
