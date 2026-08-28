#!/usr/bin/env python3
"""Generate visible/drawing.png for the cavity_from_brief case_setup task.

Annotated geometry drawing of the lid-driven cavity: 0.1 m x 0.1 m square,
lid velocity U_lid = 1 m/s on the top wall, no-slip on the other three
walls, and the vertical centerline probe line at x = 0.05 m. All
dimensions match the golden configuration (32x32x1 blockMesh, nu = 1e-3,
icoFoam to t = 5 s; see case.yaml description).

Run ON THE HOST with matplotlib available (this script is case-authoring
material, not judge material — the stdlib-only constraint applies to
reference/compute_qoi.py, the frozen QoI script):

    python3 reference/make_drawing.py

Case-authoring tool; deterministic output for a fixed matplotlib version.
"""

from pathlib import Path

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib.patches import FancyArrowPatch, Rectangle

OUT = Path(__file__).resolve().parent.parent / "visible" / "drawing.png"

L = 0.1  # m, cavity side (matches golden blockMeshDict vertices)

fig, ax = plt.subplots(figsize=(7, 7))

# Cavity outline
ax.add_patch(
    Rectangle((0, 0), L, L, fill=True, facecolor="#eaf3fb",
              edgecolor="black", linewidth=2.5, zorder=1)
)

# Lid velocity arrows on the top wall
for x in (0.02, 0.05, 0.08):
    ax.add_patch(
        FancyArrowPatch((x, L), (x + 0.018, L), arrowstyle="-|>",
                        mutation_scale=22, linewidth=2.2, color="#c0392b",
                        zorder=3)
    )
ax.text(0.05, L + 0.011, r"lid: $U_{lid}=1$ m/s ($+x$)",
        ha="center", va="bottom", fontsize=13, color="#c0392b")

# No-slip wall labels
ax.text(-0.008, 0.05, "no-slip wall", rotation=90, ha="right", va="center",
        fontsize=11)
ax.text(L + 0.008, 0.05, "no-slip wall", rotation=-90, ha="left",
        va="center", fontsize=11)
ax.text(0.05, -0.012, "no-slip wall", ha="center", va="top", fontsize=11)

# Vertical centerline probe line (x = 0.05, up to y/H = 0.95)
ax.plot([0.05, 0.05], [0, 0.095], linestyle="--", linewidth=1.8,
        color="#2471a3", zorder=2)
ax.plot(0.05, 0.095, marker="o", markersize=5, color="#2471a3", zorder=2)
ax.text(0.053, 0.055, "probe line:\nvertical centerline\n$x=0.05$ m, "
        "up to $y/H=0.95$", ha="left", va="center", fontsize=11,
        color="#2471a3")

# Dimension annotations
ax.annotate("", xy=(0, -0.03), xytext=(L, -0.03),
            arrowprops=dict(arrowstyle="<->", linewidth=1.4))
ax.text(0.05, -0.037, "L = 0.1 m", ha="center", va="top", fontsize=12)
ax.annotate("", xy=(-0.028, 0), xytext=(-0.028, L),
            arrowprops=dict(arrowstyle="<->", linewidth=1.4))
ax.text(-0.035, 0.05, "H = 0.1 m", rotation=90, ha="right", va="center",
        fontsize=12)

# Fluid / solver annotation inside the cavity
ax.text(0.028, 0.028, "incompressible, laminar\n"
        r"$\nu = 10^{-3}$ m$^2$/s" "\n"
        r"$Re = U_{lid}L/\nu = 100$" "\n"
        "icoFoam, t: 0 → 5 s",
        ha="left", va="center", fontsize=11,
        bbox=dict(boxstyle="round,pad=0.4", facecolor="white",
                  edgecolor="#888888"))

# Axis ticks in metres for scale reference
ax.set_xticks([0, 0.02, 0.04, 0.06, 0.08, 0.1])
ax.set_yticks([0, 0.02, 0.04, 0.06, 0.08, 0.1])
ax.tick_params(labelsize=9)
ax.set_xlabel("x [m]", fontsize=11)
ax.set_ylabel("y [m]", fontsize=11)
ax.set_title("Lid-Driven Cavity, Re = 100 — geometry & boundary conditions",
             fontsize=13, pad=14)

ax.set_xlim(-0.055, 0.16)
ax.set_ylim(-0.055, 0.135)
ax.set_aspect("equal")
fig.tight_layout()
fig.savefig(OUT, dpi=150)
print(f"wrote {OUT}")
