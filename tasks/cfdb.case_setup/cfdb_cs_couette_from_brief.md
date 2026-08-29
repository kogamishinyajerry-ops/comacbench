# cfdb case_setup (evidence) — Case Setup: Planar Couette Flow from Engineering Brief (evidence mode)

case_setup domain EVIDENCE-mode task: the agent receives only a natural-language engineering brief (visible/task.md) and an annotated dimensioned drawing (visible/drawing.png), then drives ANY CFD solver in its own environment (Fluent, STAR-CCM+, in-house code, OpenFOAM, ... — the judge runs NO solver at all) and submits an evidence bundle (manifest.json + solver-native log + mesh report + sampled profile). The judge validates the bundle (required files, manifest shape, generic CSV consistency) and recomputes the QoI from the raw evidence with the frozen script reference/compute_qoi.py on the host; a self-reported final QoI never enters the verdict. Task physics: planar Couette flow, gap H=0.01 m, top wall U_lid=0.1 m/s, nu=5e-5 m^2/s (Re_H=20), transient laminar from rest to the steady linear profile u(y)=U_lid*y/H. QoI bottom_wall_shear_normalized = (du/dy at the stationary wall)/(U_lid/H), held-out reference 1.0 (exact). Golden evidence is reduced from the verified docker run of cases/verification/couette_shear (measured QoI 1.00000000, rel err 0.0); see provenance.yaml.

## 交付形式（evidence 证据包，严格遵守）
输出**单个 ```python 代码块**：脚本在当前工作目录创建证据包文件：
- manifest.json
- evidence/solver.log
- evidence/mesh_report.txt
- evidence/samples/profile.csv

证据包必须来自你在自己的求解器环境中**真实求解**的产物（判分侧不运行求解器，
将用案例冻结的 QoI 脚本从证据包原始数据降算指标并与留出参考值对账；
自报最终数值不进入判分，格式不符判 0）。
