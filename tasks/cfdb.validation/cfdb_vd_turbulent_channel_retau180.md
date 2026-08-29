# cfdb validation — Turbulent Channel Flow Re_tau=180 (MKM1999 DNS Validation)

Fully developed turbulent plane channel flow at Re_tau = 180, steady RANS with OpenFOAM simpleFoam + kOmegaSST (low-Re wall treatment, first cell center y+ ~ 1). Full channel (half-height h = 1 m), cyclic in streamwise (x, Lx = 2*pi*h) and spanwise (z, Lz = pi*h), no-slip walls at y = 0 and y = 2h. Constant-flow-rate forcing (meanVelocityForce, Ubar = 1 m/s) fixes Re_b = U_b*h/nu = 2800, the bulk Reynolds number of the Moser, Kim & Mansour (1999) DNS (Phys. Fluids 11(4), 943-945; the DNS file header reports the exact Re_tau = 178.12). Reference: official MKM DNS statistics (turbulence.oden.utexas.edu, file chan180.means), frozen as reference/chan180.means and machine-transformed into reference/uplus_yplus.csv by generate_reference.py (no hand-edited digits). QoI cf_bulk = tau_w/(0.5*rho*U_b^2); published DNS value Cf = 8.18e-3 (consistent with Re_b = 2800 and Re_tau = 180 via Cf = 2*(u_tau/U_b)^2; trapezoidal integration of the frozen DNS profile by generate_reference.py gives 8.136e-3, 0.5% lower, difference attributed to quadrature on the 65-station tabulated profile). Demo mesh 8 x 64 x 4 = 2048 cells; the 10% QoI tolerance reflects this demo mesh resolution plus RANS model-form error at low Re_tau (documented domain decision, not a hidden fudge).

## 交付形式（严格遵守）
输出**单个 ```python 代码块**：脚本在当前工作目录创建 `case/` 子目录，
写入完整可运行的 OpenFOAM 算例（至少 `0/`、`constant/`、`system/`，含
`system/controlDict` 且其 `application` 条目声明所用求解器；需要 blockMesh
的算例写 `system/blockMeshDict`）。不要自行运行求解器——判分侧会在
OpenFOAM v2312 环境按案例声明的步骤（blockMesh → 求解器 → 后处理）真实执行，
然后用案例冻结的 QoI 脚本从算例产物提取指标并与留出参考值对账。

## 物理与工况
- flow=rans, turbulence=rans_kwsst, dim=3d, steady=True
- 工况: reynolds=180.0
- 评测 QoI（判分脚本从你的算例产物提取）: cf_bulk
- 参考类型: dns；容差为上游文档化决策（网格/格式耗散），不自报数值。

注意：采样/后处理 functionObject（probes、forces 等）必须按上方描述正确配置，
否则判分脚本将因找不到产物而判 0 分（它不会编造数值）。
