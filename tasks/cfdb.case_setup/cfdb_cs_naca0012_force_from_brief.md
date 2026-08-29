# cfdb case_setup (evidence) — Case Setup: NACA0012 alpha=0 Force Coefficients from Engineering Brief (evidence mode)

case_setup domain EVIDENCE-mode task: the agent receives only a natural-language engineering brief (visible/task.md) and an annotated drawing (visible/drawing.png), drives ANY CFD solver in its own environment (Fluent, STAR-CCM+, in-house, OpenFOAM — the judge has NO solver), and submits an evidence bundle (manifest.json + solver log + mesh report + force-coefficient convergence history). The judge validates the bundle and recomputes the QoIs from the raw evidence with the frozen script reference/compute_qoi.py on the host (tail-mean of the steady force history). Task physics: NACA0012 symmetric airfoil at alpha = 0 deg, Re = 6e6, M = 0.3 (low-Mach RANS), chord c = 1 m. QoIs: cl and cd; held-out reference = Ladson 1988 (NASA TM-4074) experiment, cl = 0.0, cd = 0.0086. Task physics inherited from cases/validation/naca0012 (case id naca0012_a0); the golden evidence bundle is converted from a REAL docker run of that case (runs/20260811T093058Z_naca0012_a0_openfoam_6ae74883) — the first time the alpha=0 configuration was actually executed; see provenance.yaml.

## 交付形式（evidence 证据包，严格遵守）
输出**单个 ```python 代码块**：脚本在当前工作目录创建证据包文件：
- manifest.json
- evidence/solver.log
- evidence/mesh_report.txt
- evidence/force_history.csv

证据包必须来自你在自己的求解器环境中**真实求解**的产物（判分侧不运行求解器，
将用案例冻结的 QoI 脚本从证据包原始数据降算指标并与留出参考值对账；
自报最终数值不进入判分，格式不符判 0）。
