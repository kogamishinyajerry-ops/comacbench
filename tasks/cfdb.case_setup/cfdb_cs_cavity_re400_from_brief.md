# Engineering Brief: Lid-Driven Cavity, Re = 400 (2D laminar)

## Task

Set up and run a two-dimensional laminar lid-driven cavity case with the
solver of your choice (any CFD package or in-house code), drive it to a
converged steady state, and submit an **evidence bundle** documenting the
run. You are free to use any meshing strategy, solver settings, and
hardware, subject to the physics requirements below.

The evaluation harness does **not** run your solver. It validates the
evidence bundle and recomputes the quantity of interest (QoI) from your
raw sampled data with a frozen reduction script. Numbers you compute
yourself never enter the verdict — only the raw evidence does.

## Geometry

- Square cavity, side **H = 0.1 m** (see `drawing.png`).
- Coordinates: bottom-left corner at (0, 0); x to the right, y upward.
- Two-dimensional: use a single cell layer (or a symmetry/2D setup) in
  the out-of-plane direction.

## Fluid and flow regime

- Incompressible Newtonian fluid, laminar.
- Kinematic viscosity **nu = 2.5e-4 m^2/s**.
- Lid (top wall, y = H) moves in the +x direction at **U_lid = 1.0 m/s**.
- Reynolds number based on cavity side: Re = U_lid * H / nu = 400.

## Boundary conditions

- Top wall (lid): no-slip, moving with U = (U_lid, 0).
- Bottom and side walls: no-slip, stationary.
- Pressure: zero normal gradient on all walls (reference value arbitrary).

## Solution requirements

- March the case (transient or pseudo-steady iteration, your choice)
  until the velocity field is steady: residuals down by at least 4
  orders of magnitude, and the sampled centerline profile stationary
  between successive checks.
- Second-order spatial discretization recommended; the cavity is
  diffusion-dominated and first-order upwinding visibly thickens the
  core vortex and degrades the profile.
- Keep the Courant number below 1 if you integrate in time.

## Sampling requirement

Sample the velocity vector on the **vertical centerline x = H/2 = 0.05 m**
of the converged steady field:

- Stations along y from near the bottom wall up to **y/H = 0.95**
  (y = 0.095 m) — do NOT include the moving lid point itself.
- At least 10 stations, monotonically increasing in y; 15-25 stations
  uniformly spaced are typical.

## Deliverable: evidence bundle (layout v1)

Submit a directory with exactly this layout:

```
submission/
  manifest.json
  evidence/
    solver.log
    mesh_report.txt
    samples/
      centerline.csv
```

### manifest.json

A JSON object:

```json
{
  "solver": "<solver name and version>",
  "mesh_cells": 4096,
  "timing": {"wall_time_sec": 123.4},
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

### evidence/samples/centerline.csv

The centerline sample, one header row plus one row per station:

```
y,u,v
0.005,-0.0806,0.00049
...
```

- `y`: vertical coordinate of the station [m], measured from the bottom
  wall. Must satisfy 0 <= y <= 0.095 (the lid point is excluded) and be
  strictly increasing down the file.
- `u`: x-velocity component at the station [m/s].
- `v`: y-velocity component at the station [m/s].

All values plain decimal or scientific notation, no NaN/Inf, no units in
the cells, no extra columns or comment lines.

## Acceptance

The harness checks that every file above exists and is well-formed, then
reduces **centerline_umax = max over stations of sqrt(u^2 + v^2) / U_lid**
from your `centerline.csv` and reconciles it against a held-out
reference value. Generic consistency rules: every CSV must parse, no
cell may be NaN/Inf, and any column named like a time/iteration axis
(time, t, iter, iteration, step, timestep) must be fully numeric and
non-decreasing.
