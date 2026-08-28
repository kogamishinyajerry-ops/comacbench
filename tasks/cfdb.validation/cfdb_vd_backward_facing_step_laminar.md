# cfdb validation — Backward-Facing Step (Laminar, Re=100)

Classic laminar backward-facing step benchmark (expansion ratio ER=2), OpenFOAM simpleFoam laminar (steady SIMPLE). Step height h=0.01 m, mean inlet velocity Um=1 m/s with a fully developed parabolic inlet profile, nu=2e-4 -> Re = Um*D_h/nu = 100 (D_h = 2*inlet channel height, the Armaly et al. 1983 / Erturk 2008 convention). Demo mesh 6100 cells (3 conformal hex blocks, inlet channel 5h, downstream 30h). QoI reattachment_x_over_h = primary reattachment length x_r/h, located by the Ux sign change on a near-bottom sample line (first-cell-centre height). Reference: Erturk (2008) Comput. Fluids 37:633-655, x_r/h = 2.922 at Re=100. A real run of the shipped case on opencfd/openfoam-default:2312 (2026-08-11, SIMPLE converged in 459 iterations) gave x_r/h = 2.8715 (1.73% error). Tolerance 10% reflects the coarse demo mesh (documented domain decision, not a hidden fudge).

## 要求
- 求解器族: OpenFOAM（上游基准使用 ESI v2312 语义）；从零搭建完整可运行案例（0/ constant/ system/ + Allrun），真实求解到 case 指定的终止时刻。
- 物理设定: flow=incompressible, turbulence=none, dim=2d, steady=True
- 工况: reynolds=100.0
- 输出 QoI: reattachment_x_over_h
- 参考类型: dns（容差见任务 YAML reference.tolerances；判分用冻结 QoI 脚本）

## 交付
写 result.json，字段为上述 QoI 名（数值，与 QoI 定义单位一致）。
