# cfdb validation — Turbulent Channel Flow Re_tau=180 (MKM1999 DNS Validation)

Fully developed turbulent plane channel flow at Re_tau = 180, steady RANS with OpenFOAM simpleFoam + kOmegaSST (low-Re wall treatment, first cell center y+ ~ 1). Full channel (half-height h = 1 m), cyclic in streamwise (x, Lx = 2*pi*h) and spanwise (z, Lz = pi*h), no-slip walls at y = 0 and y = 2h. Constant-flow-rate forcing (meanVelocityForce, Ubar = 1 m/s) fixes Re_b = U_b*h/nu = 2800, the bulk Reynolds number of the Moser, Kim & Mansour (1999) DNS (Phys. Fluids 11(4), 943-945; the DNS file header reports the exact Re_tau = 178.12). Reference: official MKM DNS statistics (turbulence.oden.utexas.edu, file chan180.means), frozen as reference/chan180.means and machine-transformed into reference/uplus_yplus.csv by generate_reference.py (no hand-edited digits). QoI cf_bulk = tau_w/(0.5*rho*U_b^2); published DNS value Cf = 8.18e-3 (consistent with Re_b = 2800 and Re_tau = 180 via Cf = 2*(u_tau/U_b)^2; trapezoidal integration of the frozen DNS profile by generate_reference.py gives 8.136e-3, 0.5% lower, difference attributed to quadrature on the 65-station tabulated profile). Demo mesh 8 x 64 x 4 = 2048 cells; the 10% QoI tolerance reflects this demo mesh resolution plus RANS model-form error at low Re_tau (documented domain decision, not a hidden fudge).

## 要求
- 求解器族: OpenFOAM（上游基准使用 ESI v2312 语义）；从零搭建完整可运行案例（0/ constant/ system/ + Allrun），真实求解到 case 指定的终止时刻。
- 物理设定: flow=rans, turbulence=rans_kwsst, dim=3d, steady=True
- 工况: reynolds=180.0
- 输出 QoI: cf_bulk
- 参考类型: dns（容差见任务 YAML reference.tolerances；判分用冻结 QoI 脚本）

## 交付
写 result.json，字段为上述 QoI 名（数值，与 QoI 定义单位一致）。
