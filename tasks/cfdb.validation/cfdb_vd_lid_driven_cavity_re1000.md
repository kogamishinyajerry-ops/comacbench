# cfdb validation — Lid-Driven Cavity (Re=1000)

Classic lid-driven cavity benchmark, OpenFOAM icoFoam, laminar Re=1000 (L=0.1 m, U_lid=1 m/s, nu=1e-4). Reference: Ghia, Ghia & Shin (1982), J. Comput. Phys. 48, Table I Re=1000 column. QoI centerline_umax = max |U|/U_lid on the vertical centerline probe line (y/H up to 0.95): linear interpolation of the Ghia table between y/H=0.8516 (0.33304) and y/H=0.9531 (0.46604) gives 0.462 at y/H=0.95. Tolerance 10% is a documented domain decision, not a hidden fudge: it covers (a) the reference being a linear interpolation at the probe-line top rather than a tabulated point, (b) the QoI measuring |U|=sqrt(u^2+v^2) while the reference tabulates u only, (c) the uniform 128x128 mesh vs Ghia's 129x129 multigrid solution, and (d) the finite integration time t=30 s (300 lid turnovers) vs the true steady state.

## 交付形式（严格遵守）
输出**单个 ```python 代码块**：脚本在当前工作目录创建 `case/` 子目录，
写入完整可运行的 OpenFOAM 算例（至少 `0/`、`constant/`、`system/`，含
`system/controlDict` 且其 `application` 条目声明所用求解器；需要 blockMesh
的算例写 `system/blockMeshDict`）。不要自行运行求解器——判分侧会在
OpenFOAM v2312 环境按案例声明的步骤（blockMesh → 求解器 → 后处理）真实执行，
然后用案例冻结的 QoI 脚本从算例产物提取指标并与留出参考值对账。

## 物理与工况
- flow=incompressible, turbulence=none, dim=2d, steady=False
- 工况: reynolds=1000.0
- 评测 QoI（判分脚本从你的算例产物提取）: centerline_umax
- 参考类型: dns；容差为上游文档化决策（网格/格式耗散），不自报数值。

注意：采样/后处理 functionObject（probes、forces 等）必须按上方描述正确配置，
否则判分脚本将因找不到产物而判 0 分（它不会编造数值）。
