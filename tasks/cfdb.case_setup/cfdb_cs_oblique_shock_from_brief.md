# cfdb case_setup (evidence) — Case Setup: Oblique Shock over a 10° Wedge (M1=2) from Engineering Brief

case_setup domain, EVIDENCE mode (compressible/BL family): the agent receives only a solver-agnostic engineering brief (visible/task.md) and an annotated dimensioned drawing (visible/drawing.png), drives ANY CFD solver in its own environment (Fluent, STAR-CCM+, in-house, OpenFOAM, ...), and submits an evidence bundle (manifest.json + solver log + mesh report + Mach profile CSV). The judge runs NO solver: it validates the bundle and reduces post_shock_mach from the raw evidence with the frozen QoI script reference/compute_qoi.py on the host. Task physics: 2D inviscid calorically perfect gas (gamma=1.4), freestream M1=2, 10° wedge, weak-solution oblique shock (beta=39.31384°). QoI post_shock_mach = local Mach at (0.6, 0.15), interpolated from the submitted vertical Mach profile at x=0.6; held-out reference 1.640526 (theta-beta-M weak solution, Anderson Ch. 4). Task physics and golden measurement inherited from the VERIFIED case cases/verification/oblique_shock (docker run 2026-08-11: M2=1.638477, 0.125% low); see provenance.yaml.

## 交付形式（evidence 证据包，严格遵守）
输出**单个 ```python 代码块**：脚本在当前工作目录创建证据包文件：
- manifest.json
- evidence/solver.log
- evidence/mesh_report.txt
- evidence/samples/mach_profile.csv

证据包必须来自你在自己的求解器环境中**真实求解**的产物（判分侧不运行求解器，
将用案例冻结的 QoI 脚本从证据包原始数据降算指标并与留出参考值对账；
自报最终数值不进入判分，格式不符判 0）。
