# cfdb verification — Flat Plate Blasius (OpenFOAM Verification)

Laminar flat-plate boundary layer verification, pure OpenFOAM (simpleFoam, simulationType laminar, blockMesh with leading-edge refinement). Complements verification/flat_plate_su2 (SU2-mesh variant) with a self-contained OpenFOAM setup: U_inf=1 m/s, nu=1e-5 m^2/s so Re_x = 1e5*x[m]; measurement stations x=0.1..1.0 m span Re_x = 1e4..1e5, safely laminar (transition ~5e5). Reference: Blasius correlation Cf(x)=0.664/sqrt(Re_x), generated pointwise by generate_reference.py (no hand-typed numbers). QoIs are local Cf at x=0.2/0.5/0.8/1.0 m. Tolerance 15% reflects the demo mesh (10500 cells, ~20 cells in the BL at x=0.1) and the leading-edge/finite-domain discretization error on wall shear — a documented domain decision, not a hidden fudge.

## 要求
- 求解器族: OpenFOAM（上游基准使用 ESI v2312 语义）；从零搭建完整可运行案例（0/ constant/ system/ + Allrun），真实求解到 case 指定的终止时刻。
- 物理设定: flow=incompressible, turbulence=none, dim=2d, steady=True
- 工况: reynolds=100000.0
- 输出 QoI: cf_x020, cf_x050, cf_x080, cf_x100
- 参考类型: analytical（容差见任务 YAML reference.tolerances；判分用冻结 QoI 脚本）

## 交付
写 result.json，字段为上述 QoI 名（数值，与 QoI 定义单位一致）。
