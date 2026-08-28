# cfdb verification — 1D Steady Heat Conduction with Uniform Heat Source (laplacianFoam)

Lightest-weight verification case: 1D steady heat conduction in a plane wall (L=1 m, 100x1x1 cells), OpenFOAM laplacianFoam, both faces fixedValue T=300 K, uniform volumetric source S=100 K/s (fvOptions scalarSemiImplicitSource, volumeMode specific), DT=alpha=0.1 m^2/s. Reference: closed-form parabola T(x)=300+500*x*(1-x) K (q/k=S/alpha=1000 K/m^2; Incropera & DeWitt plane wall with generation), evaluated point-by-point by reference/generate.py into reference/t_profile.csv. QoI midplane_T = T(L/2) = 425.0 K. Tolerance 1% is a documented domain decision: a v2312 smoke run of this exact case (2026-08-11, opencfd/openfoam-default:2312) showed max profile deviation 0.0125 K and interpolated midplane error 2.7e-7 relative (limited by the transient tail), so 1% is deliberately loose to absorb coarser meshes and shorter endTime variants — not a hidden fudge.

## 要求
- 求解器族: OpenFOAM（上游基准使用 ESI v2312 语义）；从零搭建完整可运行案例（0/ constant/ system/ + Allrun），真实求解到 case 指定的终止时刻。
- 物理设定: flow=None, turbulence=None, dim=None, steady=None
- 工况: 
- 输出 QoI: midplane_T
- 参考类型: analytical（容差见任务 YAML reference.tolerances；判分用冻结 QoI 脚本）

## 交付
写 result.json，字段为上述 QoI 名（数值，与 QoI 定义单位一致）。
