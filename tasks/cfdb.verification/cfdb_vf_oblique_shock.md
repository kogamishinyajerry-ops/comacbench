# cfdb verification — Oblique Shock over a 10° Wedge (M1=2)

Supersonic inviscid flow over a 10° wedge, M1=2, OpenFOAM rhoCentralFoam (transient density-based solver run to its steady long-time limit, ~4 flow-throughs). Reference: exact theta-beta-M weak solution computed by gen_reference.py (beta=39.31384°, M2=1.640526, p2/p1=1.706580; no hand-copied numbers). Gas is the normalised gamma=1.4 gas of the rhoCentralFoam wedge15Ma5 tutorial (T1=1, p1=1, U1=2 => a1≈1). QoI post_shock_mach = |U|/sqrt(gamma*R*T) at the post-shock probe (0.6, 0.15), which sits between the wedge surface (y=0.0705) and the analytical shock (y=0.3276) at x=0.6. Tolerance 5% reflects the coarse 12500-cell demo mesh (shock smeared over a few cells; documented domain decision, not a hidden fudge).

## 要求
- 求解器族: OpenFOAM（上游基准使用 ESI v2312 语义）；从零搭建完整可运行案例（0/ constant/ system/ + Allrun），真实求解到 case 指定的终止时刻。
- 物理设定: flow=compressible, turbulence=none, dim=2d, steady=True
- 工况: mach=2.0
- 输出 QoI: post_shock_mach
- 参考类型: analytical（容差见任务 YAML reference.tolerances；判分用冻结 QoI 脚本）

## 交付
写 result.json，字段为上述 QoI 名（数值，与 QoI 定义单位一致）。
