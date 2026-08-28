#!/usr/bin/env python3
"""Generate visible/drawing.png for turbulent_channel_from_brief.

Annotated schematic of the plane turbulent channel: full height 2h = 2 m,
streamwise period Lx = 2*pi*h, spanwise period Lz = pi*h, no-slip walls,
periodic streamwise/spanwise directions, imposed bulk velocity
U_b = 1 m/s. Every annotated number MUST match the engineering brief
(visible/task.md) — the drawing is part of the frozen visible/ task
surface.

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

H_HALF = 1.0  # m, channel half-height h
HEIGHT = 2.0 * H_HALF  # m, full channel height 2h
LX = 2.0 * math.pi * H_HALF  # m, streamwise period
LZ = math.pi * H_HALF  # m, spanwise period
U_BULK = 1.0  # m/s, imposed bulk velocity

CASE_DIR = Path(__file__).resolve().parent.parent
OUT = CASE_DIR / "visible" / "drawing.png"


def main() -> None:
    fig, ax = plt.subplots(figsize=(11, 4.2), dpi=150)

    # Channel body (side view, x-y plane; drawing units: metres).
    ax.add_patch(
        Rectangle((0, 0), LX, HEIGHT, facecolor="#eaf3fb", edgecolor="none", zorder=0)
    )

    # Walls (thick lines with hatching).
    ax.plot([0, LX], [HEIGHT, HEIGHT], color="black", lw=3, solid_capstyle="butt")
    ax.plot([0, LX], [0, 0], color="black", lw=3, solid_capstyle="butt")
    for i in range(25):
        x = i * LX / 24
        ax.plot([x, x - 0.09], [HEIGHT, HEIGHT + 0.06], color="black", lw=0.8)
        ax.plot([x, x - 0.09], [0, -0.06], color="black", lw=0.8)
    ax.text(LX * 0.5, HEIGHT + 0.14, "walls (no-slip), y = 0 and y = 2h",
            ha="center", fontsize=10)

    # Periodic boundaries in x.
    ax.plot([0, 0], [0, HEIGHT], color="#1f77b4", lw=2, ls="--")
    ax.plot([LX, LX], [0, HEIGHT], color="#1f77b4", lw=2, ls="--")
    ax.text(-0.18, HEIGHT * 0.5, "periodic", rotation=90, va="center",
            ha="right", color="#1f77b4", fontsize=10)
    ax.text(LX + 0.18, HEIGHT * 0.5, "periodic", rotation=270, va="center",
            ha="right", color="#1f77b4", fontsize=10)

    # Turbulent mean-profile hint (1/7 power-law shape, schematic only).
    ys = [HEIGHT * i / 60 for i in range(61)]
    prof = [0.9 + 1.35 * min((y / H_HALF) ** (1 / 7), 1.0) for y in ys]
    ax.plot(prof, ys, color="#d62728", lw=1.4, ls="--")
    ax.text(2.75, HEIGHT * 0.86, "turbulent mean profile\n(schematic)",
            color="#d62728", fontsize=9, ha="center")

    # Bulk-velocity arrows.
    for y in [0.25 * HEIGHT, 0.5 * HEIGHT, 0.75 * HEIGHT]:
        ax.annotate("", xy=(1.15, y), xytext=(0.35, y),
                    arrowprops=dict(arrowstyle="-|>", color="#1f77b4", lw=1.6))
    ax.text(0.75, HEIGHT + 0.14, f"U_b = {U_BULK} m/s bulk (imposed)",
            ha="center", fontsize=10, color="#1f77b4")

    # Dimension: Lx (below).
    y_dim = -0.42
    ax.annotate("", xy=(LX, y_dim), xytext=(0, y_dim),
                arrowprops=dict(arrowstyle="<->", color="black", lw=1.2))
    ax.plot([0, 0], [y_dim - 0.05, 0], color="black", lw=0.7, ls=":")
    ax.plot([LX, LX], [y_dim - 0.05, 0], color="black", lw=0.7, ls=":")
    ax.text(LX / 2, y_dim - 0.1, "Lx = 2πh ≈ 6.283 m (periodic)",
            ha="center", va="top", fontsize=10)

    # Dimension: 2h (left).
    x_dim = -0.62
    ax.annotate("", xy=(x_dim, HEIGHT), xytext=(x_dim, 0),
                arrowprops=dict(arrowstyle="<->", color="black", lw=1.2))
    ax.plot([x_dim - 0.06, 0], [0, 0], color="black", lw=0.7, ls=":")
    ax.plot([x_dim - 0.06, 0], [HEIGHT, HEIGHT], color="black", lw=0.7, ls=":")
    ax.text(x_dim - 0.16, HEIGHT / 2, "2h = 2 m (h = 1 m)", rotation=90,
            va="center", ha="center", fontsize=10)

    # Fluid / regime annotation.
    ax.text(LX * 0.62, HEIGHT * 0.5,
            "fully developed turbulent channel flow\n"
            "ν = 3.571429e-4 m²/s\n"
            "Re_b = U_b·h/ν = 2800   →   Re_τ ≈ 180\n"
            "spanwise period Lz = πh ≈ 3.142 m (periodic)",
            ha="center", va="center", fontsize=10)

    # Axes hints.
    ax.annotate("x", xy=(0.75, -0.13), xytext=(0.15, -0.13),
                arrowprops=dict(arrowstyle="->", lw=1), fontsize=10)
    ax.annotate("y", xy=(-0.18, 0.11), xytext=(-0.18, -0.13),
                arrowprops=dict(arrowstyle="->", lw=1), fontsize=10)

    ax.set_xlim(-1.25, LX + 0.75)
    ax.set_ylim(-0.72, HEIGHT + 0.42)
    ax.set_aspect("equal")
    ax.axis("off")
    ax.set_title("Plane turbulent channel — fully developed flow at Re_tau = 180",
                 fontsize=12, pad=10)

    OUT.parent.mkdir(parents=True, exist_ok=True)
    fig.savefig(OUT, bbox_inches="tight")
    print(f"wrote {OUT}")


if __name__ == "__main__":
    main()
