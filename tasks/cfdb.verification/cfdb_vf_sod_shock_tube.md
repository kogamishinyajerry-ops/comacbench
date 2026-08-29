# cfdb verification — Sod Shock Tube (rhoCentralFoam)

Sod (1978) shock tube, inviscid compressible Euler equations, OpenFOAM rhoCentralFoam (ESI v2312). Effectively 1D tube x in [0,1] m (mesh 1000x1x1, empty patches), diaphragm at x=0.5, gamma=1.4 exactly (Cp=3.5*R, R=RR/28.96=287.10187 J/kg/K). Left state (p,rho)=(1 Pa, 1 kg/m3), right state (0.1 Pa, 0.125 kg/m3) imposed via T=p/(R*rho) in setFields. Reference: exact Riemann solution generated pointwise by the frozen script generate_reference.py (Newton iteration for p*, no hand-typed numbers); cross-checked against the universally tabulated Sod values (p*=0.30313, u*=0.92745, rho*_L=0.42632). QoI at t=0.2 s: shock_x_t02 (exact 0.85043115) and rho_plateau_t02 (exact star-region density 0.42631943 at probe x=0.6). Tolerances 2%/5% reflect the 1000-cell demo mesh and vanLeer shock-capturing smearing (documented domain decision, not a hidden fudge).

## 交付形式（严格遵守）
输出**单个 ```python 代码块**：脚本在当前工作目录创建 `case/` 子目录，
写入完整可运行的 OpenFOAM 算例（至少 `0/`、`constant/`、`system/`，含
`system/controlDict` 且其 `application` 条目声明所用求解器；需要 blockMesh
的算例写 `system/blockMeshDict`）。不要自行运行求解器——判分侧会在
OpenFOAM v2312 环境按案例声明的步骤（blockMesh → 求解器 → 后处理）真实执行，
然后用案例冻结的 QoI 脚本从算例产物提取指标并与留出参考值对账。

## 物理与工况
- flow=compressible, turbulence=none, dim=2d, steady=False
- 工况: (见上)
- 评测 QoI（判分脚本从你的算例产物提取）: shock_x_t02, rho_plateau_t02
- 参考类型: analytical；容差为上游文档化决策（网格/格式耗散），不自报数值。

注意：采样/后处理 functionObject（probes、forces 等）必须按上方描述正确配置，
否则判分脚本将因找不到产物而判 0 分（它不会编造数值）。
