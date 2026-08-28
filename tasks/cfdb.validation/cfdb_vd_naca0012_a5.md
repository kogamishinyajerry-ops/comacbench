# cfdb validation — NACA0012 Airfoil α=5° (Ladson 1988 Validation)

NACA0012 at α=5°, Re=6e6, M=0.3, RANS-SA. Part of alpha sweep (α=0/5/10/15°) for polar curve validation against Ladson 1988.

## 要求
- 求解器族: OpenFOAM（上游基准使用 ESI v2312 语义）；从零搭建完整可运行案例（0/ constant/ system/ + Allrun），真实求解到 case 指定的终止时刻。
- 物理设定: flow=rans, turbulence=rans_sa, dim=2d, steady=True
- 工况: reynolds=6.0e6, mach=0.3, alpha_deg=5.0
- 输出 QoI: cl, cd
- 参考类型: experimental（容差见任务 YAML reference.tolerances；判分用冻结 QoI 脚本）

## 交付
写 result.json，字段为上述 QoI 名（数值，与 QoI 定义单位一致）。
