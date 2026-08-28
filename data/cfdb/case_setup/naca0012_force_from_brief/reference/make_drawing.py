#!/usr/bin/env python3
"""Generate visible/drawing.png for naca0012_force_from_brief.

Annotated schematic of the NACA0012 airfoil at alpha = 0 deg: chord
c = 1 m, freestream U_inf = 100 m/s, farfield extent, force directions.
The airfoil contour is drawn from the closed-form NACA 4-digit thickness
equation (self-contained; the source validation case's geometry file
cases/validation/naca0012/geometry/naca0012.dat is the same profile).
Every annotated number MUST match the engineering brief
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

CHORD = 1.0  # m
U_INF = 100.0  # m/s
NU = 1.6667e-5  # m^2/s -> Re = 6.0e6

CASE_DIR = Path(__file__).resolve().parent.parent
OUT = CASE_DIR / "visible" / "drawing.png"


def naca0012_half_thickness(x: float) -> float:
    """Closed-form NACA 4-digit (12%) half thickness at chord station x."""
    return (0.12 / 0.2) * CHORD * (
        0.2969 * math.sqrt(x / CHORD)
        - 0.1260 * (x / CHORD)
        - 0.3516 * (x / CHORD) ** 2
        + 0.2843 * (x / CHORD) ** 3
        - 0.1015 * (x / CHORD) ** 4
    )


def main() -> None:
    fig, ax = plt.subplots(figsize=(11, 4.6), dpi=150)

    xs = [CHORD * i / 200 for i in range(201)]
    yt = [naca0012_half_thickness(x) for x in xs]
    ax.plot(xs, yt, color="black", lw=2)
    ax.plot(xs, [-y for y in yt], color="black", lw=2)
    ax.fill(xs + xs[::-1], yt + [-y for y in yt[::-1]], color="#eaf3fb", zorder=0)

    # Freestream arrows.
    for y in [-0.25, -0.15, 0.15, 0.25]:
        ax.annotate("", xy=(0.28, y), xytext=(-0.32, y),
                    arrowprops=dict(arrowstyle="-|>", color="#1f77b4", lw=1.6))
    ax.text(-0.02, 0.33, f"U_inf = {U_INF:g} m/s,  alpha = 0 deg",
            ha="center", fontsize=11, color="#1f77b4")

    # Chord dimension (below).
    y_dim = -0.42
    ax.annotate("", xy=(CHORD, y_dim), xytext=(0, y_dim),
                arrowprops=dict(arrowstyle="<->", color="black", lw=1.2))
    ax.plot([0, 0], [y_dim - 0.02, 0], color="black", lw=0.7, ls=":")
    ax.plot([CHORD, CHORD], [y_dim - 0.02, -0.06], color="black", lw=0.7, ls=":")
    ax.text(CHORD / 2, y_dim - 0.05, "chord c = 1 m", ha="center", va="top",
            fontsize=10)
    ax.text(0, 0.02, "LE (0, 0)", fontsize=9, va="bottom", ha="left")
    ax.text(CHORD, 0.02, "TE (1, 0)", fontsize=9, va="bottom", ha="right")

    # Force directions.
    ax.annotate("", xy=(0.78, 0.0), xytext=(0.5, 0.0),
                arrowprops=dict(arrowstyle="-|>", color="#d62728", lw=1.8))
    ax.text(0.64, -0.055, "drag (x)", color="#d62728", fontsize=10, ha="center")
    ax.annotate("", xy=(0.5, 0.22), xytext=(0.5, 0.0),
                arrowprops=dict(arrowstyle="-|>", color="#2ca02c", lw=1.8))
    ax.text(0.515, 0.12, "lift (y)", color="#2ca02c", fontsize=10)

    # Conditions box.
    ax.text(1.25, 0.3,
            "NACA0012 (symmetric, t/c = 12%)\n"
            "Re = U_inf·c/ν = 6.0e6\n"
            "ν = 1.6667e-5 m²/s\n"
            "M = 0.3 (low-Mach RANS)\n"
            "turbulence model: SA or equivalent\n"
            "(declare model + near-wall treatment)",
            fontsize=10, va="top", ha="left")

    # Farfield hint.
    ax.text(1.25, -0.28,
            "farfield: extend >= 15c around the airfoil\n"
            "reference area A_ref = c x unit span\n"
            "(sectional, per-unit-span cl/cd)",
            fontsize=9, va="top", ha="left", color="#555555")

    ax.set_xlim(-0.55, 2.1)
    ax.set_ylim(-0.62, 0.5)
    ax.set_aspect("equal")
    ax.axis("off")
    ax.set_title("NACA0012 airfoil at alpha = 0 deg — Re = 6e6, M = 0.3",
                 fontsize=12, pad=10)

    OUT.parent.mkdir(parents=True, exist_ok=True)
    fig.savefig(OUT, bbox_inches="tight")
    print(f"wrote {OUT}")


if __name__ == "__main__":
    main()
