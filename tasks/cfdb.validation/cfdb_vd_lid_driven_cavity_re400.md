# cfdb validation — Lid-Driven Cavity (Re=400)

Classic lid-driven cavity benchmark, OpenFOAM icoFoam, laminar Re=400 (L=0.1 m, U_lid=1 m/s, nu=2.5e-4). Reference: Ghia, Ghia & Shin (1982), J. Comput. Phys. 48, Table I Re=400 column (17 stations, transcription verified against multiple independent reproductions). QoI centerline_umax = max |U|/U_lid on the vertical centerline probe line (y/H up to 0.95): interpolated Ghia value 0.551 at y/H=0.95. Tolerance 10% reflects the 64x64 demo mesh and the linear interpolation across the wide 0.8516-0.9531 station gap (documented domain decisions, not hidden fudges).

## 交付形式（严格遵守）
输出**单个 ```python 代码块**：脚本在当前工作目录创建 `case/` 子目录，
写入完整可运行的 OpenFOAM 算例（至少 `0/`、`constant/`、`system/`，含
`system/controlDict` 且其 `application` 条目声明所用求解器；需要 blockMesh
的算例写 `system/blockMeshDict`）。不要自行运行求解器——判分侧会在
OpenFOAM v2312 环境按案例声明的步骤（blockMesh → 求解器 → 后处理）真实执行，
然后用案例冻结的 QoI 脚本从算例产物提取指标并与留出参考值对账。

## 物理与工况
- flow=incompressible, turbulence=none, dim=2d, steady=False
- 工况: reynolds=400.0
- 评测 QoI（判分脚本从你的算例产物提取）: centerline_umax
- 参考类型: dns；容差为上游文档化决策（网格/格式耗散），不自报数值。

注意：采样/后处理 functionObject（probes、forces 等）必须按上方描述正确配置，
否则判分脚本将因找不到产物而判 0 分（它不会编造数值）。
