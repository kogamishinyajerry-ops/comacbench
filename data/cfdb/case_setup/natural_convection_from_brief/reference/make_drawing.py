#!/usr/bin/env python3
"""Generate visible/drawing.png for natural_convection_from_brief.

Annotated schematic of the 2D differentially heated square cavity: side
H = 1 m, hot wall (x = 0) at 293 K, cold wall (x = 1) at 283 K,
adiabatic top/bottom, gravity downward, and the hot-wall heat flux
sampling extent. Every annotated number MUST match the engineering brief
(visible/task.md) and the golden configuration inherited from
cases/validation/natural_convection_cavity — the drawing is part of the
frozen visible/ task surface.

Host-side authoring tool (matplotlib); NOT part of the scoring path —
the frozen QoI script is reference/compute_qoi.py (stdlib-only).

Run:  python3 reference/make_drawing.py
"""

from __future__ import annotations

import math
from pathlib import Path

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib.patches import Rectangle

H = 1.0  # m, cavity side
T_HOT = 293.0  # K
T_COLD = 283.0  # K

CASE_DIR = Path(__file__).resolve().parent.parent
OUT = CASE_DIR / "visible" / "drawing.png"


def main() -> None:
    fig, ax = plt.subplots(figsize=(7.4, 6.6), dpi=150)

    # Cavity body.
    ax.add_patch(
        Rectangle((0, 0), H, H, facecolor="#f6f0e6", edgecolor="none", zorder=0)
    )

    # Walls: hot (left), cold (right), adiabatic top/bottom.
    ax.plot([0, 0], [0, H], color="#d62728", lw=4, solid_capstyle="butt")
    ax.plot([H, H], [0, H], color="#1f77b4", lw=4, solid_capstyle="butt")
    ax.plot([0, H], [H, H], color="black", lw=2.5, solid_capstyle="butt")
    ax.plot([0, H], [0, 0], color="black", lw=2.5, solid_capstyle="butt")
    ax.text(-0.04, 0.5 * H, f"hot wall: T = {T_HOT:.0f} K", rotation=90,
            va="center", ha="center", fontsize=10, color="#d62728")
    ax.text(H + 0.04, 0.5 * H, f"cold wall: T = {T_COLD:.0f} K", rotation=270,
            va="center", ha="center", fontsize=10, color="#1f77b4")
    ax.text(0.5 * H, H + 0.035, "adiabatic", ha="center", fontsize=10)
    ax.text(0.5 * H, -0.05, "adiabatic", ha="center", fontsize=10)

    # Gravity arrow.
    ax.annotate("", xy=(0.82 * H, 0.06 * H), xytext=(0.82 * H, 0.2 * H),
                arrowprops=dict(arrowstyle="-|>", color="black", lw=1.8))
    ax.text(0.85 * H, 0.13 * H, "g = 9.81 m/s$^2$", fontsize=10, va="center")

    # Schematic circulation (fluid rises at the hot wall, sinks at the cold).
    theta = [i * 2 * math.pi / 80 for i in range(81)]
    ax.plot([0.5 * H + 0.3 * H * math.cos(t) for t in theta],
            [0.5 * H + 0.3 * H * math.sin(t) for t in theta],
            color="grey", lw=0.9, ls="--")
    ax.annotate("", xy=(0.2 * H + 0.02, 0.66 * H), xytext=(0.2 * H - 0.02, 0.5 * H),
                arrowprops=dict(arrowstyle="-|>", color="grey", lw=1.2))
    ax.annotate("", xy=(0.8 * H - 0.02, 0.34 * H), xytext=(0.8 * H + 0.02, 0.5 * H),
                arrowprops=dict(arrowstyle="-|>", color="grey", lw=1.2))

    # Hot-wall heat flux sampling hint.
    for i in range(16):
        y = H * (i + 0.5) / 16
        ax.plot(0.015, y, marker=">", ms=4, color="#d62728")
    ax.annotate("sample q(y) on the hot wall\n(full height, uniform stations)",
                xy=(0.03, 0.28 * H), xytext=(0.3 * H, 0.13 * H), fontsize=9,
                color="#d62728",
                arrowprops=dict(arrowstyle="->", color="#d62728", lw=1))

    # Dimension: H (bottom, below the adiabatic label).
    y_dim = -0.11
    ax.annotate("", xy=(H, y_dim), xytext=(0, y_dim),
                arrowprops=dict(arrowstyle="<->", color="black", lw=1.2))
    ax.plot([0, 0], [y_dim - 0.03, -0.02], color="black", lw=0.7, ls=":")
    ax.plot([H, H], [y_dim - 0.03, -0.02], color="black", lw=0.7, ls=":")
    ax.text(0.5 * H, y_dim - 0.045, "H = 1.0 m", ha="center", va="top",
            fontsize=10)

    # Dimension: H (left).
    x_dim = -0.13
    ax.annotate("", xy=(x_dim, H), xytext=(x_dim, 0),
                arrowprops=dict(arrowstyle="<->", color="black", lw=1.2))
    ax.plot([x_dim - 0.03, -0.02], [0, 0], color="black", lw=0.7, ls=":")
    ax.plot([x_dim - 0.03, -0.02], [H, H], color="black", lw=0.7, ls=":")
    ax.text(x_dim - 0.055, 0.5 * H, "H = 1.0 m", rotation=90, va="center",
            ha="center", fontsize=10)

    # Fluid annotation.
    ax.text(0.5 * H, 0.88 * H,
            "Boussinesq, laminar, steady\n"
            "Pr = 0.71,  Ra = 1.0e4",
            ha="center", va="center", fontsize=10)

    # Axes hints.
    ax.annotate("x", xy=(0.14, -0.2), xytext=(0.02, -0.2),
                arrowprops=dict(arrowstyle="->", lw=1), fontsize=10)
    ax.annotate("y", xy=(-0.04, -0.08), xytext=(-0.04, -0.2),
                arrowprops=dict(arrowstyle="->", lw=1), fontsize=10)

    ax.set_xlim(-0.24, H + 0.14)
    ax.set_ylim(-0.28, H + 0.08)
    ax.set_aspect("equal")
    ax.axis("off")
    ax.set_title("Differentially heated square cavity (2D) — natural convection",
                 fontsize=12, pad=10)

    OUT.parent.mkdir(parents=True, exist_ok=True)
    fig.savefig(OUT, bbox_inches="tight")
    print(f"wrote {OUT}")


if __name__ == "__main__":
    main()
