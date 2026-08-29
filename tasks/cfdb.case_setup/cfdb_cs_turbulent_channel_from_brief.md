# cfdb case_setup (evidence) — Case Setup: Turbulent Channel Re_tau=180 from Engineering Brief (evidence mode)

case_setup domain EVIDENCE-mode task: the agent receives only a natural-language engineering brief (visible/task.md) and an annotated dimensioned drawing (visible/drawing.png), drives ANY CFD solver in its own environment (Fluent, STAR-CCM+, in-house, OpenFOAM — the judge has NO solver), and submits an evidence bundle (manifest.json + solver log + mesh report + wall-shear samples). The judge validates the bundle and recomputes the QoI from the raw evidence with the frozen script reference/compute_qoi.py on the host. Task physics: fully developed turbulent plane channel at Re_tau = 180 (half-height h = 1 m, bulk velocity U_b = 1 m/s imposed, nu = 3.571429e-4 m^2/s so Re_b = 2800), steady RANS with declared turbulence model and near-wall treatment. QoI cf_bulk = tau_w/(0.5*rho*U_b^2); held-out reference = published Moser, Kim & Mansour (1999) DNS value Cf = 8.18e-3. Task physics and golden measurement (Cf = 7.842e-3, 4.13% low, docker OpenFOAM v2312 kOmegaSST on the 2048-cell demo mesh) inherited from cases/validation/turbulent_channel_retau180; see provenance.yaml.

## 交付形式（evidence 证据包，严格遵守）
输出**单个 ```python 代码块**：脚本在当前工作目录创建证据包文件：
- manifest.json
- evidence/solver.log
- evidence/mesh_report.txt
- evidence/samples/wall_shear.csv

证据包必须来自你在自己的求解器环境中**真实求解**的产物（判分侧不运行求解器，
将用案例冻结的 QoI 脚本从证据包原始数据降算指标并与留出参考值对账；
自报最终数值不进入判分，格式不符判 0）。
