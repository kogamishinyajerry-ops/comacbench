# cfdb case_setup (evidence) — Case Setup: Lid-Driven Cavity Re=400 from Engineering Brief (evidence)

case_setup domain, EVIDENCE mode: the agent receives only a natural-language engineering brief (visible/task.md) and an annotated dimensioned drawing (visible/drawing.png), drives ANY solver in its own environment (Fluent/STAR-CCM+/in-house/OpenFOAM — the judge has no solver), and submits an evidence bundle (manifest.json + solver-native log + mesh report + centerline sample CSV). The judge validates the bundle and recomputes the QoI from the raw evidence with the frozen script reference/compute_qoi.py on the host — a self-reported QoI never enters the verdict. Task physics inherited from the VALIDATED case cases/validation/lid_driven_cavity_re400: square cavity H=0.1 m, lid velocity U_lid=1 m/s, nu=2.5e-4 m^2/s (Re=400), 2D laminar to steady state; QoI centerline_umax = max |U|/U_lid on the vertical centerline (x=H/2) up to y/H=0.95. Held-out reference 0.551 (Ghia, Ghia & Shin 1982, JCP 48 Table I Re=400, interpolated at y/H=0.95) inherited verbatim from the source case. Docker-verified measurement on the golden configuration: 0.49778 (9.66% error, 64x64 demo mesh); see provenance.yaml.

## 交付形式（evidence 证据包，严格遵守）
输出**单个 ```python 代码块**：脚本在当前工作目录创建证据包文件：
- manifest.json
- evidence/solver.log
- evidence/mesh_report.txt
- evidence/samples/centerline.csv

证据包必须来自你在自己的求解器环境中**真实求解**的产物（判分侧不运行求解器，
将用案例冻结的 QoI 脚本从证据包原始数据降算指标并与留出参考值对账；
自报最终数值不进入判分，格式不符判 0）。
