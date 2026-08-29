# cfdb verification — Taylor-Green Decaying Vortex (Re=100, icoFoam)

2D Taylor-Green decaying vortex, OpenFOAM icoFoam, doubly periodic domain [0, 2*pi]^2, 64x64x1 demo mesh. Analytic reference (Taylor & Green 1937): u = U0 sin(kx) cos(ky) exp(-2 nu k^2 t), v = -U0 cos(kx) sin(ky) exp(-2 nu k^2 t), with U0 = 1 m/s, k = 1 1/m, nu = 0.01 m^2/s (Re = U0/(k nu) = 100), endTime t = 5 s. Reference CSVs are computed point-by-point from these formulas by reference/generate.py (kept in the case; no hand-typed numbers). QoIs: ke_ratio_end = KE(5)/KE(0) (analytic exp(-0.2) = 0.8187307530779818) and u_line_l2_rel_end = relative L2 error of (u, v) along the t = 5 sample line (mesh row j = 5) vs the analytic field (zero-reference QoI gated by absolute tolerance). Tolerances (5%) reflect the coarse 64x64 demo mesh — a documented domain decision in the same spirit as lid_driven_cavity, not a hidden fudge. Measured on this exact setup with ESI v2312 (2026-08-11, see provenance.yaml): ke_ratio_end = 0.81199 (0.82% error), u_line_l2_rel_end = 0.0043.

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
- 评测 QoI（判分脚本从你的算例产物提取）: ke_ratio_end, u_line_l2_rel_end
- 参考类型: analytical；容差为上游文档化决策（网格/格式耗散），不自报数值。

注意：采样/后处理 functionObject（probes、forces 等）必须按上方描述正确配置，
否则判分脚本将因找不到产物而判 0 分（它不会编造数值）。
