# cfdb verification — Plane Channel Poiseuille Flow (Re_H=20)

Plane Poiseuille laminar channel flow verification, OpenFOAM icoFoam. Mean velocity U0=0.1 m/s, channel height H=0.01 m, length L=12H, nu=5e-5 m^2/s, Re_H=U0*H/nu=20. Uniform-velocity inlet; the probe line sits at x/H=10, well past the laminar hydrodynamic entrance length (L_e/Dh~0.05*Re_Dh, Re_Dh=40 -> L_e~2Dh=4H). Reference: closed-form fully developed profile u(y)=6*U0*(y/H)*(1-y/H) (u_max=1.5*U0), machine-generated pointwise by reference/generate_profile.py. QoI centerline_umax = max |Ux| (m/s) on the x/H=10 probe line; analytical value 0.15. Tolerance 5% covers the 240x20 demo mesh resolution plus residual entrance/transient effects (documented domain decision, not a hidden fudge); a full docker run (ESI v2312, t=5 s, 2026-08-11) measured u_max=0.149254 m/s (0.50% low), max pointwise profile error 2.05%.

## 要求
- 求解器族: OpenFOAM（上游基准使用 ESI v2312 语义）；从零搭建完整可运行案例（0/ constant/ system/ + Allrun），真实求解到 case 指定的终止时刻。
- 物理设定: flow=incompressible, turbulence=none, dim=2d, steady=False
- 工况: reynolds=20.0
- 输出 QoI: centerline_umax
- 参考类型: analytical（容差见任务 YAML reference.tolerances；判分用冻结 QoI 脚本）

## 交付
写 result.json，字段为上述 QoI 名（数值，与 QoI 定义单位一致）。
