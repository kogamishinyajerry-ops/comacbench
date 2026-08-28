# cfdb validation — Natural Convection Cavity (Ra=1e4)

Classic de Vahl Davis (1983) differentially-heated square cavity benchmark, OpenFOAM buoyantSimpleFoam with Boussinesq equation of state (rho = rho0*(1-beta*(T-T0))), laminar, steady, Ra=1e4, Pr=0.71. Unit square H=1 m: hot wall x=0 at 293 K, cold wall x=1 at 283 K, adiabatic top/bottom; g=9.81 m/s2, beta=3e-3 1/K, rho0=1 kg/m3, mu=4.571e-3 Pa s => nu=4.571e-3, alpha=nu/Pr=6.437e-3, Ra=g*beta*dT*H^3/(nu*alpha)=1.0e4. Reference: de Vahl Davis (1983), Int. J. Numer. Methods Fluids 3:249-264, hot-wall average Nu=2.238 at Ra=1e4 (cross-checked against multiple independent published reproductions). QoI hot_wall_nu_avg = |q''|_avg * H / (k * dT), k=mu*Cp/Pr=6.437 W/(m K) => Nu = |q''|_avg / 64.37, from the wallHeatFlux functionObject on hotWall. Tolerance 10% reflects the coarse 64x64 demo mesh (documented domain decision, not a hidden fudge).

## 要求
- 求解器族: OpenFOAM（上游基准使用 ESI v2312 语义）；从零搭建完整可运行案例（0/ constant/ system/ + Allrun），真实求解到 case 指定的终止时刻。
- 物理设定: flow=low_mach, turbulence=none, dim=2d, steady=True
- 工况: 
- 输出 QoI: hot_wall_nu_avg
- 参考类型: dns（容差见任务 YAML reference.tolerances；判分用冻结 QoI 脚本）

## 交付
写 result.json，字段为上述 QoI 名（数值，与 QoI 定义单位一致）。
