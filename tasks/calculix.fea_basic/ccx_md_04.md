# Cantilever beam natural frequencies (200×12×6 mm)

Compute the first natural frequencies of a cantilever beam with CalculiX:

- Geometry: length L = 200 mm along x, cross-section H = 12 mm in y,
  T = 6 mm in z (note H = 2T: first mode bends about the weak axis).
- Root face x=0 fully clamped (set NROOT = all nodes with x=0); set NTIP = tip face nodes.
- Material includes density (7.85e-9 tonne/mm^3) — required for *FREQUENCY.
- Analysis: `*STEP` with `*FREQUENCY` requesting 4 modes (linear perturbation).
- Minimum mesh: >= 16 elements along the length, >= 4 through the height,
  >= 2 through the width (C3D20).
- Node sets: NROOT, NTIP (not printed, but define them).

## Deliverable

Respond with ONE complete ```python code block: a script that, when executed in an
empty working directory, writes a valid CalculiX 2.23 input deck named exactly
`model.inp` (in the current directory). The script must NOT run the solver, must not
use subprocess/network, and must be self-contained (no external files).

## Deck discipline (grading contract)

- Units: mm, N, MPa, tonne/mm^3 — steel: E = 210000 MPa, nu = 0.3,
  rho = 7.85e-9 tonne/mm^3.
- Elements: 20-node hexahedra `C3D20` ONLY, on a structured mesh with
  AT LEAST the minimum mesh counts stated above.
- Node sets with EXACTLY the names given below (grading parses the .dat output
  for these set names).
- Any data line must contain at most 16 comma-separated entries (wrap element
  connectivity and node-set lines across lines as needed).
- Request exactly the output prints specified below, inside the step.
