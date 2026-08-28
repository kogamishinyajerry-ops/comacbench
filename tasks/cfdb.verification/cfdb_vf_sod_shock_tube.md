# cfdb verification — Sod Shock Tube (rhoCentralFoam)

Sod (1978) shock tube, inviscid compressible Euler equations, OpenFOAM rhoCentralFoam (ESI v2312). Effectively 1D tube x in [0,1] m (mesh 1000x1x1, empty patches), diaphragm at x=0.5, gamma=1.4 exactly (Cp=3.5*R, R=RR/28.96=287.10187 J/kg/K). Left state (p,rho)=(1 Pa, 1 kg/m3), right state (0.1 Pa, 0.125 kg/m3) imposed via T=p/(R*rho) in setFields. Reference: exact Riemann solution generated pointwise by the frozen script generate_reference.py (Newton iteration for p*, no hand-typed numbers); cross-checked against the universally tabulated Sod values (p*=0.30313, u*=0.92745, rho*_L=0.42632). QoI at t=0.2 s: shock_x_t02 (exact 0.85043115) and rho_plateau_t02 (exact star-region density 0.42631943 at probe x=0.6). Tolerances 2%/5% reflect the 1000-cell demo mesh and vanLeer shock-capturing smearing (documented domain decision, not a hidden fudge).

## 要求
- 求解器族: OpenFOAM（上游基准使用 ESI v2312 语义）；从零搭建完整可运行案例（0/ constant/ system/ + Allrun），真实求解到 case 指定的终止时刻。
- 物理设定: flow=compressible, turbulence=none, dim=2d, steady=False
- 工况: 
- 输出 QoI: shock_x_t02, rho_plateau_t02
- 参考类型: analytical（容差见任务 YAML reference.tolerances；判分用冻结 QoI 脚本）

## 交付
写 result.json，字段为上述 QoI 名（数值，与 QoI 定义单位一致）。
