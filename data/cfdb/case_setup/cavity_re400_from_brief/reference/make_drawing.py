#!/usr/bin/env python3
"""Generate visible/drawing.png for cavity_re400_from_brief.

Annotated schematic of the 2D lid-driven cavity: side H = 0.1 m, lid
velocity U_lid = 1.0 m/s, stationary no-slip walls, and the vertical
centerline sample line (x = H/2, up to y/H = 0.95). Every annotated
number MUST match the engineering brief (visible/task.md) and the golden
configuration inherited from cases/validation/lid_driven_cavity_re400 —
the drawing is part of the frozen visible/ task surface.

Host-side authoring tool (matplotlib); NOT part of the scoring path —
the frozen QoI script is reference/compute_qoi.py (stdlib-only).

Run:  python3 reference/make_drawing.py
"""

from __future__ import annotations

from pathlib import Path

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib.patches import Rectangle

H = 0.1  # m, cavity side
U_LID = 1.0  # m/s, lid velocity
NU = 2.5e-4  # m^2/s, kinematic viscosity
X_LINE = 0.05  # m, vertical centerline x = H/2
Y_TOP = 0.095  # m, sample line top y/H = 0.95

CASE_DIR = Path(__file__).resolve().parent.parent
OUT = CASE_DIR / "visible" / "drawing.png"


def main() -> None:
    fig, ax = plt.subplots(figsize=(7.2, 6.4), dpi=150)

    # Cavity body (drawing units: metres, equal aspect).
    ax.add_patch(
        Rectangle((0, 0), H, H, facecolor="#eaf3fb", edgecolor="none", zorder=0)
    )

    # Walls: bottom + sides stationary (thick with hatch marks), top = lid.
    for a, b, hatch in (
        ((0, 0), (H, 0), (0, -0.004)),
        ((0, 0), (0, H), (-0.004, 0)),
        ((H, 0), (H, H), (0.004, 0)),
    ):
        ax.plot([a[0], b[0]], [a[1], b[1]], color="black", lw=3,
                solid_capstyle="butt")
        for i in range(17):
            t = i * H / 16
            if a[0] == b[0]:  # vertical wall
                ax.plot([a[0], a[0] + hatch[0]], [t, t + hatch[1]],
                        color="black", lw=0.8)
            else:  # horizontal wall
                ax.plot([t, t + hatch[0]], [a[1], a[1] + hatch[1]],
                        color="black", lw=0.8)
    ax.plot([0, H], [H, H], color="#d62728", lw=3, solid_capstyle="butt")

    # Lid motion arrow.
    ax.annotate("", xy=(0.75 * H, H + 0.012), xytext=(0.25 * H, H + 0.012),
                arrowprops=dict(arrowstyle="-|>", color="#d62728", lw=2))
    ax.text(0.5 * H, H + 0.017, f"lid: U = ({U_LID} m/s, 0)",
            ha="center", fontsize=10, color="#d62728")
    ax.text(-0.014, 0.5 * H, "stationary no-slip walls", rotation=90,
            va="center", ha="center", fontsize=10)

    # Centerline sample line with stations.
    ax.plot([X_LINE, X_LINE], [0, Y_TOP], color="#1f77b4", lw=1.8)
    for i in range(19):
        y = 0.005 + i * 0.005
        ax.plot(X_LINE, y, marker="o", ms=3, color="#1f77b4")
    ax.annotate("sample line\nx = H/2 = 0.05 m\ny up to y/H = 0.95",
                xy=(X_LINE, 0.028), xytext=(0.06, 0.006), fontsize=9,
                color="#1f77b4", ha="left", va="center",
                arrowprops=dict(arrowstyle="->", color="#1f77b4", lw=1))

    # Primary vortex hint (schematic streamlines ellipse).
    theta = [i * 6.283185307 / 60 for i in range(61)]
    ax.plot([0.5 * H + 0.02 * __import__("math").cos(t) for t in theta],
            [0.58 * H + 0.014 * __import__("math").sin(t) for t in theta],
            color="grey", lw=0.9, ls="--")

    # Dimension: H (bottom).
    y_dim = -0.012
    ax.annotate("", xy=(H, y_dim), xytext=(0, y_dim),
                arrowprops=dict(arrowstyle="<->", color="black", lw=1.2))
    ax.plot([0, 0], [y_dim - 0.003, 0], color="black", lw=0.7, ls=":")
    ax.plot([H, H], [y_dim - 0.003, 0], color="black", lw=0.7, ls=":")
    ax.text(0.5 * H, y_dim - 0.006, "H = 0.1 m", ha="center", va="top",
            fontsize=10)

    # Dimension: H (left).
    x_dim = -0.024
    ax.annotate("", xy=(x_dim, H), xytext=(x_dim, 0),
                arrowprops=dict(arrowstyle="<->", color="black", lw=1.2))
    ax.plot([x_dim - 0.004, 0], [0, 0], color="black", lw=0.7, ls=":")
    ax.plot([x_dim - 0.004, 0], [H, H], color="black", lw=0.7, ls=":")
    ax.text(x_dim - 0.008, 0.5 * H, "H = 0.1 m", rotation=90, va="center",
            ha="center", fontsize=10)

    # Fluid annotation.
    ax.text(0.5 * H, 0.3 * H,
            "incompressible laminar flow\n"
            "nu = 2.5e-4 m$^2$/s\n"
            "Re = U$_{lid}$ H / nu = 400",
            ha="center", va="center", fontsize=10)

    # Axes hints at the origin.
    ax.annotate("x", xy=(0.018, -0.028), xytext=(0.002, -0.028),
                arrowprops=dict(arrowstyle="->", lw=1), fontsize=10)
    ax.annotate("y", xy=(-0.01, 0.016), xytext=(-0.01, -0.028),
                arrowprops=dict(arrowstyle="->", lw=1), fontsize=10)

    ax.set_xlim(-0.045, H + 0.02)
    ax.set_ylim(-0.035, H + 0.028)
    ax.set_aspect("equal")
    ax.axis("off")
    ax.set_title("Lid-driven cavity (2D) — Re = 400 case setup",
                 fontsize=12, pad=10)

    OUT.parent.mkdir(parents=True, exist_ok=True)
    fig.savefig(OUT, bbox_inches="tight")
    print(f"wrote {OUT}")


if __name__ == "__main__":
    main()
