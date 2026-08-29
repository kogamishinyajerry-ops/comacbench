# cfdb verification — Planar Couette Shear Flow (icoFoam)

Planar Couette flow between a stationary no-slip bottom wall and a top lid moving at U_lid=0.1 m/s (H=0.01 m, nu=5e-5 m^2/s, Re_H=20), OpenFOAM icoFoam, 4x40x1 channel mesh (streamwise cyclic, one cell in z with empty -> flow uniform in x, exactly 1D profile in y). Analytical steady state: u(y)=U_lid*y/H (linear), |tau_wall|=nu*U_lid/H=5e-4 m^2/s^2 on both walls. Reference CSV is generated point-by-point by reference/generate.py (anchored, deterministic; no hand-typed digits). QoI bottom_wall_shear_normalized = |tau_bottom|/(nu*U_lid/H) = 1.0 analytically, extracted from the sampled profile slope at the bottom wall. The 1% tolerance is a documented generous bound: the linear profile is exactly representable on ANY mesh, so mesh resolution is not the error source here — the tolerance absorbs transient time-integration residue and sampling/interpolation error only (documented domain decision, not a hidden fudge).

## 交付形式（严格遵守）
输出**单个 ```python 代码块**：脚本在当前工作目录创建 `case/` 子目录，
写入完整可运行的 OpenFOAM 算例（至少 `0/`、`constant/`、`system/`，含
`system/controlDict` 且其 `application` 条目声明所用求解器；需要 blockMesh
的算例写 `system/blockMeshDict`）。不要自行运行求解器——判分侧会在
OpenFOAM v2312 环境按案例声明的步骤（blockMesh → 求解器 → 后处理）真实执行，
然后用案例冻结的 QoI 脚本从算例产物提取指标并与留出参考值对账。

## 物理与工况
- flow=incompressible, turbulence=none, dim=2d, steady=False
- 工况: reynolds=20.0
- 评测 QoI（判分脚本从你的算例产物提取）: bottom_wall_shear_normalized
- 参考类型: analytical；容差为上游文档化决策（网格/格式耗散），不自报数值。

注意：采样/后处理 functionObject（probes、forces 等）必须按上方描述正确配置，
否则判分脚本将因找不到产物而判 0 分（它不会编造数值）。
