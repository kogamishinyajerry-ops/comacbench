# cfdb verification — Taylor-Green Decaying Vortex (Re=100, icoFoam)

2D Taylor-Green decaying vortex, OpenFOAM icoFoam, doubly periodic domain [0, 2*pi]^2, 64x64x1 demo mesh. Analytic reference (Taylor & Green 1937): u = U0 sin(kx) cos(ky) exp(-2 nu k^2 t), v = -U0 cos(kx) sin(ky) exp(-2 nu k^2 t), with U0 = 1 m/s, k = 1 1/m, nu = 0.01 m^2/s (Re = U0/(k nu) = 100), endTime t = 5 s. Reference CSVs are computed point-by-point from these formulas by reference/generate.py (kept in the case; no hand-typed numbers). QoIs: ke_ratio_end = KE(5)/KE(0) (analytic exp(-0.2) = 0.8187307530779818) and u_line_l2_rel_end = relative L2 error of (u, v) along the t = 5 sample line (mesh row j = 5) vs the analytic field (zero-reference QoI gated by absolute tolerance). Tolerances (5%) reflect the coarse 64x64 demo mesh — a documented domain decision in the same spirit as lid_driven_cavity, not a hidden fudge. Measured on this exact setup with ESI v2312 (2026-08-11, see provenance.yaml): ke_ratio_end = 0.81199 (0.82% error), u_line_l2_rel_end = 0.0043.

## 要求
- 求解器族: OpenFOAM（上游基准使用 ESI v2312 语义）；从零搭建完整可运行案例（0/ constant/ system/ + Allrun），真实求解到 case 指定的终止时刻。
- 物理设定: flow=incompressible, turbulence=none, dim=2d, steady=False
- 工况: reynolds=100.0
- 输出 QoI: ke_ratio_end, u_line_l2_rel_end
- 参考类型: analytical（容差见任务 YAML reference.tolerances；判分用冻结 QoI 脚本）

## 交付
写 result.json，字段为上述 QoI 名（数值，与 QoI 定义单位一致）。
