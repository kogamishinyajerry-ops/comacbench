# L-bracket static deflection (arms 60×60 mm, t=10 mm, W=20 mm)

Model a wall-mounted L-bracket with CalculiX (linear static):

- Cross-section (x-y plane) is an L shape: vertical arm x in [0, 10] with
  y in [0, 60], plus horizontal arm y in [0, 10] with x in [0, 60].
  The bracket is extruded in z over width W = 20 mm (z in [0, W]).
- Mount face: the whole face x=0 is clamped (set NROOT = all nodes with x=0).
- Load: total Fy = -500.0 N (downward, -y) distributed EQUALLY among ALL nodes
  of the free end face x=60 (set NLOAD), summing exactly to Fy.
- Minimum mesh (C3D20, structured, conformal at the re-entrant corner): >= 2 elements
  across each arm thickness, >= 6 along each arm length, >= 2 through the width.
- Output requests inside *STEP/*STATIC:
  `*NODE PRINT, NSET=NLOAD` with `U`, and `*NODE PRINT, NSET=NROOT` with `RF`.

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
