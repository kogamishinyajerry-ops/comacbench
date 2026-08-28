# Task: Lid-Driven Cavity (Re = 100) — Build the OpenFOAM Case

You are given this natural-language brief and the annotated drawing
`drawing.png` (same directory). Build a complete, runnable OpenFOAM case
directory from them. No case files are provided — every dictionary is
yours to write.

## Flow brief

- Square 2D cavity, side L = 0.1 m (see `drawing.png` for the annotated
  geometry and boundary conditions).
- The top wall ("lid") moves tangentially at U_lid = 1 m/s in +x; the
  other three walls are stationary no-slip walls.
- Fluid: incompressible, laminar, kinematic viscosity nu = 1e-3 m^2/s
  (Re = U_lid * L / nu = 100).
- Solve the transient with the incompressible laminar solver `icoFoam`,
  integrating from t = 0 to t = 5 s.

## Required submission interface

Your submission is the case directory itself, containing `0/`,
`constant/`, and `system/`. The harness will:

1. Copy your directory into a writable work zone inside a network-less
   sandbox (OpenFOAM v2312 image; serial runs only; no Python, no
   package installation inside).
2. Run `blockMesh` **only if `system/blockMeshDict` exists** — so place
   the blockMeshDict at `system/blockMeshDict`, not under
   `constant/polyMesh/`.
3. Read the `application` entry of `system/controlDict` and run that
   solver on the case.
4. Run a frozen QoI script on the host that reads the velocity probe
   output `postProcessing/probes/<time>/U` and computes
   `centerline_umax` = max |U| / U_lid over the probe line at the final
   recorded time.

To make step 4 possible, your case MUST record the velocity on the
vertical centerline (x = 0.05 m, spanning the cavity height up to
y/H = 0.95) with a `probes` functionObject sampling field `U` every time
step (`writeControl timeStep; writeInterval 1;`), so that
`postProcessing/probes/<time>/U` exists after the run.

## Quantity of Interest

- `centerline_umax`: maximum of |U|/U_lid on the vertical centerline
  probe line at the final time.

Mesh resolution and time-stepping are your engineering choice — the
score measures how close your computed QoI lands to the reference.
