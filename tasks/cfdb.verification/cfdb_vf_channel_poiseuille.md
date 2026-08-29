# cfdb verification — Plane Channel Poiseuille Flow (Re_H=20)

Plane Poiseuille laminar channel flow verification, OpenFOAM icoFoam. Mean velocity U0=0.1 m/s, channel height H=0.01 m, length L=12H, nu=5e-5 m^2/s, Re_H=U0*H/nu=20. Uniform-velocity inlet; the probe line sits at x/H=10, well past the laminar hydrodynamic entrance length (L_e/Dh~0.05*Re_Dh, Re_Dh=40 -> L_e~2Dh=4H). Reference: closed-form fully developed profile u(y)=6*U0*(y/H)*(1-y/H) (u_max=1.5*U0), machine-generated pointwise by reference/generate_profile.py. QoI centerline_umax = max |Ux| (m/s) on the x/H=10 probe line; analytical value 0.15. Tolerance 5% covers the 240x20 demo mesh resolution plus residual entrance/transient effects (documented domain decision, not a hidden fudge); a full docker run (ESI v2312, t=5 s, 2026-08-11) measured u_max=0.149254 m/s (0.50% low), max pointwise profile error 2.05%.

## 交付形式（严格遵守）
输出**单个 ```python 代码块**：脚本在当前工作目录创建 `case/` 子目录，
写入完整可运行的 OpenFOAM 算例（至少 `0/`、`constant/`、`system/`，含
`system/controlDict` 且其 `application` 条目声明所用求解器；需要 blockMesh
的算例写 `system/blockMeshDict`）。不要自行运行求解器——判分侧会在
OpenFOAM v2312 环境按案例声明的步骤（blockMesh → 求解器 → 后处理）真实执行，
然后用案例冻结的 QoI 脚本从算例产物提取指标并与留出参考值对账。

## 物理与工况
- flow=incompressible, turbulence=none, dim=2d, steady=False
- 工况: reynolds=20.0
- 评测 QoI（判分脚本从你的算例产物提取）: centerline_umax
- 参考类型: analytical；容差为上游文档化决策（网格/格式耗散），不自报数值。

注意：采样/后处理 functionObject（probes、forces 等）必须按上方描述正确配置，
否则判分脚本将因找不到产物而判 0 分（它不会编造数值）。
