# cfdb validation — Flow Past a Circular Cylinder (Re=40, Steady)

Classic external-flow validation: steady laminar flow past a circular cylinder at Re=40 (D=1 m, U_inf=1 m/s, nu=0.025 m^2/s), OpenFOAM simpleFoam (laminar, SIMPLEC) on an O-type blockMesh grid, far-field radius 50D (100D diameter). Reference: Gautier, Biau & Lamballais (2013), Comput. Fluids 75, pseudo-spectral reference solution Cd=1.49, Lw/D=2.24; corroborated by Posdziech & Grundmann (Cd=1.4942) and the published literature envelope 1.48<=Cd<=1.62, 2.13<=Lw/D<=2.35 (see reference/literature_re40.csv). QoI drag_coeff_cd = total drag coefficient from the forceCoeffs functionObject (Aref = D x unit depth = 1.0); QoI wake_length_lw_over_d = streamwise extent of the recirculation bubble on the wake centerline measured from the rear stagnation point, normalised by D. Tolerance 10% on both QoIs reflects the coarse ~10k-cell demo mesh and the ~5-8% published literature scatter (documented domain decision, not a hidden fudge).

## 交付形式（严格遵守）
输出**单个 ```python 代码块**：脚本在当前工作目录创建 `case/` 子目录，
写入完整可运行的 OpenFOAM 算例（至少 `0/`、`constant/`、`system/`，含
`system/controlDict` 且其 `application` 条目声明所用求解器；需要 blockMesh
的算例写 `system/blockMeshDict`）。不要自行运行求解器——判分侧会在
OpenFOAM v2312 环境按案例声明的步骤（blockMesh → 求解器 → 后处理）真实执行，
然后用案例冻结的 QoI 脚本从算例产物提取指标并与留出参考值对账。

## 物理与工况
- flow=incompressible, turbulence=none, dim=2d, steady=True
- 工况: reynolds=40.0
- 评测 QoI（判分脚本从你的算例产物提取）: drag_coeff_cd, wake_length_lw_over_d
- 参考类型: dns；容差为上游文档化决策（网格/格式耗散），不自报数值。

注意：采样/后处理 functionObject（probes、forces 等）必须按上方描述正确配置，
否则判分脚本将因找不到产物而判 0 分（它不会编造数值）。
