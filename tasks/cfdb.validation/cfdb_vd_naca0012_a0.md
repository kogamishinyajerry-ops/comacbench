# cfdb validation — NACA0012 Airfoil α=0° (Ladson 1988 Validation)

Classic external aerodynamics validation case. NACA0012 symmetric airfoil at angle of attack α=0°, Re=6e6, M=0.3 (low Mach, RANS). OpenFOAM (simpleFoam + SA turbulence) and SU2 (RANS-SA) solvers compared against Ladson 1988 experimental Cp distribution (NASA TM-4074).

## 要求
- 求解器族: OpenFOAM（上游基准使用 ESI v2312 语义）；从零搭建完整可运行案例（0/ constant/ system/ + Allrun），真实求解到 case 指定的终止时刻。
- 物理设定: flow=rans, turbulence=rans_sa, dim=2d, steady=True
- 工况: reynolds=6.0e6, mach=0.3, alpha_deg=0.0
- 输出 QoI: cl, cd
- 参考类型: experimental（容差见任务 YAML reference.tolerances；判分用冻结 QoI 脚本）

## 交付
写 result.json，字段为上述 QoI 名（数值，与 QoI 定义单位一致）。
