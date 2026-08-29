# cfdb validation — Backward-Facing Step (Laminar, Re=100)

Classic laminar backward-facing step benchmark (expansion ratio ER=2), OpenFOAM simpleFoam laminar (steady SIMPLE). Step height h=0.01 m, mean inlet velocity Um=1 m/s with a fully developed parabolic inlet profile, nu=2e-4 -> Re = Um*D_h/nu = 100 (D_h = 2*inlet channel height, the Armaly et al. 1983 / Erturk 2008 convention). Demo mesh 6100 cells (3 conformal hex blocks, inlet channel 5h, downstream 30h). QoI reattachment_x_over_h = primary reattachment length x_r/h, located by the Ux sign change on a near-bottom sample line (first-cell-centre height). Reference: Erturk (2008) Comput. Fluids 37:633-655, x_r/h = 2.922 at Re=100. A real run of the shipped case on opencfd/openfoam-default:2312 (2026-08-11, SIMPLE converged in 459 iterations) gave x_r/h = 2.8715 (1.73% error). Tolerance 10% reflects the coarse demo mesh (documented domain decision, not a hidden fudge).

## 交付形式（严格遵守）
输出**单个 ```python 代码块**：脚本在当前工作目录创建 `case/` 子目录，
写入完整可运行的 OpenFOAM 算例（至少 `0/`、`constant/`、`system/`，含
`system/controlDict` 且其 `application` 条目声明所用求解器；需要 blockMesh
的算例写 `system/blockMeshDict`）。不要自行运行求解器——判分侧会在
OpenFOAM v2312 环境按案例声明的步骤（blockMesh → 求解器 → 后处理）真实执行，
然后用案例冻结的 QoI 脚本从算例产物提取指标并与留出参考值对账。

## 物理与工况
- flow=incompressible, turbulence=none, dim=2d, steady=True
- 工况: reynolds=100.0
- 评测 QoI（判分脚本从你的算例产物提取）: reattachment_x_over_h
- 参考类型: dns；容差为上游文档化决策（网格/格式耗散），不自报数值。

注意：采样/后处理 functionObject（probes、forces 等）必须按上方描述正确配置，
否则判分脚本将因找不到产物而判 0 分（它不会编造数值）。
