# cfdb verification — Taylor-Couette Circular Couette (Laminar)

Laminar circular Couette flow between concentric cylinders (2D annular section, OpenFOAM icoFoam, ESI v2312). Inner cylinder R_i=0.05 m rotates at omega=1 rad/s (rotatingWallVelocity), outer cylinder R_o=0.10 m stationary, nu=1e-3 -> Re=omega*R_i*(R_o-R_i)/nu=2.5, deeply subcritical for Taylor vortices. Reference is the exact analytical profile u_theta(r)=A*r+B/r with A=-omega*R_i^2/(R_o^2-R_i^2), B=omega*R_i^2*R_o^2/(R_o^2-R_i^2), generated point-by-point by reference/generate.py (pure stdlib, BCs asserted to machine precision) — no hand-typed numbers. QoI utheta_midgap = u_theta at the mid-gap radius r=0.075 m; reference 0.0194444 m/s. Tolerance 2% is a documented domain decision: a full endTime=10 s run on the shipped 2880-cell demo mesh (docker opencfd/openfoam-default:2312, 2026-08-11) measured 0.17% QoI error and 0.18% max pointwise profile error, so 2% absorbs solver-version/platform variation while still biting on any genuinely wrong setup.

## 交付形式（严格遵守）
输出**单个 ```python 代码块**：脚本在当前工作目录创建 `case/` 子目录，
写入完整可运行的 OpenFOAM 算例（至少 `0/`、`constant/`、`system/`，含
`system/controlDict` 且其 `application` 条目声明所用求解器；需要 blockMesh
的算例写 `system/blockMeshDict`）。不要自行运行求解器——判分侧会在
OpenFOAM v2312 环境按案例声明的步骤（blockMesh → 求解器 → 后处理）真实执行，
然后用案例冻结的 QoI 脚本从算例产物提取指标并与留出参考值对账。

## 物理与工况
- flow=incompressible, turbulence=none, dim=2d, steady=False
- 工况: reynolds=2.5
- 评测 QoI（判分脚本从你的算例产物提取）: utheta_midgap
- 参考类型: analytical；容差为上游文档化决策（网格/格式耗散），不自报数值。

注意：采样/后处理 functionObject（probes、forces 等）必须按上方描述正确配置，
否则判分脚本将因找不到产物而判 0 分（它不会编造数值）。
