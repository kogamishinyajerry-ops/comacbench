# cfdb case_setup (evidence) — Case Setup: Taylor-Couette Circular Couette from Engineering Brief (evidence mode)

case_setup domain EVIDENCE-mode task: the agent receives only a natural-language engineering brief (visible/task.md) and an annotated dimensioned drawing (visible/drawing.png), then drives ANY CFD solver in its own environment (Fluent, STAR-CCM+, in-house code, OpenFOAM, ... — the judge runs NO solver at all) and submits an evidence bundle (manifest.json + solver-native log + mesh report + sampled radial profile). The judge validates the bundle (required files, manifest shape, generic CSV consistency) and recomputes the QoI from the raw evidence with the frozen script reference/compute_qoi.py on the host; a self-reported final QoI never enters the verdict. Task physics: laminar circular Couette flow between concentric cylinders, R_i=0.05 m rotating at omega=1 rad/s, R_o=0.10 m stationary, nu=1e-3 m^2/s (Re=2.5, deeply subcritical for Taylor vortices), transient laminar to the steady profile u_theta(r)=A*r+B/r. QoI utheta_midgap = u_theta at the mid-gap radius r=0.075 m; held-out reference 0.01944444444444445 m/s (exact closed-form value, the SAME number the verified source case anchors). Golden evidence is reduced from the verified docker run of cases/verification/taylor_couette (measured 0.01941113, 0.17%); see provenance.yaml.

## 交付形式（evidence 证据包，严格遵守）
输出**单个 ```python 代码块**：脚本在当前工作目录创建证据包文件：
- manifest.json
- evidence/solver.log
- evidence/mesh_report.txt
- evidence/samples/profile.csv

证据包必须来自你在自己的求解器环境中**真实求解**的产物（判分侧不运行求解器，
将用案例冻结的 QoI 脚本从证据包原始数据降算指标并与留出参考值对账；
自报最终数值不进入判分，格式不符判 0）。
