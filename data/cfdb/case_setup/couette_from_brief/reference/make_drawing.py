#!/usr/bin/env python3
"""Generate visible/drawing.png for couette_from_brief.

Annotated schematic of the planar Couette channel: gap H = 0.01 m,
periodic streamwise length L = 0.01 m, stationary bottom wall, top wall
moving at U_lid = 0.1 m/s, and the wall-to-wall sample line. Every
annotated number MUST match the engineering brief (visible/task.md) —
the drawing is part of the frozen visible/ task surface.

English-only annotations (academic default font) so the asset renders
identically on hosts without CJK fonts.

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

H = 0.01  # m, gap height (y)
L = 0.01  # m, periodic streamwise length (x)
U_LID = 0.1  # m/s, moving-wall speed

CASE_DIR = Path(__file__).resolve().parent.parent
OUT = CASE_DIR / "visible" / "drawing.png"


def main() -> None:
    fig, ax = plt.subplots(figsize=(8, 5.2), dpi=150)

    # Channel body (drawing units: metres, equal aspect).
    ax.add_patch(
        Rectangle((0, 0), L, H, facecolor="#eaf3fb", edgecolor="none", zorder=0)
    )

    # Walls (thick lines with hatching).
    ax.plot([0, L], [H, H], color="black", lw=3, solid_capstyle="butt")
    ax.plot([0, L], [0, 0], color="black", lw=3, solid_capstyle="butt")
    for x in [i * L / 20 for i in range(21)]:
        ax.plot([x, x - 0.0008], [H, H + 0.0005], color="black", lw=0.8)
        ax.plot([x, x - 0.0008], [0, -0.0005], color="black", lw=0.8)

    # Moving-wall velocity arrow above the top wall.
    ax.annotate("", xy=(L * 0.62, H + 0.0016), xytext=(L * 0.30, H + 0.0016),
                arrowprops=dict(arrowstyle="-|>", color="#d62728", lw=2.2))
    ax.text(L * 0.46, H + 0.0024, "moving wall  U_lid = 0.1 m/s",
            ha="center", fontsize=10, color="#d62728")
    ax.text(L * 0.5, -0.0016, "stationary wall (no-slip)",
            ha="center", fontsize=10)

    # Periodic streamwise boundaries.
    ax.plot([0, 0], [0, H], color="#1f77b4", lw=2, ls="--")
    ax.plot([L, L], [0, H], color="#1f77b4", lw=2, ls="--")
    ax.text(-0.0006, H * 0.5, "periodic", rotation=90, va="center",
            ha="right", color="#1f77b4", fontsize=9)
    ax.text(L + 0.0006, H * 0.5, "periodic", rotation=270, va="center",
            ha="right", color="#1f77b4", fontsize=9)

    # Developed linear profile hint (dashed) inside the channel.
    ys = [H * i / 40 for i in range(41)]
    prof = [L * 0.72 + 0.0022 * (y / H) for y in ys]
    ax.plot(prof, ys, color="#d62728", lw=1.3, ls="--")

    # Sample line (wall to wall).
    x_s = L * 0.45
    ax.plot([x_s, x_s], [0, H], color="#2ca02c", lw=1.8)
    for i in range(11):
        y = H * i / 10
        ax.plot(x_s, y, marker="o", ms=3, color="#2ca02c")
    ax.text(x_s + 0.0006, H * 0.18, "sample line\n(wall to wall,\n>= 10 points)",
            fontsize=9, color="#2ca02c", va="bottom")

    # Dimension: L (below).
    y_dim = -0.0032
    ax.annotate("", xy=(L, y_dim), xytext=(0, y_dim),
                arrowprops=dict(arrowstyle="<->", color="black", lw=1.2))
    ax.plot([0, 0], [y_dim - 0.0004, 0], color="black", lw=0.7, ls=":")
    ax.plot([L, L], [y_dim - 0.0004, 0], color="black", lw=0.7, ls=":")
    ax.text(L / 2, y_dim - 0.0008, "L = 0.01 m (periodic)", ha="center",
            va="top", fontsize=10)

    # Dimension: H (left).
    x_dim = -0.0035
    ax.annotate("", xy=(x_dim, H), xytext=(x_dim, 0),
                arrowprops=dict(arrowstyle="<->", color="black", lw=1.2))
    ax.plot([x_dim - 0.0004, 0], [0, 0], color="black", lw=0.7, ls=":")
    ax.plot([x_dim - 0.0004, 0], [H, H], color="black", lw=0.7, ls=":")
    ax.text(x_dim - 0.0009, H / 2, "H = 0.01 m", rotation=90, va="center",
            ha="center", fontsize=10)

    # Fluid annotation.
    ax.text(L * 0.22, H * 0.62,
            "incompressible laminar flow\nnu = 5e-5 m^2/s   Re_H = 20",
            ha="center", va="center", fontsize=10)

    # Axes hints.
    ax.annotate("x", xy=(0.0022, -0.0012), xytext=(0.0004, -0.0012),
                arrowprops=dict(arrowstyle="->", lw=1), fontsize=10)
    ax.annotate("y", xy=(-0.0016, 0.0010), xytext=(-0.0016, -0.0012),
                arrowprops=dict(arrowstyle="->", lw=1), fontsize=10)

    ax.set_xlim(-0.0072, L + 0.0035)
    ax.set_ylim(-0.005, H + 0.0036)
    ax.set_aspect("equal")
    ax.axis("off")
    ax.set_title("Planar Couette flow (2D) — case setup from engineering brief",
                 fontsize=12, pad=10)

    OUT.parent.mkdir(parents=True, exist_ok=True)
    fig.savefig(OUT, bbox_inches="tight")
    print(f"wrote {OUT}")


if __name__ == "__main__":
    main()
