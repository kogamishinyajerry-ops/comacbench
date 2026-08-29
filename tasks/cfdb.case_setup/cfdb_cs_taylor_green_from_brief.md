# cfdb case_setup (evidence) — Case Setup: Taylor-Green Decaying Vortex from Engineering Brief (evidence mode)

case_setup domain EVIDENCE-mode task: the agent receives only a natural-language engineering brief (visible/task.md) and an annotated dimensioned drawing (visible/drawing.png), drives an ARBITRARY solver in its own environment (the judge has NO solver), and submits an evidence bundle (manifest.json + raw solver log + mesh report + kinetic-energy history CSV + final-time sample-line CSV). The judge validates the bundle and the frozen QoI script reference/compute_qoi.py reduces ke_ratio_end (KE(t=5)/KE(t=0), KE = domain mean of 0.5*|u|^2) and u_line_l2_rel_end (relative L2 error of (u, v) along the t=5 sample line at y = 11*pi/64 vs the frozen analytic field) on the host. Task physics: 2D Taylor-Green decaying vortex, doubly periodic [0, 2*pi]^2, U0 = 1 m/s, k = 1 1/m, nu = 0.01 m^2/s (Re = 100), incompressible laminar, t in [0, 5] s. Held-out reference QoI = analytical exp(-0.2) = 0.8187307530779818 and 0.0 (Taylor & Green 1937). Golden measurement inherited from the VERIFIED case cases/verification/taylor_green_vortex (2026-08-11 docker run measured ke_ratio_end = 0.8119854701224898, u_line_l2_rel_end = 0.004340225467502078); see provenance.yaml.

## 交付形式（evidence 证据包，严格遵守）
输出**单个 ```python 代码块**：脚本在当前工作目录创建证据包文件：
- manifest.json
- evidence/solver.log
- evidence/mesh_report.txt
- evidence/samples/ke_history.csv
- evidence/samples/line_end.csv

证据包必须来自你在自己的求解器环境中**真实求解**的产物（判分侧不运行求解器，
将用案例冻结的 QoI 脚本从证据包原始数据降算指标并与留出参考值对账；
自报最终数值不进入判分，格式不符判 0）。
