#!/usr/bin/env python3
"""Generate visible/drawing.png for backward_step_from_brief.

Annotated schematic of the 2D laminar backward-facing step: step height
h = 0.01 m, expansion ratio ER = 2, inlet channel 5h, downstream 30h,
parabolic inlet profile (mean Um = 1.0 m/s), and the bottom-wall shear
sampling extent. Every annotated number MUST match the engineering brief
(visible/task.md) and the golden configuration inherited from
cases/validation/backward_facing_step_laminar — the drawing is part of
the frozen visible/ task surface.

The vertical axis is exaggerated (x and y NOT to the same scale) so the
step and the recirculation zone stay readable over the 35h-long domain.

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
from matplotlib.patches import Polygon

H = 0.01  # m, step height
X_IN = -0.05  # m, inlet at x = -5h
X_OUT = 0.30  # m, outlet at x = 30h
UM = 1.0  # m/s, mean inlet velocity

SY = 6.0  # vertical exaggeration (drawing only)


def sy(y: float) -> float:
    return y * SY


CASE_DIR = Path(__file__).resolve().parent.parent
OUT = CASE_DIR / "visible" / "drawing.png"


def main() -> None:
    fig, ax = plt.subplots(figsize=(12, 4.6), dpi=150)

    # Fluid domain polygon.
    poly = Polygon(
        [(X_IN, sy(H)), (X_IN, sy(2 * H)), (X_OUT, sy(2 * H)),
         (X_OUT, sy(0)), (0, sy(0)), (0, sy(H))],
        closed=True, facecolor="#eaf3fb", edgecolor="none", zorder=0,
    )
    ax.add_patch(poly)

    # Walls.
    ax.plot([X_IN, 0], [sy(H), sy(H)], color="black", lw=2.5)
    ax.plot([0, 0], [sy(0), sy(H)], color="black", lw=2.5)
    ax.plot([0, X_OUT], [sy(0), sy(0)], color="black", lw=2.5)
    ax.plot([X_IN, X_OUT], [sy(2 * H), sy(2 * H)], color="black", lw=2.5)
    ax.text(0.5 * X_IN, sy(H) - 0.012, "no-slip walls", ha="center",
            va="top", fontsize=9)
    ax.text(0.17, sy(2 * H) + 0.014, "no-slip wall", ha="center", fontsize=9)
    ax.text(0.17, sy(0) - 0.016, "bottom wall: sample tau_w(x) here",
            ha="center", va="top", fontsize=9, color="#1f77b4")

    # Inlet parabolic profile (fully developed, mean Um).
    ys = [H + H * i / 40 for i in range(41)]
    prof = [X_IN + 0.018 * (6 * UM * ((y - H) / H) * (1 - (y - H) / H)) / (1.5 * UM)
            for y in ys]
    ax.plot(prof, [sy(y) for y in ys], color="#1f77b4", lw=1.6)
    ax.plot([X_IN, X_IN], [sy(H), sy(2 * H)], color="#1f77b4", lw=2)
    ax.annotate("inlet x = -5h: parabolic profile\n(fully developed, mean Um = 1.0 m/s)",
                xy=(X_IN + 0.002, sy(1.5 * H)), xytext=(-0.048, sy(2 * H) + 0.052),
                fontsize=9, color="#1f77b4", ha="left",
                arrowprops=dict(arrowstyle="->", color="#1f77b4", lw=1))

    # Outlet.
    ax.plot([X_OUT, X_OUT], [sy(0), sy(2 * H)], color="#2ca02c", lw=2)
    ax.text(X_OUT, sy(2 * H) + 0.014, "outlet x = 30h", ha="center",
            fontsize=9, color="#2ca02c")

    # Recirculation bubble hint (schematic, elongated along the wall).
    theta = [i * 2 * math.pi / 60 for i in range(61)]
    ax.plot([0.0145 + 0.0130 * math.cos(t) for t in theta],
            [sy(0) + 0.020 + 0.017 * math.sin(t) for t in theta],
            color="grey", lw=0.9, ls="--")
    ax.annotate("recirculation bubble\nx_r: tau_w zero crossing (- to +)",
                xy=(0.028, sy(0) + 0.006), xytext=(0.055, sy(H) + 0.03),
                fontsize=9, color="dimgrey",
                arrowprops=dict(arrowstyle="->", color="dimgrey", lw=1))

    # Dimension: step height h (at the step face).
    ax.annotate("", xy=(0.009, sy(H)), xytext=(0.009, sy(0)),
                arrowprops=dict(arrowstyle="<->", color="black", lw=1.1))
    ax.text(0.013, sy(0.5 * H), "h = 0.01 m", fontsize=9, va="center")

    # Dimension: downstream channel height 2h.
    ax.annotate("", xy=(X_OUT + 0.012, sy(2 * H)), xytext=(X_OUT + 0.012, sy(0)),
                arrowprops=dict(arrowstyle="<->", color="black", lw=1.1))
    ax.text(X_OUT + 0.017, sy(H), "2h", fontsize=9, va="center")

    # Dimension: inlet channel height h (left).
    ax.annotate("", xy=(X_IN - 0.012, sy(2 * H)), xytext=(X_IN - 0.012, sy(H)),
                arrowprops=dict(arrowstyle="<->", color="black", lw=1.1))
    ax.text(X_IN - 0.017, sy(1.5 * H), "h", fontsize=9, va="center", ha="right")

    # Dimension: downstream length 30h (below).
    y_dim = sy(0) - 0.055
    ax.annotate("", xy=(X_OUT, y_dim), xytext=(0, y_dim),
                arrowprops=dict(arrowstyle="<->", color="black", lw=1.1))
    ax.plot([0, 0], [y_dim - 0.012, sy(0)], color="black", lw=0.7, ls=":")
    ax.plot([X_OUT, X_OUT], [y_dim - 0.012, sy(0)], color="black", lw=0.7, ls=":")
    ax.text(0.5 * X_OUT, y_dim - 0.012, "30h", ha="center", va="top", fontsize=9)

    # Dimension: upstream length 5h (above).
    ax.annotate("", xy=(0, sy(2 * H) + 0.038), xytext=(X_IN, sy(2 * H) + 0.038),
                arrowprops=dict(arrowstyle="<->", color="black", lw=1.1))
    ax.text(0.5 * X_IN, sy(2 * H) + 0.046, "5h", ha="center", fontsize=9)

    # Fluid annotation.
    ax.text(0.205, sy(1.35 * H),
            "incompressible laminar, steady\n"
            "nu = 2.0e-4 m$^2$/s\n"
            "Re = Um D$_h$ / nu = 100 (D$_h$ = 2h)",
            ha="center", va="center", fontsize=10)

    # Axes hints.
    ax.annotate("x", xy=(-0.033, y_dim), xytext=(-0.045, y_dim),
                arrowprops=dict(arrowstyle="->", lw=1), fontsize=9)
    ax.annotate("y", xy=(-0.05, y_dim + 0.02), xytext=(-0.05, y_dim),
                arrowprops=dict(arrowstyle="->", lw=1), fontsize=9)
    ax.text(-0.05, y_dim - 0.014, "(y exaggerated)", fontsize=7.5,
            color="grey", ha="left", va="top")

    ax.set_xlim(X_IN - 0.03, X_OUT + 0.03)
    ax.set_ylim(y_dim - 0.03, sy(2 * H) + 0.1)
    ax.axis("off")
    ax.set_title("Backward-facing step (2D) — laminar Re = 100, expansion ratio 1:2",
                 fontsize=12, pad=8)

    OUT.parent.mkdir(parents=True, exist_ok=True)
    fig.savefig(OUT, bbox_inches="tight")
    print(f"wrote {OUT}")


if __name__ == "__main__":
    main()
