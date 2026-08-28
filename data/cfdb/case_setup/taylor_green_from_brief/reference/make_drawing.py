#!/usr/bin/env python3
"""Generate visible/drawing.png for taylor_green_from_brief.

Annotated schematic of the Taylor-Green decaying vortex domain: doubly
periodic square [0, 2*pi]^2, the t=0 vortex cell pattern, viscosity
nu = 0.01 m^2/s (Re = 100), and the t = 5 s sample line at
y = 11*pi/64. Every annotated number MUST match the brief
(visible/task.md) and the golden source configuration
(cases/verification/taylor_green_vortex) — the drawing is part of the
frozen visible/ task surface.

Host-side authoring tool (matplotlib); NOT part of the scoring path —
the frozen QoI script is reference/compute_qoi.py (stdlib-only).
Annotations use English only to avoid CJK glyph issues.

Run:  python3 reference/make_drawing.py
"""

from __future__ import annotations

import math
from pathlib import Path

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib.patches import Rectangle

L = 2.0 * math.pi  # m, domain side length (both directions periodic)
NU = 0.01  # m^2/s
U0 = 1.0  # m/s
Y_LINE = 5.5 * 2.0 * math.pi / 64.0  # 11*pi/64 sample line ordinate

CASE_DIR = Path(__file__).resolve().parent.parent
OUT = CASE_DIR / "visible" / "drawing.png"


def main() -> None:
    fig, ax = plt.subplots(figsize=(8.4, 7.6), dpi=150)

    # Domain body.
    ax.add_patch(
        Rectangle((0, 0), L, L, facecolor="#eef6ee", edgecolor="none", zorder=0)
    )

    # Periodic boundaries (same style on opposite sides = paired).
    for seg in ([(0, 0), (L, 0)], [(0, L), (L, L)]):
        ax.plot([seg[0][0], seg[1][0]], [seg[0][1], seg[1][1]],
                color="#1f77b4", lw=2.5, ls=(0, (6, 3)))
    for seg in ([(0, 0), (0, L)], [(L, 0), (L, L)]):
        ax.plot([seg[0][0], seg[1][0]], [seg[0][1], seg[1][1]],
                color="#2ca02c", lw=2.5, ls=(0, (2, 2)))
    ax.text(L / 2, L + 0.18, "periodic (paired with bottom)",
            ha="center", fontsize=9, color="#1f77b4")
    ax.text(L / 2, -0.42, "periodic (paired with top)",
            ha="center", fontsize=9, color="#1f77b4")
    ax.text(-0.18, L / 2, "periodic (paired with right)", rotation=90,
            va="center", ha="right", fontsize=9, color="#2ca02c")
    ax.text(L + 0.18, L / 2, "periodic (paired with left)", rotation=270,
            va="center", ha="right", fontsize=9, color="#2ca02c")

    # Vortex cell pattern: arrows of the t=0 field on a coarse lattice.
    n = 9
    for i in range(n):
        for j in range(n):
            x = (i + 0.5) * L / n
            y = (j + 0.5) * L / n
            u = U0 * math.sin(x) * math.cos(y)
            v = -U0 * math.cos(x) * math.sin(y)
            ax.annotate("", xy=(x + 0.22 * u, y + 0.22 * v), xytext=(x, y),
                        arrowprops=dict(arrowstyle="-|>", color="#555555",
                                        lw=0.9, alpha=0.8))
    ax.text(L * 0.5, L * 0.52,
            "t = 0:  u = U0 sin(kx) cos(ky)\n"
            "         v = -U0 cos(kx) sin(ky)\n"
            f"U0 = {U0:g} m/s,  k = 1 1/m\n"
            f"nu = {NU:g} m^2/s,  Re = U0/(k nu) = 100\n"
            "freely decaying (no forcing), t: 0 -> 5 s",
            ha="center", va="center", fontsize=10,
            bbox=dict(facecolor="white", alpha=0.88, edgecolor="none"))

    # Sample line at y = 11*pi/64.
    ax.plot([0, L], [Y_LINE, Y_LINE], color="#d62728", lw=1.8)
    for i in range(64):
        ax.plot((i + 0.5) * L / 64, Y_LINE, marker="o", ms=2, color="#d62728")
    ax.annotate("sample line at t = 5 s\ny = 11*pi/64 = 0.5399613 m\n(~64 points, fields u, v)",
                xy=(L * 0.98, Y_LINE), xytext=(L * 0.63, Y_LINE + 1.15),
                ha="center", fontsize=9, color="#d62728",
                arrowprops=dict(arrowstyle="->", color="#d62728", lw=0.9))

    # Dimension: side length.
    y_dim = -0.85
    ax.annotate("", xy=(L, y_dim), xytext=(0, y_dim),
                arrowprops=dict(arrowstyle="<->", color="black", lw=1.2))
    ax.plot([0, 0], [y_dim - 0.12, 0], color="black", lw=0.7, ls=":")
    ax.plot([L, L], [y_dim - 0.12, 0], color="black", lw=0.7, ls=":")
    ax.text(L / 2, y_dim - 0.2, "2*pi = 6.2832 m", ha="center", va="top",
            fontsize=11)
    x_dim = -0.85
    ax.annotate("", xy=(x_dim, L), xytext=(x_dim, 0),
                arrowprops=dict(arrowstyle="<->", color="black", lw=1.2))
    ax.plot([x_dim - 0.12, 0], [0, 0], color="black", lw=0.7, ls=":")
    ax.plot([x_dim - 0.12, 0], [L, L], color="black", lw=0.7, ls=":")
    ax.text(x_dim - 0.2, L / 2, "2*pi = 6.2832 m", rotation=90, va="center",
            ha="center", fontsize=11)

    # Axis hints.
    ax.annotate("x", xy=(0.75, -1.35), xytext=(0.0, -1.35),
                arrowprops=dict(arrowstyle="->", lw=1), fontsize=10)
    ax.annotate("y", xy=(-1.35, 0.75), xytext=(-1.35, 0.0),
                arrowprops=dict(arrowstyle="->", lw=1), fontsize=10)

    ax.set_xlim(-1.8, L + 0.6)
    ax.set_ylim(-1.6, L + 0.6)
    ax.set_aspect("equal")
    ax.axis("off")
    ax.set_title("Taylor-Green decaying vortex (2D, doubly periodic)",
                 fontsize=12, pad=10)

    OUT.parent.mkdir(parents=True, exist_ok=True)
    fig.savefig(OUT, bbox_inches="tight")
    print(f"wrote {OUT}")


if __name__ == "__main__":
    main()
