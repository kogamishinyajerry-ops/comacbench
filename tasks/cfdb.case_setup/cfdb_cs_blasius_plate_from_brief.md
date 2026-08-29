# cfdb case_setup (evidence) — Case Setup: Laminar Flat-Plate Boundary Layer (Blasius Cf) from Engineering Brief

case_setup domain, EVIDENCE mode (compressible/BL family): the agent receives only a solver-agnostic engineering brief (visible/task.md) and an annotated dimensioned drawing (visible/drawing.png), drives ANY CFD solver in its own environment, and submits an evidence bundle (manifest.json + solver log + mesh report + wall Cf distribution CSV). The judge runs NO solver: it validates the bundle and reduces the four station Cf QoIs from the raw evidence with the frozen QoI script reference/compute_qoi.py on the host (linear interpolation of the submitted Cf(x) to x = 0.2/0.5/0.8/1.0 m). Task physics: 2D incompressible laminar flat-plate boundary layer, U_inf=1 m/s, nu=1e-5 m^2/s (Re_x = 1e5 per metre), stations span Re_x = 2e4..1e5, safely laminar. Held-out reference: Blasius Cf = 0.664/sqrt(Re_x) at the four stations (Schlichting & Gersten), inherited verbatim from the VERIFIED source case cases/verification/flat_plate_blasius_of (docker run 2026-08-11 measured Cf 4.0%/7.2%/9.4%/10.6% high at the four stations, inside the 15% V&V tolerance); see provenance.yaml.

## 交付形式（evidence 证据包，严格遵守）
输出**单个 ```python 代码块**：脚本在当前工作目录创建证据包文件：
- manifest.json
- evidence/solver.log
- evidence/mesh_report.txt
- evidence/samples/cf_distribution.csv

证据包必须来自你在自己的求解器环境中**真实求解**的产物（判分侧不运行求解器，
将用案例冻结的 QoI 脚本从证据包原始数据降算指标并与留出参考值对账；
自报最终数值不进入判分，格式不符判 0）。
