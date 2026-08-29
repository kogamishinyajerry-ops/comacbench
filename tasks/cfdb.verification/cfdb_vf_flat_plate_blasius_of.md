# cfdb verification — Flat Plate Blasius (OpenFOAM Verification)

Laminar flat-plate boundary layer verification, pure OpenFOAM (simpleFoam, simulationType laminar, blockMesh with leading-edge refinement). Complements verification/flat_plate_su2 (SU2-mesh variant) with a self-contained OpenFOAM setup: U_inf=1 m/s, nu=1e-5 m^2/s so Re_x = 1e5*x[m]; measurement stations x=0.1..1.0 m span Re_x = 1e4..1e5, safely laminar (transition ~5e5). Reference: Blasius correlation Cf(x)=0.664/sqrt(Re_x), generated pointwise by generate_reference.py (no hand-typed numbers). QoIs are local Cf at x=0.2/0.5/0.8/1.0 m. Tolerance 15% reflects the demo mesh (10500 cells, ~20 cells in the BL at x=0.1) and the leading-edge/finite-domain discretization error on wall shear — a documented domain decision, not a hidden fudge.

## 交付形式（严格遵守）
输出**单个 ```python 代码块**：脚本在当前工作目录创建 `case/` 子目录，
写入完整可运行的 OpenFOAM 算例（至少 `0/`、`constant/`、`system/`，含
`system/controlDict` 且其 `application` 条目声明所用求解器；需要 blockMesh
的算例写 `system/blockMeshDict`）。不要自行运行求解器——判分侧会在
OpenFOAM v2312 环境按案例声明的步骤（blockMesh → 求解器 → 后处理）真实执行，
然后用案例冻结的 QoI 脚本从算例产物提取指标并与留出参考值对账。

## 物理与工况
- flow=incompressible, turbulence=none, dim=2d, steady=True
- 工况: reynolds=100000.0
- 评测 QoI（判分脚本从你的算例产物提取）: cf_x020, cf_x050, cf_x080, cf_x100
- 参考类型: analytical；容差为上游文档化决策（网格/格式耗散），不自报数值。

注意：采样/后处理 functionObject（probes、forces 等）必须按上方描述正确配置，
否则判分脚本将因找不到产物而判 0 分（它不会编造数值）。
