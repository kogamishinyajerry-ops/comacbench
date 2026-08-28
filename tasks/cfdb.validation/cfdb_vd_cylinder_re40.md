# cfdb validation — Flow Past a Circular Cylinder (Re=40, Steady)

Classic external-flow validation: steady laminar flow past a circular cylinder at Re=40 (D=1 m, U_inf=1 m/s, nu=0.025 m^2/s), OpenFOAM simpleFoam (laminar, SIMPLEC) on an O-type blockMesh grid, far-field radius 50D (100D diameter). Reference: Gautier, Biau & Lamballais (2013), Comput. Fluids 75, pseudo-spectral reference solution Cd=1.49, Lw/D=2.24; corroborated by Posdziech & Grundmann (Cd=1.4942) and the published literature envelope 1.48<=Cd<=1.62, 2.13<=Lw/D<=2.35 (see reference/literature_re40.csv). QoI drag_coeff_cd = total drag coefficient from the forceCoeffs functionObject (Aref = D x unit depth = 1.0); QoI wake_length_lw_over_d = streamwise extent of the recirculation bubble on the wake centerline measured from the rear stagnation point, normalised by D. Tolerance 10% on both QoIs reflects the coarse ~10k-cell demo mesh and the ~5-8% published literature scatter (documented domain decision, not a hidden fudge).

## 要求
- 求解器族: OpenFOAM（上游基准使用 ESI v2312 语义）；从零搭建完整可运行案例（0/ constant/ system/ + Allrun），真实求解到 case 指定的终止时刻。
- 物理设定: flow=incompressible, turbulence=none, dim=2d, steady=True
- 工况: reynolds=40.0
- 输出 QoI: drag_coeff_cd, wake_length_lw_over_d
- 参考类型: dns（容差见任务 YAML reference.tolerances；判分用冻结 QoI 脚本）

## 交付
写 result.json，字段为上述 QoI 名（数值，与 QoI 定义单位一致）。
