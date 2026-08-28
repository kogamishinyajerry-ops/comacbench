# Engineering Brief: Natural Convection in a Square Cavity, Ra = 1e4 (2D)

## Task

Set up and run a two-dimensional buoyancy-driven natural convection case
in a differentially heated square cavity with the solver of your choice
(any CFD package or in-house code), converge it to a steady state, and
submit an **evidence bundle** documenting the run. The quantity of
interest is the **average Nusselt number on the hot wall**.

The evaluation harness does **not** run your solver. It validates the
evidence bundle and recomputes the QoI from your raw wall data with a
frozen reduction script. Numbers you compute yourself never enter the
verdict — only the raw evidence does.

## Geometry

- Square cavity, side **H = 1.0 m** (see `drawing.png`).
- Coordinates: bottom-left corner at (0, 0); x to the right, y upward.
- Two-dimensional: single cell layer (or symmetry/2D setup) in the
  out-of-plane direction.

## Fluid model and flow regime

- Incompressible fluid with the **Boussinesq approximation** for
  buoyancy: density variations enter only through the gravity body
  force, rho = rho0 * (1 - beta * (T - T0)).
- Laminar, steady.
- Properties (constant):
  - reference density **rho0 = 1.0 kg/m^3** at T0 = 288 K
  - dynamic viscosity **mu = 4.571e-3 Pa s** (nu = 4.571e-3 m^2/s)
  - thermal expansion coefficient **beta = 3.0e-3 1/K**
  - specific heat **Cp = 1000 J/(kg K)**
  - Prandtl number **Pr = 0.71**, hence thermal diffusivity
    alpha = nu/Pr = 6.437e-3 m^2/s and conductivity
    k = mu*Cp/Pr = 6.437 W/(m K)
- Gravity **g = 9.81 m/s^2** acting downward (-y).

## Boundary conditions

- Left wall (x = 0), the **hot wall**: fixed temperature **T_hot = 293 K**.
- Right wall (x = 1), the **cold wall**: fixed temperature
  **T_cold = 283 K**.
- Top and bottom walls: **adiabatic** (zero heat flux).
- All walls: no-slip, stationary.

With dT = T_hot - T_cold = 10 K this gives
Ra = g * beta * dT * H^3 / (nu * alpha) = 1.0e4.

## Solution requirements

- Steady solver with coupled velocity-temperature iteration (buoyancy
  converges slowly); converge until residuals are down by at least 4
  orders of magnitude and the hot-wall heat flux is stationary between
  checks.
- Second-order spatial discretization recommended; first-order
  upwinding smears the wall temperature gradient and directly degrades
  the heat flux.
- Resolve the thermal boundary layers on both vertical walls (they are
  thin at Ra = 1e4).

## Sampling requirement

Export the **heat flux distribution along the hot wall** (x = 0) of the
converged steady field:

- Local wall heat flux q [W/m^2] at stations along the wall height.
  Sign convention is free (the reduction works on magnitudes); use your
  solver's native wall heat flux or -k * dT/dn at the wall.
- Stations must cover the **full wall height** (y from 0 to H), be
  monotonically increasing in y, **uniformly spaced** (equal-height
  strips, so the plain average is the area average), at least 16
  stations; 32-64 stations are typical.

## Deliverable: evidence bundle (layout v1)

Submit a directory with exactly this layout:

```
submission/
  manifest.json
  evidence/
    solver.log
    mesh_report.txt
    samples/
      hot_wall_flux.csv
```

### manifest.json

A JSON object:

```json
{
  "solver": "<solver name and version>",
  "mesh_cells": 4096,
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

### evidence/samples/hot_wall_flux.csv

The hot-wall heat flux distribution, one header row plus one row per
station:

```
y,q
0.0078125,216.85
...
```

- `y`: vertical coordinate of the station [m] along the hot wall, 0 at
  the bottom. Must satisfy 0 <= y <= 1, be strictly increasing and
  uniformly spaced down the file, start at y <= 0.02 and end at
  y >= 0.98 (full-height coverage); at least 16 stations.
- `q`: wall heat flux at the station [W/m^2] (sign convention free; the
  reduction uses magnitudes).

All values plain decimal or scientific notation, no NaN/Inf, no units in
the cells, no extra columns or comment lines.

## Acceptance

The harness checks that every file above exists and is well-formed, then
reduces **hot_wall_nu_avg = mean(|q|) * H / (k * dT)** from your
`hot_wall_flux.csv` — with H = 1 m, k = 6.437 W/(m K), dT = 10 K this is
mean(|q|) / 64.37 — and reconciles it against a held-out reference
value. Generic consistency rules: every CSV must parse, no cell may be
NaN/Inf, and any column named like a time/iteration axis (time, t, iter,
iteration, step, timestep) must be fully numeric and non-decreasing.
