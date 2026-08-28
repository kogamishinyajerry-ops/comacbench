# cfdb verification — Taylor-Couette Circular Couette (Laminar)

Laminar circular Couette flow between concentric cylinders (2D annular section, OpenFOAM icoFoam, ESI v2312). Inner cylinder R_i=0.05 m rotates at omega=1 rad/s (rotatingWallVelocity), outer cylinder R_o=0.10 m stationary, nu=1e-3 -> Re=omega*R_i*(R_o-R_i)/nu=2.5, deeply subcritical for Taylor vortices. Reference is the exact analytical profile u_theta(r)=A*r+B/r with A=-omega*R_i^2/(R_o^2-R_i^2), B=omega*R_i^2*R_o^2/(R_o^2-R_i^2), generated point-by-point by reference/generate.py (pure stdlib, BCs asserted to machine precision) — no hand-typed numbers. QoI utheta_midgap = u_theta at the mid-gap radius r=0.075 m; reference 0.0194444 m/s. Tolerance 2% is a documented domain decision: a full endTime=10 s run on the shipped 2880-cell demo mesh (docker opencfd/openfoam-default:2312, 2026-08-11) measured 0.17% QoI error and 0.18% max pointwise profile error, so 2% absorbs solver-version/platform variation while still biting on any genuinely wrong setup.

## 要求
- 求解器族: OpenFOAM（上游基准使用 ESI v2312 语义）；从零搭建完整可运行案例（0/ constant/ system/ + Allrun），真实求解到 case 指定的终止时刻。
- 物理设定: flow=incompressible, turbulence=none, dim=2d, steady=False
- 工况: reynolds=2.5
- 输出 QoI: utheta_midgap
- 参考类型: analytical（容差见任务 YAML reference.tolerances；判分用冻结 QoI 脚本）

## 交付
写 result.json，字段为上述 QoI 名（数值，与 QoI 定义单位一致）。
