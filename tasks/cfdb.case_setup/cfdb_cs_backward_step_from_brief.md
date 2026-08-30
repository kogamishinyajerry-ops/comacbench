# cfdb case_setup（evidence 工具通道）— Case Setup: Laminar Backward-Facing Step Re=100 from Engineering Brief (evidence)

## 两阶段交付协议（严格遵守）
你的脚本会被判分环境执行**两次**，以工作目录下的标记文件 `.cfdb_assemble` 区分：

**阶段 1（首次执行，无标记）**：在当前目录创建 `case/` 子目录，写入完整可运行的
OpenFOAM 算例（`0/` `constant/` `system/`，`system/controlDict` 的 `application`
声明求解器，并按任务书配置采样/监测 functionObject）。判分环境会在 OpenFOAM
v2312 真实执行该算例（blockMesh → 求解器）：`case/` 内落运行场与
`postProcessing/` 采样输出，各步骤日志（`log.block_mesh`、`log.solve` 等）
落在**工作目录根**。

**阶段 2（二次执行，存在 `.cfdb_assemble` 标记）**：从 `case/` 的**运行产物**提取
原始数据，组装证据包写入当前目录（不得编造/篡改数值——判分将用冻结脚本从证据包
原始数据降算指标并与留出参考对账，自报最终值永不进入判分）：
- manifest.json
- evidence/solver.log
- evidence/mesh_report.txt
- evidence/samples/wall_shear.csv

证据文件用 `open()` 逐文件读写（不要 import shutil——沙箱静态检查禁止）。
`manifest.json` 为 JSON 对象（至少含 solver 标识与说明字段）。

---

# Engineering Brief: Laminar Backward-Facing Step, Re = 100 (2D)

## Task

Set up and run a two-dimensional laminar flow over a backward-facing
step with the solver of your choice (any CFD package or in-house code),
converge it to a steady state, and submit an **evidence bundle**
documenting the run. The quantity of interest is the **primary
reattachment length** of the recirculation bubble behind the step.

The evaluation harness does **not** run your solver. It validates the
evidence bundle and recomputes the QoI from your raw wall data with a
frozen reduction script. Numbers you compute yourself never enter the
verdict — only the raw evidence does.

## Geometry

- Planar channel with a sudden 1:2 expansion (see `drawing.png`).
- Step height **h = 0.01 m**. Upstream (inlet) channel height **h**
  (0.01 m); downstream channel height **2h** (0.02 m).
- Step face at **x = 0**: upstream channel spans x in [-5h, 0], the
  expanded section spans x in [0, 30h].
- Bottom wall: y = h upstream of the step, y = 0 downstream of it.
- Two-dimensional: single cell layer (or symmetry/2D setup) in the
  out-of-plane direction.

## Fluid and flow regime

- Incompressible Newtonian fluid, laminar, steady.
- Kinematic viscosity **nu = 2.0e-4 m^2/s** (density 1 kg/m^3 if your
  solver needs one).
- Inlet (x = -5h): fully developed plane-channel **parabolic** velocity
  profile with mean velocity **Um = 1.0 m/s** (maximum 1.5 m/s on the
  inlet channel centerline), flow in +x.
- Reynolds number Re = Um * D_h / nu = 100, with the hydraulic diameter
  D_h = 2h = 0.02 m based on the inlet channel height (the standard
  convention for this benchmark).

## Boundary conditions

- Inlet: the parabolic profile above (do NOT use a uniform plug — the
  reattachment length is sensitive to the inlet state).
- Outlet (x = 30h): zero normal gradient for velocity, fixed reference
  pressure.
- All walls: no-slip, stationary.

## Solution requirements

- Steady laminar solver (or pseudo-steady iteration) converged until
  residuals are down by at least 4 orders of magnitude and the
  reattachment position is stationary between checks.
- Second-order spatial discretization recommended; first-order
  upwinding smears the shear layer and shifts the reattachment point.
- Resolve the near-wall region below the shear layer: the first cell
  height at the bottom wall downstream of the step should be a small
  fraction of h (the golden configuration uses about 0.02h).

## Sampling requirement

Export the **wall shear stress distribution along the bottom wall
downstream of the step** (y = 0, x > 0) of the converged steady field:

- Signed shear stress tau_w [Pa]: positive when the near-wall flow goes
  in +x, negative inside the recirculation bubble. (Sign convention: if
  your solver reports the wall-traction vector, take its x-component;
  magnitudes with a documented sign convention are equally acceptable as
  long as separated flow reads negative.)
- Stations from just downstream of the step face to at least **x = 6h**;
  spacing 0.1h or finer through the recirculation zone is typical. The
  primary reattachment point (where tau_w crosses zero from negative to
  positive) lies within a few step heights, so make sure the station
  spacing resolves it.

## Deliverable: evidence bundle (layout v1)

Submit a directory with exactly this layout:

```
submission/
  manifest.json
  evidence/
    solver.log
    mesh_report.txt
    samples/
      wall_shear.csv
```

### manifest.json

A JSON object:

```json
{
  "solver": "<solver name and version>",
  "mesh_cells": 6100,
  "timing": {"wall_time_sec": 42.0},
  "notes": "<free text: hardware, convergence criterion reached, ...>"
}
```

- `solver` (required): name and version of the solver you ran.
- `mesh_cells` (recommended): total cell count of the final mesh.
- `timing.wall_time_sec` (recommended): wall-clock seconds of the solver
  run, self-reported. It feeds the runtime budget check (budget
  3600 s). If omitted, the budget gate degrades to judging only the
  harness-side reduction time.

### evidence/solver.log

The solver's native log, unedited, showing at least the residual history
and the final convergence state.

### evidence/mesh_report.txt

Mesh summary as reported by your meshing tool or mesh check utility:
cell count, cell type(s), and quality metrics (e.g. min/max aspect
ratio, non-orthogonality, skewness — whatever your tool reports).

### evidence/samples/wall_shear.csv

The bottom-wall shear distribution, one header row plus one row per
station:

```
x,tau_w
0.0005,0.00028
0.0015,-0.00049
...
```

- `x`: streamwise coordinate of the station [m], measured from the step
  face (x = 0). Must satisfy x >= 0, be strictly increasing down the
  file, and reach at least x = 0.05 m (= 5h); at least 10 stations.
- `tau_w`: signed wall shear stress [Pa] at the station (positive =
  near-wall flow in +x).

All values plain decimal or scientific notation, no NaN/Inf, no units in
the cells, no extra columns or comment lines.

## Acceptance

The harness checks that every file above exists and is well-formed, then
reduces **reattachment_x_over_h = x_r / h** from your `wall_shear.csv`:
x_r is the first negative-to-positive zero crossing of tau_w downstream
of the step, located by linear interpolation between the bracketing
stations. The result is reconciled against a held-out reference value.
Generic consistency rules: every CSV must parse, no cell may be NaN/Inf,
and any column named like a time/iteration axis (time, t, iter,
iteration, step, timestep) must be fully numeric and non-decreasing.
