# cfdb validation — Lid-Driven Cavity (Re=100)

Classic lid-driven cavity benchmark, OpenFOAM icoFoam, laminar Re=100 (L=0.1 m, U_lid=1 m/s, nu=1e-3). Reference: Ghia, Ghia & Shin (1982), J. Comput. Phys. 48, Table I Re=100 column. QoI centerline_umax = max |U|/U_lid on the vertical centerline probe line (y/H up to 0.95): interpolated Ghia value 0.665 at y/H=0.95. Tolerance 10% reflects the coarse 32x32 demo mesh (documented domain decision, not a hidden fudge).

## 要求
- 求解器族: OpenFOAM（上游基准使用 ESI v2312 语义）；从零搭建完整可运行案例（0/ constant/ system/ + Allrun），真实求解到 case 指定的终止时刻。
- 物理设定: flow=incompressible, turbulence=none, dim=2d, steady=False
- 工况: reynolds=100.0
- 输出 QoI: centerline_umax
- 参考类型: dns（容差见任务 YAML reference.tolerances；判分用冻结 QoI 脚本）

## 交付
写 result.json，字段为上述 QoI 名（数值，与 QoI 定义单位一致）。
