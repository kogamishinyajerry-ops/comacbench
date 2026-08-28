# cfdb verification — Flat Plate (SU2 Verification)

Flat plate laminar boundary layer verification case for SU2 solver. Reference: Blasius analytical solution.

## 要求
- 求解器族: OpenFOAM（上游基准使用 ESI v2312 语义）；从零搭建完整可运行案例（0/ constant/ system/ + Allrun），真实求解到 case 指定的终止时刻。
- 物理设定: flow=incompressible, turbulence=none, dim=2d, steady=True
- 工况: reynolds=200000.0, mach=0.3, alpha_deg=0.0
- 输出 QoI: skin_friction_coeff
- 参考类型: analytical（容差见任务 YAML reference.tolerances；判分用冻结 QoI 脚本）

## 交付
写 result.json，字段为上述 QoI 名（数值，与 QoI 定义单位一致）。
