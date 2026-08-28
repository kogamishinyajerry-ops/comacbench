# cfdb verification — Planar Couette Shear Flow (icoFoam)

Planar Couette flow between a stationary no-slip bottom wall and a top lid moving at U_lid=0.1 m/s (H=0.01 m, nu=5e-5 m^2/s, Re_H=20), OpenFOAM icoFoam, 4x40x1 channel mesh (streamwise cyclic, one cell in z with empty -> flow uniform in x, exactly 1D profile in y). Analytical steady state: u(y)=U_lid*y/H (linear), |tau_wall|=nu*U_lid/H=5e-4 m^2/s^2 on both walls. Reference CSV is generated point-by-point by reference/generate.py (anchored, deterministic; no hand-typed digits). QoI bottom_wall_shear_normalized = |tau_bottom|/(nu*U_lid/H) = 1.0 analytically, extracted from the sampled profile slope at the bottom wall. The 1% tolerance is a documented generous bound: the linear profile is exactly representable on ANY mesh, so mesh resolution is not the error source here — the tolerance absorbs transient time-integration residue and sampling/interpolation error only (documented domain decision, not a hidden fudge).

## 要求
- 求解器族: OpenFOAM（上游基准使用 ESI v2312 语义）；从零搭建完整可运行案例（0/ constant/ system/ + Allrun），真实求解到 case 指定的终止时刻。
- 物理设定: flow=incompressible, turbulence=none, dim=2d, steady=False
- 工况: reynolds=20.0
- 输出 QoI: bottom_wall_shear_normalized
- 参考类型: analytical（容差见任务 YAML reference.tolerances；判分用冻结 QoI 脚本）

## 交付
写 result.json，字段为上述 QoI 名（数值，与 QoI 定义单位一致）。
