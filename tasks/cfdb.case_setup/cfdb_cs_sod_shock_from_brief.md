# cfdb case_setup (evidence) — Case Setup: Sod Shock Tube from Engineering Brief (evidence mode)

case_setup domain EVIDENCE-mode task: the agent receives only a natural-language engineering brief (visible/task.md) and an annotated dimensioned drawing (visible/drawing.png), drives an ARBITRARY solver in its own environment (the judge has NO solver), and submits an evidence bundle (manifest.json + raw solver log + mesh report + density-profile CSV at t = 0.2 s). The judge validates the bundle and the frozen QoI script reference/compute_qoi.py reduces shock_x_t02 (shock position = midpoint of the sample pair with the largest density jump) and rho_plateau_t02 (density at the star-region probe x = 0.6) on the host. Task physics: Sod (1978) shock tube, inviscid compressible Euler, 1D tube x in [0, 1] m, diaphragm at x = 0.5, gamma = 1.4 exactly, left state (p, rho) = (1 Pa, 1 kg/m^3), right state (0.1 Pa, 0.125 kg/m^3), both at rest. Held-out reference QoI = exact Riemann solution at t = 0.2 s (shock at 0.8504311464060357, star-region density 0.4263194281784952). Golden measurement inherited from the VERIFIED case cases/verification/sod_shock_tube (2026-08-11 docker run measured shock_x_t02 = 0.85, rho_plateau_t02 = 0.42631711); see provenance.yaml.

## 交付形式（evidence 证据包，严格遵守）
输出**单个 ```python 代码块**：脚本在当前工作目录创建证据包文件：
- manifest.json
- evidence/solver.log
- evidence/mesh_report.txt
- evidence/samples/density_profile.csv

证据包必须来自你在自己的求解器环境中**真实求解**的产物（判分侧不运行求解器，
将用案例冻结的 QoI 脚本从证据包原始数据降算指标并与留出参考值对账；
自报最终数值不进入判分，格式不符判 0）。
