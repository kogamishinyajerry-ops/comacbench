# cfdb case_setup (evidence) — Case Setup: Laminar Backward-Facing Step Re=100 from Engineering Brief (evidence)

case_setup domain, EVIDENCE mode: the agent receives only a natural-language engineering brief (visible/task.md) and an annotated dimensioned drawing (visible/drawing.png), drives ANY solver in its own environment (Fluent/STAR-CCM+/in-house/OpenFOAM — the judge has no solver), and submits an evidence bundle (manifest.json + solver-native log + mesh report + bottom-wall shear stress distribution CSV). The judge validates the bundle and recomputes the QoI from the raw evidence with the frozen script reference/compute_qoi.py on the host — a self-reported QoI never enters the verdict. Task physics inherited from the VALIDATED case cases/validation/backward_facing_step_laminar: expansion ratio ER=2, step height h=0.01 m, fully developed parabolic inlet (mean Um=1 m/s), nu=2e-4 m^2/s -> Re = Um*D_h/nu = 100 (D_h = 2*inlet channel height, the Armaly et al. 1983 / Erturk 2008 convention); QoI reattachment_x_over_h = primary reattachment length x_r/h located by the negative->positive zero crossing of the bottom-wall shear stress. Held-out reference 2.922 (Erturk 2008, Comput. Fluids 37:633-655, Re=100 row) inherited verbatim from the source case. Docker-verified measurement on the golden configuration: 2.8715 (1.73% error, 6100-cell demo mesh); see provenance.yaml.

## 交付形式（evidence 证据包，严格遵守）
输出**单个 ```python 代码块**：脚本在当前工作目录创建证据包文件：
- manifest.json
- evidence/solver.log
- evidence/mesh_report.txt
- evidence/samples/wall_shear.csv

证据包必须来自你在自己的求解器环境中**真实求解**的产物（判分侧不运行求解器，
将用案例冻结的 QoI 脚本从证据包原始数据降算指标并与留出参考值对账；
自报最终数值不进入判分，格式不符判 0）。
