# cfdb case_setup (evidence) — Case Setup: Natural Convection Cavity Ra=1e4 from Engineering Brief (evidence)

case_setup domain, EVIDENCE mode: the agent receives only a natural-language engineering brief (visible/task.md) and an annotated dimensioned drawing (visible/drawing.png), drives ANY solver in its own environment (Fluent/STAR-CCM+/in-house/OpenFOAM — the judge has no solver), and submits an evidence bundle (manifest.json + solver-native log + mesh report + hot-wall heat flux distribution CSV). The judge validates the bundle and recomputes the QoI from the raw evidence with the frozen script reference/compute_qoi.py on the host — a self-reported QoI never enters the verdict. Task physics inherited from the VALIDATED case cases/validation/natural_convection_cavity: de Vahl Davis (1983) differentially-heated square cavity, Boussinesq incompressible flow, laminar steady, unit square H=1 m, hot wall x=0 at 293 K, cold wall x=1 at 283 K, adiabatic top/bottom; g=9.81 m/s^2, beta=3e-3 1/K, rho0=1 kg/m^3, mu=4.571e-3 Pa s, Pr=0.71 -> Ra=1.0e4. QoI hot_wall_nu_avg = |q''|_avg * H / (k*dT) with k = mu*Cp/Pr = 6.437 W/(m K), i.e. Nu = |q''|_avg / 64.37, reduced from the wall heat flux distribution. Held-out reference 2.238 (de Vahl Davis 1983 hot-wall average Nu at Ra=1e4) inherited verbatim from the source case. Docker-verified measurement on the golden configuration: 2.2351 (0.13% error, 64x64 demo mesh); see provenance.yaml.

## 交付形式（evidence 证据包，严格遵守）
输出**单个 ```python 代码块**：脚本在当前工作目录创建证据包文件：
- manifest.json
- evidence/solver.log
- evidence/mesh_report.txt
- evidence/samples/hot_wall_flux.csv

证据包必须来自你在自己的求解器环境中**真实求解**的产物（判分侧不运行求解器，
将用案例冻结的 QoI 脚本从证据包原始数据降算指标并与留出参考值对账；
自报最终数值不进入判分，格式不符判 0）。
