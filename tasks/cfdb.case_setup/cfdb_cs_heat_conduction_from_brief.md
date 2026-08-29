# cfdb case_setup (evidence) — Case Setup: 1D Solid Conduction with Heat Source from Engineering Brief (evidence mode)

case_setup domain EVIDENCE-mode task: the agent receives only a natural-language engineering brief (visible/task.md) and an annotated dimensioned drawing (visible/drawing.png), drives an ARBITRARY solver in its own environment (Fluent / STAR-CCM+ / in-house / OpenFOAM — the judge has NO solver), and submits an evidence bundle (manifest.json + raw solver log + mesh report + steady-state temperature profile CSV). The judge validates the bundle and the frozen QoI script reference/compute_qoi.py reduces midplane_T (T at x = L/2, linearly interpolated from the submitted profile) on the host. Task physics: plane solid wall L = 1 m, both faces held at T = 300 K, uniform volumetric heat source with q'''/k = 1000 K/m^2, thermal diffusivity alpha = 0.1 m^2/s, transient to steady state. Held-out reference QoI = analytical midplane T(L/2) = 425.0 K (Incropera & DeWitt plane wall with generation). Golden measurement inherited from the VERIFIED case cases/verification/heat_conduction_1d (2026-08-11 docker run measured midplane_T = 424.9998849 K, 2.7e-7 relative); see provenance.yaml.

## 交付形式（evidence 证据包，严格遵守）
输出**单个 ```python 代码块**：脚本在当前工作目录创建证据包文件：
- manifest.json
- evidence/solver.log
- evidence/mesh_report.txt
- evidence/samples/profile.csv

证据包必须来自你在自己的求解器环境中**真实求解**的产物（判分侧不运行求解器，
将用案例冻结的 QoI 脚本从证据包原始数据降算指标并与留出参考值对账；
自报最终数值不进入判分，格式不符判 0）。
