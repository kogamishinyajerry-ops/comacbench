# cfdb case_setup (evidence) — Case Setup: Turbulent Flat Plate (k-omega SST RANS) from Engineering Brief

case_setup domain, EVIDENCE mode (compressible/BL family): the agent receives only a solver-agnostic engineering brief (visible/task.md) and an annotated dimensioned drawing (visible/drawing.png), drives ANY CFD solver in its own environment, and submits an evidence bundle (manifest.json + solver log + mesh report + wall Cf distribution CSV). The judge runs NO solver: it validates the bundle and reduces the two station Cf QoIs from the raw evidence with the frozen QoI script reference/compute_qoi.py on the host (linear interpolation of the submitted Cf(x) to Re_x = 5e5 and 1e6). Task physics: 2D steady incompressible zero-pressure-gradient TURBULENT flat plate, U_inf=10 m/s, nu=1e-5 m^2/s (Re_x = 1e6 per metre, plate spans 0..2e6), fully turbulent RANS with a k-omega SST class model, inlet turbulence intensity 5% / length scale 0.01 m, wall-function y+ regime. Held-out reference: 1/7-power-law engineering correlation Cf = 0.0592*Re_x^(-1/5) at the two stations (White 2006), inherited verbatim from the VALIDATED source case cases/validation/turbulent_flat_plate (docker run 2026-08-11 measured Cf 5.9%/3.0% low at the two stations, inside the 15% V&V tolerance); see provenance.yaml.

## 交付形式（evidence 证据包，严格遵守）
输出**单个 ```python 代码块**：脚本在当前工作目录创建证据包文件：
- manifest.json
- evidence/solver.log
- evidence/mesh_report.txt
- evidence/samples/cf_distribution.csv

证据包必须来自你在自己的求解器环境中**真实求解**的产物（判分侧不运行求解器，
将用案例冻结的 QoI 脚本从证据包原始数据降算指标并与留出参考值对账；
自报最终数值不进入判分，格式不符判 0）。
