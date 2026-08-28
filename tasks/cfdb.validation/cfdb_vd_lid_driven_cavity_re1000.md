# cfdb validation — Lid-Driven Cavity (Re=1000)

Classic lid-driven cavity benchmark, OpenFOAM icoFoam, laminar Re=1000 (L=0.1 m, U_lid=1 m/s, nu=1e-4). Reference: Ghia, Ghia & Shin (1982), J. Comput. Phys. 48, Table I Re=1000 column. QoI centerline_umax = max |U|/U_lid on the vertical centerline probe line (y/H up to 0.95): linear interpolation of the Ghia table between y/H=0.8516 (0.33304) and y/H=0.9531 (0.46604) gives 0.462 at y/H=0.95. Tolerance 10% is a documented domain decision, not a hidden fudge: it covers (a) the reference being a linear interpolation at the probe-line top rather than a tabulated point, (b) the QoI measuring |U|=sqrt(u^2+v^2) while the reference tabulates u only, (c) the uniform 128x128 mesh vs Ghia's 129x129 multigrid solution, and (d) the finite integration time t=30 s (300 lid turnovers) vs the true steady state.

## 要求
- 求解器族: OpenFOAM（上游基准使用 ESI v2312 语义）；从零搭建完整可运行案例（0/ constant/ system/ + Allrun），真实求解到 case 指定的终止时刻。
- 物理设定: flow=incompressible, turbulence=none, dim=2d, steady=False
- 工况: reynolds=1000.0
- 输出 QoI: centerline_umax
- 参考类型: dns（容差见任务 YAML reference.tolerances；判分用冻结 QoI 脚本）

## 交付
写 result.json，字段为上述 QoI 名（数值，与 QoI 定义单位一致）。
