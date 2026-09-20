#!/usr/bin/env python3
"""
Generate a CalculiX 2.23 input deck 'model.inp' for a cantilever beam
linear static deflection analysis.

Model:
  - Beam 100 x 10 x 5 mm (L x H x T), root face at x=0 fully clamped.
  - Total tip load Fy = -1000 N split equally over ALL nodes of the tip
    face x=L (sum of nodal *CLOAD values is exactly -1000.0 N).
  - Structured mesh of 20-node hexahedra (C3D20):
      16 elements along x (>= 16), 4 through height y (>= 4), 2 through
      width z (>= 2).
  - Units: mm, N, MPa, tonne/mm^3 (steel: E=210000 MPa, nu=0.3,
    rho=7.85e-9 tonne/mm^3).
  - Node sets NROOT (all nodes at x=0) and NTIP (all nodes at x=L).
  - Step output: *NODE PRINT U for NTIP, *NODE PRINT RF for NROOT.

The script only writes 'model.inp'; it does NOT run the solver.
All data lines contain at most 16 comma-separated entries.
"""

# ----------------------------------------------------------------------------
# Parameters
# ----------------------------------------------------------------------------
L = 100.0          # beam length along x [mm]
H = 10.0           # cross-section height along y [mm]
T = 5.0            # cross-section width along z [mm]

NX = 16            # elements along length (minimum 16)
NY = 4             # elements through height (minimum 4)
NZ = 2             # elements through width  (minimum 2)

E_YOUNG = 210000.0     # Young's modulus [MPa]
NU = 0.3               # Poisson's ratio
RHO = 7.85e-9          # density [tonne/mm^3]

FY_TOTAL = -1000.0     # total tip force in y [N]

OUT_FILE = "model.inp"

# Number of node "lines" per direction in the quadratic mesh
NXL = 2 * NX + 1
NYL = 2 * NY + 1
NZL = 2 * NZ + 1


def nid(i, j, k):
    """1-based node id for grid line indices (i,j,k) in quadratic mesh."""
    return 1 + i + j * NXL + k * NXL * NYL


def main():
    lines = []
    ap = lines.append

    # ------------------------------------------------------------------ nodes
    ap("*HEADING")
    ap("Cantilever beam 100x10x5 mm, C3D20, tip load -1000 N, linear static")
    ap("** Units: mm, N, MPa, tonne/mm^3")
    ap("*NODE, NSET=NALL")
    for k in range(NZL):
        z = -T / 2.0 + T * k / (2.0 * NZ)
        for j in range(NYL):
            y = -H / 2.0 + H * j / (2.0 * NY)
            for i in range(NXL):
                x = L * i / (2.0 * NX)
                ap("{:d}, {:.6f}, {:.6f}, {:.6f}".format(nid(i, j, k), x, y, z))

    # --------------------------------------------------------------- elements
    # C3D20 node ordering (ABAQUS/CalculiX convention):
    #   1-4  : corners of the -z face, counterclockwise seen from +z
    #   5-8  : corners of the +z face, node 5 above node 1, etc.
    #   9-12 : mid-side nodes of bottom face edges 1-2, 2-3, 3-4, 4-1
    #   13-16: mid-side nodes of top face edges 5-6, 6-7, 7-8, 8-5
    #   17-20: mid-side nodes of vertical edges 1-5, 2-6, 3-7, 4-8
    ap("*ELEMENT, TYPE=C3D20, ELSET=EALL")
    elem = 0
    for iz in range(NZ):
        for iy in range(NY):
            for ix in range(NX):
                elem += 1
                i0, j0, k0 = 2 * ix, 2 * iy, 2 * iz
                i1, i2 = i0 + 1, i0 + 2
                j1, j2 = j0 + 1, j0 + 2
                k1, k2 = k0 + 1, k0 + 2
                conn = [
                    nid(i0, j0, k0), nid(i2, j0, k0), nid(i2, j2, k0), nid(i0, j2, k0),
                    nid(i0, j0, k2), nid(i2, j0, k2), nid(i2, j2, k2), nid(i0, j2, k2),
                    nid(i1, j0, k0), nid(i2, j1, k0), nid(i1, j2, k0), nid(i0, j1, k0),
                    nid(i1, j0, k2), nid(i2, j1, k2), nid(i1, j2, k2), nid(i0, j1, k2),
                    nid(i0, j0, k1), nid(i2, j0, k1), nid(i2, j2, k1), nid(i0, j2, k1),
                ]
                # 16 entries max per line: label + 15 nodes, then continuation
                first = [str(elem)] + [str(n) for n in conn[:15]]
                ap(", ".join(first))
                ap(", ".join(str(n) for n in conn[15:]))

    # -------------------------------------------------------------- node sets
    nroot = sorted(nid(0, j, k) for j in range(NYL) for k in range(NZL))
    ntip = sorted(nid(2 * NX, j, k) for j in range(NYL) for k in range(NZL))

    def write_nset(name, ids):
        ap("*NSET, NSET={}".format(name))
        for s in range(0, len(ids), 16):
            ap(", ".join(str(n) for n in ids[s:s + 16]))

    write_nset("NROOT", nroot)
    write_nset("NTIP", ntip)

    # ------------------------------------------- material and section (steel)
    ap("** Steel, units mm/N/MPa/tonne per mm^3")
    ap("*MATERIAL, NAME=STEEL")
    ap("*ELASTIC")
    ap("{:.1f}, {:.1f}".format(E_YOUNG, NU))
    ap("*DENSITY")
    ap("{:.3e}".format(RHO))
    ap("*SOLID SECTION, ELSET=EALL, MATERIAL=STEEL")

    # ------------------------------------------------------------- tip loads
    # Total Fy = FY_TOTAL split equally among ALL NTIP nodes; the printed
    # values sum exactly to FY_TOTAL (last value absorbs rounding).
    per_val = float("{:.6f}".format(FY_TOTAL / len(ntip)))
    vals = [per_val] * len(ntip)
    vals[-1] = round(FY_TOTAL - sum(vals[:-1]), 6)

    # ------------------------------------------------------------- boundaries
    ap("** Fully clamp the root face x=0 (all DOF)")
    ap("*BOUNDARY")
    ap("NROOT, 1, 6, 0.0")

    # ------------------------------------------------------------------- step
    ap("*STEP")
    ap("*STATIC")
    ap("** Total tip force {:.1f} N in y, equally distributed over {:d} NTIP nodes"
       .format(FY_TOTAL, len(ntip)))
    ap("*CLOAD")
    for node, val in zip(ntip, vals):
        ap("{:d}, 2, {:.6f}".format(node, val))
    ap("*NODE PRINT, NSET=NTIP")
    ap("U")
    ap("*NODE PRINT, NSET=NROOT")
    ap("RF")
    ap("*END STEP")

    with open(OUT_FILE, "w") as f:
        f.write("\n".join(lines) + "\n")

    # Small sanity summary (no solver execution)
    print("Wrote {}: {} nodes, {} C3D20 elements".format(
        OUT_FILE, NXL * NYL * NZL, NX * NY * NZ))
    print("NTIP nodes: {} (per-node Fy = {:.6f} N, sum = {:.6f} N)".format(
        len(ntip), vals[0], sum(vals)))


if __name__ == "__main__":
    main()