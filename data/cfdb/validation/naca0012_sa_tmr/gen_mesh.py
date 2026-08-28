"""Generate system/blockMeshDict for naca0012_sa_tmr (pure Python stdlib).

Structured C-grid-style multi-block mesh for the NACA 0012 at alpha = 0,
Re = 6e6, targeting the NASA Turbulence Modeling Resource (TMR) SA
validation conditions (M = 0.15, Re_c = 6 million, fully turbulent).

Geometry: TMR's *altered* NACA 0012 definition (sharp trailing edge),
transcribed from https://tmbwg.github.io/turbmodels/naca0012_val.html
(formerly turbmodels.larc.nasa.gov/naca0012_val.html):

    y = +- 0.594689181 * [0.298222773*sqrt(x) - 0.127125232*x
        - 0.357907906*x^2 + 0.291984971*x^3 - 0.105174606*x^4]

Topology (10 hex blocks, full plane, no symmetry BC):
    Per half-plane: upstream block, two airfoil blocks (split at x/c = 0.5),
    a geometrically graded near-wake block (first cell 2.5e-3 c behind the
    TE, growing to 0.15 c) and a uniform far-wake block to the outlet plane. The airfoil surface is a
    spline edge; wall-normal grading gives a first cell of ~3e-4 c
    (y+ ~ 65 at Re = 6e6, i.e. the wall-function regime — this demo mesh is
    deliberately far coarser than the TMR 897x257 / finer grid families).

Farfield extent is only ~20-40 c (TMR grids use ~500 c); the difference is
one of the documented reasons for the case's honest Cd tolerance
(see case.yaml).

Usage:
    python3 gen_mesh.py            # writes system/blockMeshDict next to this file
"""

from __future__ import annotations

import math
from pathlib import Path

# ---------------------------------------------------------------- parameters
X_UP = 20.0       # upstream extent (x = -X_UP), chords
X_OUT = 40.0      # outlet plane (x = +X_OUT), chords
Y_FF = 20.0       # top/bottom farfield (y = +-Y_FF), chords
Z_HALF = 0.05     # 2D span half-thickness; Aref = chord * 2*Z_HALF = 0.1

N_RADIAL = 55     # wall-normal cells (all blocks share this distribution)
D_WALL = 3.0e-4   # first wall-normal cell height (chords), y+ ~ 65

N_CHORD_FWD = 40  # chordwise cells, LE -> x/c=0.5
N_CHORD_AFT = 40  # chordwise cells, x/c=0.5 -> TE
D_LE = 2.5e-3     # first chordwise cell at the leading edge (arc length).
#   NOTE: 5e-4 was tried and resolves the suction peak better, but with this
#   BC/solver set the SA field then goes into a slow large-amplitude limit
#   cycle (Cl ~ O(1) swings by iter ~900); 2.5e-3 is the largest value we
#   found that stays steady. The under-resolved LE suction peak is the main
#   driver of the case's high pressure drag - see case.yaml tolerance note.
D_TE = 2.5e-3     # last chordwise cell at the trailing edge

N_UP = 80         # streamwise cells in the upstream block (uniform)
N_WAKE_NEAR = 150  # streamwise cells TE -> wake-split (geometric growth)
D_TE_WAKE = 2.5e-3  # first wake cell behind the TE (matches D_TE at the spoke)
D_WAKE_MID = 0.2    # cell size at the near/far wake split and in the far wake

N_SPLINE = 25     # intermediate spline points per airfoil segment


def yt(x: float) -> float:
    """TMR altered NACA 0012 half-thickness (sharp TE), see module docstring."""
    return 0.594689181 * (
        0.298222773 * math.sqrt(x)
        - 0.127125232 * x
        - 0.357907906 * x**2
        + 0.291984971 * x**3
        - 0.105174606 * x**4
    )


def surface_points(x0: float, x1: float, n: int, upper: bool) -> list[tuple[float, float]]:
    """n intermediate spline points between x0 and x1 (endpoints excluded),
    cosine-clustered toward both ends. Order follows x0 -> x1."""
    pts = []
    for j in range(1, n + 1):
        s = 0.5 * (1.0 - math.cos(math.pi * j / (n + 1.0)))  # 0..1
        x = x0 + (x1 - x0) * s
        y = yt(x) if upper else -yt(x)
        pts.append((x, y))
    return pts


def arc_length(x0: float, x1: float, upper: bool = True, n: int = 2000) -> float:
    """Numerical arc length of the airfoil surface between x0 and x1."""
    length = 0.0
    xp, yp = x0, (yt(x0) if upper else -yt(x0))
    for i in range(1, n + 1):
        x = x0 + (x1 - x0) * i / n
        y = yt(x) if upper else -yt(x)
        length += math.hypot(x - xp, y - yp)
        xp, yp = x, y
    return length


def geometric_ratio(n: int, first_cell: float, total: float) -> float:
    """Solve the geometric growth factor r > 1 such that
    first_cell * (r**n - 1) / (r - 1) == total, by bisection."""
    if first_cell * n >= total:
        raise ValueError(f"first_cell*n >= total ({first_cell}*{n} vs {total})")
    lo, hi = 1.0 + 1e-9, 2.0
    for _ in range(200):
        mid = 0.5 * (lo + hi)
        s = first_cell * (mid**n - 1.0) / (mid - 1.0)
        if s < total:
            lo = mid
        else:
            hi = mid
    return 0.5 * (lo + hi)


def grading_ratio(n: int, first_cell: float, total: float) -> float:
    """blockMesh simpleGrading ratio (last cell / first cell) for a geometric
    distribution starting with first_cell over length total."""
    r = geometric_ratio(n, first_cell, total)
    return r ** (n - 1)


def fmt_pt(p: tuple[float, float, float]) -> str:
    return f"({p[0]:.8g} {p[1]:.8g} {p[2]:.8g})"


def build_dict() -> str:
    y_mid = yt(0.5)

    # ---- grading ratios
    r_rad = grading_ratio(N_RADIAL, D_WALL, Y_FF)
    l_fwd = arc_length(0.0, 0.5)
    l_aft = arc_length(0.5, 1.0)
    r_cf = grading_ratio(N_CHORD_FWD, D_LE, l_fwd)       # grow LE -> mid
    r_ca = 1.0 / grading_ratio(N_CHORD_AFT, D_TE, l_aft)  # shrink mid -> TE
    # Upstream block: uniform cells. Geometric growth from a TE-scale first
    # cell to a 15c farfield either needs thousands of cells or produces
    # far-field cells with aspect ratio > 1e4 against the thin wall-normal
    # first layer (checkMesh aspect check); uniform 0.25c keeps AR < 1000.
    r_up = 1.0
    # Wake: geometric growth from the TE cell size (2.5e-3) to 0.15c over the
    # near-wake block (TMR notes TE streamwise spacing strongly affects drag
    # convergence), then a uniform 0.15c far-wake block out to the outlet.
    r_wn = D_WAKE_MID / D_TE_WAKE  # simpleGrading ratio (last/first)
    # geometric series length of the near-wake block
    rr = r_wn ** (1.0 / (N_WAKE_NEAR - 1))
    x_split = 1.0 + D_TE_WAKE * (rr ** N_WAKE_NEAR - 1.0) / (rr - 1.0)
    n_wake_far = max(1, round((X_OUT - x_split) / D_WAKE_MID))

    # ---- 2D point table (z planes at -Z_HALF and +Z_HALF)
    pts2d = [
        (0.0, 0.0),        # 0  LE
        (1.0, 0.0),        # 1  TE
        (0.5, y_mid),      # 2  Mu (mid-chord, upper surface)
        (0.5, -y_mid),     # 3  Ml
        (0.0, Y_FF),       # 4  Au
        (0.0, -Y_FF),      # 5  Al
        (0.5, Y_FF),       # 6  Bu
        (0.5, -Y_FF),      # 7  Bl
        (1.0, Y_FF),       # 8  Cu
        (1.0, -Y_FF),      # 9  Cl
        (-X_UP, 0.0),      # 10 D  (upstream, on the axis)
        (-X_UP, Y_FF),     # 11 E
        (-X_UP, -Y_FF),    # 12 El
        (X_OUT, 0.0),      # 13 W  (outlet, on the axis)
        (X_OUT, Y_FF),     # 14 O
        (X_OUT, -Y_FF),    # 15 Ol
        (x_split, 0.0),    # 16 Wm (near/far wake split, on the axis)
        (x_split, Y_FF),   # 17 Um
        (x_split, -Y_FF),  # 18 Lm
    ]
    nz = len(pts2d)  # z-plane offset for vertex ids

    # ---- blocks: (2D quad corners CCW from +z, counts, grading)
    blocks = [
        # upstream / airfoil-forward / airfoil-aft / wake-near / wake-far,
        # upper half
        ((10, 0, 4, 11), (N_UP, N_RADIAL, 1), (r_up, r_rad, 1.0)),
        ((0, 2, 6, 4), (N_CHORD_FWD, N_RADIAL, 1), (r_cf, r_rad, 1.0)),
        ((2, 1, 8, 6), (N_CHORD_AFT, N_RADIAL, 1), (r_ca, r_rad, 1.0)),
        ((1, 16, 17, 8), (N_WAKE_NEAR, N_RADIAL, 1), (r_wn, r_rad, 1.0)),
        ((16, 13, 14, 17), (n_wake_far, N_RADIAL, 1), (1.0, r_rad, 1.0)),
        # lower half (mirrored, re-ordered to stay CCW from +z)
        ((10, 12, 5, 0), (N_RADIAL, N_UP, 1), (r_rad, r_up, 1.0)),
        ((0, 5, 7, 3), (N_RADIAL, N_CHORD_FWD, 1), (r_rad, r_cf, 1.0)),
        ((3, 7, 9, 1), (N_RADIAL, N_CHORD_AFT, 1), (r_rad, r_ca, 1.0)),
        ((1, 9, 18, 16), (N_RADIAL, N_WAKE_NEAR, 1), (r_rad, r_wn, 1.0)),
        ((16, 18, 15, 13), (N_RADIAL, n_wake_far, 1), (r_rad, 1.0, 1.0)),
    ]

    # ---- curved edges (airfoil splines + nose-wrap arcs); all other edges
    # are straight. blockMesh does NOT propagate a curved edge to the
    # corresponding edge on the other z plane — each vertex pair needs its
    # own definition, otherwise the back-plane edge is a straight chord and
    # every wall cell becomes a twisted (ruled) face (checkMesh: incorrectly
    # oriented faces).
    spline_edges = []
    for v0, v1, pts in [
        (0, 2, surface_points(0.0, 0.5, N_SPLINE, upper=True)),
        (2, 1, surface_points(0.5, 1.0, N_SPLINE, upper=True)),
        (3, 0, surface_points(0.5, 0.0, N_SPLINE, upper=False)),
        (1, 3, surface_points(1.0, 0.5, N_SPLINE, upper=False)),
    ]:
        spline_edges.append((v0, v1, pts, -Z_HALF))
        spline_edges.append((v0 + nz, v1 + nz, pts, Z_HALF))

    # Nose-wrap arcs for the LE spokes (LE -> A / LE -> Al). A straight
    # vertical spoke would be nearly collinear with the airfoil spline at the
    # nose (surface tangent at the LE is vertical), giving ~0-degree block
    # corners and sliver cells. A circular arc centred at (Y/2, Y/2) with
    # radius Y/sqrt(2) leaves the LE at 135 deg, so both blocks meeting at
    # the LE get ~45-degree corners.
    r_arc = Y_FF / math.sqrt(2.0)
    arc_mid_up = (0.5 * Y_FF - r_arc, 0.5 * Y_FF)      # point on the arc
    arc_mid_lo = (0.5 * Y_FF - r_arc, -0.5 * Y_FF)
    arc_edges = [
        (0, 4, arc_mid_up, -Z_HALF),
        (0 + nz, 4 + nz, arc_mid_up, Z_HALF),
        (0, 5, arc_mid_lo, -Z_HALF),
        (0 + nz, 5 + nz, arc_mid_lo, Z_HALF),
    ]

    def face3d(a: int, b: int) -> str:
        """Quad face for 2D edge a->b extruded through z."""
        return f"({a} {b} {b + nz} {a + nz})"

    airfoil_faces = [face3d(0, 2), face3d(2, 1), face3d(3, 0), face3d(1, 3)]
    # Farfield split into inlet / outlet / topAndBottom — the classic robust
    # BC assignment for a close (~20-40c) farfield: fixedValue U +
    # zeroGradient p at the inlet, fixedValue p=0 + zeroGradient U at the
    # outlet, slip on top/bottom.
    inlet_faces = [face3d(10, 11), face3d(10, 12)]
    outlet_faces = [face3d(13, 14), face3d(13, 15)]
    top_bottom_faces = [
        face3d(11, 4), face3d(4, 6), face3d(6, 8),
        face3d(8, 17), face3d(17, 14),
        face3d(12, 5), face3d(5, 7), face3d(7, 9),
        face3d(9, 18), face3d(18, 15),
    ]
    front_back_faces = []
    for quad, _, _ in blocks:
        front_back_faces.append(
            f"({quad[0]} {quad[1]} {quad[2]} {quad[3]})")
        front_back_faces.append(
            f"({quad[0] + nz} {quad[1] + nz} {quad[2] + nz} {quad[3] + nz})")

    # ---- emit
    lines: list[str] = []
    add = lines.append
    add("/*--------------------------------*- C++ -*----------------------------------*\\")
    add("| =========                 |                                                 |")
    add("| \\\\      /  F ield         | OpenFOAM: The Open Source CFD Toolbox           |")
    add("|  \\\\    /   O peration     | Version:  v2312                                 |")
    add("|   \\\\  /    A nd           | Web:      www.openfoam.com                      |")
    add("|    \\\\/     M anipulation  |                                                 |")
    add("\\*---------------------------------------------------------------------------*/")
    add("FoamFile")
    add("{")
    add("    version     2.0;")
    add("    format      ascii;")
    add("    class       dictionary;")
    add("    object      blockMeshDict;")
    add("}")
    add("// * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * //")
    add("// Structured C-grid-style mesh for NACA 0012 (TMR altered definition,")
    add("// sharp TE), alpha = 0, Re = 6e6. Generated by gen_mesh.py — do not edit")
    add("// by hand; regenerate with `python3 gen_mesh.py`.")
    add("//")
    add(f"// Farfield: x in [{-X_UP:g}, {X_OUT:g}], y in +/-{Y_FF:g} (chords).")
    add(f"// First wall cell {D_WALL:g} c (y+ ~ 65, wall-function regime).")
    add("")
    add("scale   1;")
    add("")
    add("vertices")
    add("(")
    for z in (-Z_HALF, Z_HALF):
        for x, y in pts2d:
            add(f"    {fmt_pt((x, y, z))}")
    add(");")
    add("")
    add("blocks")
    add("(")
    for quad, counts, grading in blocks:
        v3d = quad + tuple(v + nz for v in quad)
        add(
            f"    hex ({' '.join(str(v) for v in v3d)})"
            f" ({counts[0]} {counts[1]} {counts[2]})"
            f" simpleGrading ({grading[0]:.6g} {grading[1]:.6g} {grading[2]:g})"
        )
    add(");")
    add("")
    add("edges")
    add("(")
    for v0, v1, mid, z in arc_edges:
        # arc through-point syntax; no trailing semicolon (see below).
        add(f"    arc {v0} {v1} {fmt_pt((mid[0], mid[1], z))}")
    for v0, v1, pts, z in spline_edges:
        # NOTE: entries inside edges() take NO trailing semicolon (blockMesh
        # list syntax) — a ';' here is a FATAL parse error.
        add(f"    spline {v0} {v1}")
        add("    (")
        for x, y in pts:
            add(f"        {fmt_pt((x, y, z))}")
        add("    )")
    add(");")
    add("")
    add("boundary")
    add("(")
    add("    airfoil")
    add("    {")
    add("        type wall;")
    add("        faces")
    add("        (")
    for f in airfoil_faces:
        add(f"            {f}")
    add("        );")
    add("    }")
    add("    inlet")
    add("    {")
    add("        type patch;")
    add("        faces")
    add("        (")
    for f in inlet_faces:
        add(f"            {f}")
    add("        );")
    add("    }")
    add("    outlet")
    add("    {")
    add("        type patch;")
    add("        faces")
    add("        (")
    for f in outlet_faces:
        add(f"            {f}")
    add("        );")
    add("    }")
    add("    topAndBottom")
    add("    {")
    add("        type patch;")
    add("        faces")
    add("        (")
    for f in top_bottom_faces:
        add(f"            {f}")
    add("        );")
    add("    }")
    add("    frontAndBack")
    add("    {")
    add("        type empty;")
    add("        faces")
    add("        (")
    for f in front_back_faces:
        add(f"            {f}")
    add("        );")
    add("    }")
    add(");")
    add("")
    add("mergePatchPairs")
    add("(")
    add(");")
    add("")
    add("// ************************************************************************* //")
    return "\n".join(lines) + "\n"


if __name__ == "__main__":
    out = Path(__file__).parent / "system" / "blockMeshDict"
    out.parent.mkdir(parents=True, exist_ok=True)
    text = build_dict()
    out.write_text(text, encoding="utf-8")
    # recompute the near/far wake split for the summary line
    r_wn = D_WAKE_MID / D_TE_WAKE
    rr = r_wn ** (1.0 / (N_WAKE_NEAR - 1))
    x_split = 1.0 + D_TE_WAKE * (rr ** N_WAKE_NEAR - 1.0) / (rr - 1.0)
    n_wake_far = max(1, round((X_OUT - x_split) / D_WAKE_MID))
    n_cells = (
        (N_UP + N_CHORD_FWD + N_CHORD_AFT + N_WAKE_NEAR + n_wake_far)
        * N_RADIAL * 2
    )
    print(f"wrote {out}")
    print(f"cells: {n_cells}  (near/far wake split at x = {x_split:.2f}c, "
          f"far-wake cells {n_wake_far})")
    print(f"yt(0.5) = {yt(0.5):.6f}  (max half-thickness ~0.0595 at x~0.3)")
