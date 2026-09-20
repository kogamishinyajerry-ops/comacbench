# Cantilever beam static deflection (100×10×5 mm, tip load -1000.0 N)

Model a straight cantilever beam with CalculiX (linear static):

- Geometry: length L = 100 mm along +x (root at x=0), rectangular cross-section
  height H = 10 mm (y from -H/2 to +H/2), width T = 5 mm (z from -T/2 to +T/2).
- Root face x=0 fully clamped (all DOF, set NROOT = all nodes with x=0).
- Tip load: total force Fy = -1000.0 N distributed EQUALLY among ALL nodes of the
  tip face x=L (set NTIP) as concentrated nodal loads (*CLOAD), summing exactly to Fy.
- Minimum mesh: >= 16 elements along the length, >= 4 through the height,
  >= 2 through the width (C3D20).
- Node sets: NROOT (root face), NTIP (tip face).
- Output requests inside *STEP/*STATIC:
  `*NODE PRINT, NSET=NTIP` with `U`, and `*NODE PRINT, NSET=NROOT` with `RF`.

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
