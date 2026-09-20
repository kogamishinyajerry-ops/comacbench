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


## Explicit input audit profile (ccx.cantilever.v1)

Use a complete, axis-aligned, conforming structured C3D20 mesh of this solid
rectangular beam. Adjacent elements must share node IDs. Only define nodes used
by elements: ALL tip/root nodes above means ALL connected mesh nodes on that
face, including edge midside nodes, not unused points of a full 3-D half grid.
Every element must have one material assignment. Clamp only the root; do not
introduce extra constraints or any other nonzero load. C3D20 edge midside nodes
must lie at the geometric edge midpoints. Node numbers and axis orientation of
valid positive elements may vary. Refinement may be nonuniform, but must form a
complete Cartesian partition meeting the minimum counts.

The supported self-contained deck has one linear *STEP / *STATIC / *END STEP.
Supported keywords: HEADING; NODE (optional NSET); ELEMENT (TYPE=C3D20, optional
ELSET); NSET and ELSET (explicit IDs, previously defined sets, or GENERATE);
MATERIAL (NAME); ELASTIC (default or TYPE=ISOTROPIC); DENSITY; SOLID SECTION
(ELSET, MATERIAL, no extra data); BOUNDARY; STEP (optional NAME); STATIC; CLOAD;
NODE PRINT (NSET); END STEP. Other keywords/options, including INCLUDE, AMPLITUDE,
TRANSFORM, NLGEOM and multi-step analyses, are outside this profile. Data can be
wrapped at element and set boundaries as specified above; no external files.
Use finite numeric values. Maximum deck size 8 MiB, 100000 nodes, 20000 elements.

The Y force must be equally distributed per connected tip node; repeated CLOAD
entries in this one step are summed. This nodal load contract does not represent
uniform surface traction. Exactly request NTIP U and NROOT RF as above.
The input audit precedes the solver: violating a declared engineering requirement
makes this attempt invalid (zero overall score). Reference values and 5% result
tolerance are unchanged from aviation-core-v1.
