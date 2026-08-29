# cfdb validation — Natural Convection Cavity (Ra=1e4)

Classic de Vahl Davis (1983) differentially-heated square cavity benchmark, OpenFOAM buoyantSimpleFoam with Boussinesq equation of state (rho = rho0*(1-beta*(T-T0))), laminar, steady, Ra=1e4, Pr=0.71. Unit square H=1 m: hot wall x=0 at 293 K, cold wall x=1 at 283 K, adiabatic top/bottom; g=9.81 m/s2, beta=3e-3 1/K, rho0=1 kg/m3, mu=4.571e-3 Pa s => nu=4.571e-3, alpha=nu/Pr=6.437e-3, Ra=g*beta*dT*H^3/(nu*alpha)=1.0e4. Reference: de Vahl Davis (1983), Int. J. Numer. Methods Fluids 3:249-264, hot-wall average Nu=2.238 at Ra=1e4 (cross-checked against multiple independent published reproductions). QoI hot_wall_nu_avg = |q''|_avg * H / (k * dT), k=mu*Cp/Pr=6.437 W/(m K) => Nu = |q''|_avg / 64.37, from the wallHeatFlux functionObject on hotWall. Tolerance 10% reflects the coarse 64x64 demo mesh (documented domain decision, not a hidden fudge).

## 交付形式（严格遵守）
输出**单个 ```python 代码块**：脚本在当前工作目录创建 `case/` 子目录，
写入完整可运行的 OpenFOAM 算例（至少 `0/`、`constant/`、`system/`，含
`system/controlDict` 且其 `application` 条目声明所用求解器；需要 blockMesh
的算例写 `system/blockMeshDict`）。不要自行运行求解器——判分侧会在
OpenFOAM v2312 环境按案例声明的步骤（blockMesh → 求解器 → 后处理）真实执行，
然后用案例冻结的 QoI 脚本从算例产物提取指标并与留出参考值对账。

## 物理与工况
- flow=low_mach, turbulence=none, dim=2d, steady=True
- 工况: (见上)
- 评测 QoI（判分脚本从你的算例产物提取）: hot_wall_nu_avg
- 参考类型: dns；容差为上游文档化决策（网格/格式耗散），不自报数值。

注意：采样/后处理 functionObject（probes、forces 等）必须按上方描述正确配置，
否则判分脚本将因找不到产物而判 0 分（它不会编造数值）。
