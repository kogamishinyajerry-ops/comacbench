#!/usr/bin/env python3
"""Generate visible/drawing.png for cylinder_from_drawing (任务3).

Schematic (NOT to scale — the far-field radius is 100x the cylinder
radius) of the 2D external-flow domain, matching the golden geometry in
cases/validation/cylinder_re40/constant/polyMesh/blockMeshDict exactly:

  - cylinder: diameter D = 1 m (radius 0.5 m), centred at the origin;
  - far field: circle of radius R = 50 m (= 50 D, domain diameter 100 D);
  - boundaries: cylinder = no-slip wall; far field = freestream
    (U_inf = 1 m/s along +x); front/back = empty (2D, unit depth 1 m).

Labels are English-only so the PNG renders identically on any host
(the judge-side fonts ship no CJK glyphs).

Run: ``python3 make_drawing.py`` from this directory (needs matplotlib;
regenerate whenever the golden geometry changes).
"""

from __future__ import annotations

import math
from pathlib import Path

import matplotlib

matplotlib.use("Agg")

import matplotlib.pyplot as plt
from matplotlib.patches import Circle, FancyArrowPatch

OUT = Path(__file__).resolve().parent.parent / "visible" / "drawing.png"

fig, ax = plt.subplots(figsize=(8, 8))

# Far-field boundary (schematic radius; true proportion 50 : 0.5 would
# make the cylinder invisible, so the drawing is labelled not-to-scale).
R_DRAW = 5.0
R_CYL_DRAW = 0.9

farfield = Circle((0, 0), R_DRAW, fill=True, facecolor="#eaf3fb",
                  edgecolor="#1f6fb2", linewidth=2.2, zorder=1)
ax.add_patch(farfield)
cylinder = Circle((0, 0), R_CYL_DRAW, facecolor="#d9d9d9",
                  edgecolor="#333333", linewidth=2.2, zorder=3)
ax.add_patch(cylinder)

# Centrelines through the origin.
ax.axhline(0, color="#888888", linestyle="--", linewidth=0.9, zorder=2)
ax.axvline(0, color="#888888", linestyle="--", linewidth=0.9, zorder=2)
ax.plot(0, 0, marker="+", color="#333333", markersize=10, zorder=4)

# Inflow arrow (U_inf along +x).
ax.add_patch(FancyArrowPatch((-R_DRAW + 0.35, 2.9), (-1.9, 2.9),
                             arrowstyle="-|>", mutation_scale=26,
                             linewidth=2.4, color="#c0392b", zorder=5))
ax.text(-3.6, 3.25, r"$U_\infty$ = 1 m/s", fontsize=13, color="#c0392b",
        ha="center")

# Cylinder diameter annotation (double arrow across the cylinder).
ax.annotate("", xy=(R_CYL_DRAW, -1.45), xytext=(-R_CYL_DRAW, -1.45),
            arrowprops=dict(arrowstyle="<->", color="#333333", lw=1.6))
ax.plot([-R_CYL_DRAW, -R_CYL_DRAW], [-R_CYL_DRAW, -1.55], color="#333333",
        lw=0.9, linestyle=":")
ax.plot([R_CYL_DRAW, R_CYL_DRAW], [-R_CYL_DRAW, -1.55], color="#333333",
        lw=0.9, linestyle=":")
ax.text(0, -1.85, "D = 1 m", fontsize=13, ha="center", color="#333333")

# Far-field radius annotation (radial double arrow, 45 deg).
c = math.cos(math.radians(45))
s = math.sin(math.radians(45))
ax.annotate("", xy=(R_DRAW * c, R_DRAW * s), xytext=(0, 0),
            arrowprops=dict(arrowstyle="<->", color="#1f6fb2", lw=1.6))
ax.text(2.6, 2.05, "R = 50 m (= 50 D)\nfar-field radius", fontsize=12,
        color="#1f6fb2", ha="center")

# Labels.
ax.text(0, 0.28, "cylinder\n(at origin O)", fontsize=11, ha="center",
        zorder=6, color="#333333")
ax.text(0, 4.3, "far-field boundary: freestream\n(cylinder wall: no-slip)",
        fontsize=12, ha="center", color="#1f6fb2")
ax.text(0, -4.5, "2D case, unit spanwise depth dz = 1 m\nfront/back faces: empty",
        fontsize=12, ha="center", color="#555555")

ax.text(0, -5.6, "schematic, not to scale: R / D = 50",
        fontsize=10, ha="center", color="#999999")

ax.set_xlim(-6.2, 6.2)
ax.set_ylim(-6.0, 6.0)
ax.set_aspect("equal")
ax.set_xlabel("x", fontsize=12)
ax.set_ylabel("y", fontsize=12)
ax.set_title(r"Flow past a circular cylinder (Re = $U_\infty$D/$\nu$ = 40, steady laminar)",
             fontsize=13)

OUT.parent.mkdir(parents=True, exist_ok=True)
fig.savefig(OUT, dpi=150, bbox_inches="tight")
print(f"wrote {OUT}")
