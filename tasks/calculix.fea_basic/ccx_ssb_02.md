# Simply supported beam, mid-span load (160×12×6 mm, P=-1200.0 N)

Model a simply supported beam on knife-edge supports with CalculiX (linear static):

- Geometry: length L = 160 mm along x, cross-section H = 12 mm (y from -H/2
  to +H/2), T = 6 mm (z from -T/2 to +T/2).
- Supports (knife edges at the BOTTOM lines of the end faces, y = -H/2):
  set NLEFT = nodes at x=0, y=-H/2 (all z); set NRIGHT = nodes at x=L, y=-H/2 (all z).
  Constrain Uy = 0 on NLEFT and NRIGHT; additionally fix Ux and Uz of ONE node of
  NLEFT (set PIN, just that node) to remove rigid-body modes. All other DOF free.
- Mid-span load: total Fy = -1200.0 N distributed EQUALLY among ALL nodes of the
  mid-span section x=L/2 (set NMID), summing exactly to Fy.
- Minimum mesh: >= 16 elements along the length, >= 4 through the height,
  >= 2 through the width (C3D20).
- Output requests inside *STEP/*STATIC:
  `*NODE PRINT, NSET=NMID` with `U`, and `*NODE PRINT, NSET=NLEFT` with `RF`.

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
