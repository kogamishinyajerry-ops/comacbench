#!/usr/bin/env python3
"""Generate visible/drawing.png for pipe_from_brief.

Annotated schematic of the straight circular pipe: radius R = 0.005 m,
length L = 0.12 m, plug inlet U_mean = 0.1 m/s, no-slip wall, and the
radial sample line at x = 0.1 m. Every annotated number MUST match the
engineering brief (visible/task.md) — the drawing is part of the frozen
visible/ task surface.

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

R = 0.005  # m, pipe radius
L = 0.12  # m, pipe length
U_MEAN = 0.1  # m/s, plug inlet velocity
X_SAMPLE = 0.1  # m, radial sample station

CASE_DIR = Path(__file__).resolve().parent.parent
OUT = CASE_DIR / "visible" / "drawing.png"


def main() -> None:
    # Drawing is a meridian half-section: axis at y=0, wall at y=R.
    fig, ax = plt.subplots(figsize=(11, 3.4), dpi=150)

    ax.add_patch(
        Rectangle((0, 0), L, R, facecolor="#eaf3fb", edgecolor="none", zorder=0)
    )

    # Wall (thick line with hatching) and axis (dash-dot).
    ax.plot([0, L], [R, R], color="black", lw=3, solid_capstyle="butt")
    for x in [i * L / 30 for i in range(31)]:
        ax.plot([x, x - 0.002], [R, R + 0.0009], color="black", lw=0.8)
    ax.text(L * 0.42, R + 0.0022, "wall (no-slip)", ha="center", fontsize=10)
    ax.plot([0, L], [0, 0], color="black", lw=1.2, ls="-.")
    ax.text(L * 0.5, -0.0016, "axis", ha="center", fontsize=9)

    # Inlet / outlet.
    ax.plot([0, 0], [0, R], color="#1f77b4", lw=2)
    ax.plot([L, L], [0, R], color="#2ca02c", lw=2)
    ax.text(-0.004, R * 0.5, "inlet", rotation=90, va="center", ha="right",
            color="#1f77b4", fontsize=10)
    ax.text(L + 0.004, R * 0.5, "outlet", rotation=270, va="center",
            ha="right", color="#2ca02c", fontsize=10)

    # Plug inlet velocity arrows.
    for y in [0.25 * R, 0.5 * R, 0.75 * R]:
        ax.annotate("", xy=(0.016, y), xytext=(0.004, y),
                    arrowprops=dict(arrowstyle="-|>", color="#1f77b4", lw=1.6))
    ax.text(0.010, R + 0.0022, f"U_mean = {U_MEAN} m/s (plug)",
            ha="center", fontsize=10, color="#1f77b4")

    # Developed parabolic profile hint near the sample station.
    ys = [R * i / 40 for i in range(41)]
    prof = [X_SAMPLE + 0.018 * (1 - (y / R) ** 2) for y in ys]
    ax.plot(prof, ys, color="#d62728", lw=1.4, ls="--")

    # Radial sample line at x = 0.1 m.
    ax.plot([X_SAMPLE, X_SAMPLE], [0, R], color="#d62728", lw=1.8)
    for i in range(10):
        y = R * (i + 0.5) / 10
        ax.plot(X_SAMPLE, y, marker="o", ms=3, color="#d62728")
    ax.plot(X_SAMPLE, R, marker="s", ms=5, color="#d62728")
    ax.text(X_SAMPLE, -0.0030, "radial sample line\nx = 0.1 m\n(incl. wall endpoint)",
            ha="center", va="top", fontsize=9, color="#d62728")

    # Dimension: L (below, offset under the sample-line label).
    y_dim = -0.0075
    ax.annotate("", xy=(L, y_dim), xytext=(0, y_dim),
                arrowprops=dict(arrowstyle="<->", color="black", lw=1.2))
    ax.plot([0, 0], [y_dim - 0.0008, 0], color="black", lw=0.7, ls=":")
    ax.plot([L, L], [y_dim - 0.0008, 0], color="black", lw=0.7, ls=":")
    ax.text(L * 0.32, y_dim - 0.0009, "L = 0.12 m (= 12D)", ha="center",
            va="top", fontsize=10)

    # Dimension: R (left).
    x_dim = -0.012
    ax.annotate("", xy=(x_dim, R), xytext=(x_dim, 0),
                arrowprops=dict(arrowstyle="<->", color="black", lw=1.2))
    ax.plot([x_dim - 0.0015, 0], [0, 0], color="black", lw=0.7, ls=":")
    ax.plot([x_dim - 0.0015, 0], [R, R], color="black", lw=0.7, ls=":")
    ax.text(x_dim - 0.0032, R / 2, "R = 0.005 m", rotation=90, va="center",
            ha="center", fontsize=10)

    # Fluid annotation.
    ax.text(L * 0.66, R * 0.55,
            "incompressible laminar pipe flow\nnu = 5e-5 m^2/s   Re_D = 20",
            ha="center", va="center", fontsize=10)

    # Axes hints.
    ax.annotate("x", xy=(0.012, -0.0022), xytext=(0.002, -0.0022),
                arrowprops=dict(arrowstyle="->", lw=1), fontsize=10)
    ax.annotate("r", xy=(-0.004, 0.0018), xytext=(-0.004, -0.0022),
                arrowprops=dict(arrowstyle="->", lw=1), fontsize=10)

    ax.set_xlim(-0.024, L + 0.014)
    ax.set_ylim(-0.011, R + 0.005)
    ax.set_aspect("equal")
    ax.axis("off")
    ax.set_title("Circular pipe — Hagen-Poiseuille laminar flow case setup",
                 fontsize=12, pad=10)

    OUT.parent.mkdir(parents=True, exist_ok=True)
    fig.savefig(OUT, bbox_inches="tight")
    print(f"wrote {OUT}")


if __name__ == "__main__":
    main()
