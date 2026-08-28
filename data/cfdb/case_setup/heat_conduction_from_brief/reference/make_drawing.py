#!/usr/bin/env python3
"""Generate visible/drawing.png for heat_conduction_from_brief.

Annotated schematic of the plane solid wall: thickness L = 1 m, both
faces held at T_s = 300 K, uniform volumetric heat source, thermal
diffusivity alpha = 0.1 m^2/s, and the expected parabolic steady profile
hint. Every annotated number MUST match the brief (visible/task.md) and
the golden source configuration (cases/verification/heat_conduction_1d)
— the drawing is part of the frozen visible/ task surface.

Host-side authoring tool (matplotlib); NOT part of the scoring path —
the frozen QoI script is reference/compute_qoi.py (stdlib-only).
Annotations use English only to avoid CJK glyph issues.

Run:  python3 reference/make_drawing.py
"""

from __future__ import annotations

from pathlib import Path

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib.patches import Rectangle

L = 1.0  # m, wall thickness (x)
H = 0.5  # m, drawing height of the wall cross-section (arbitrary)
T_S = 300.0  # K, both face temperatures
ALPHA = 0.1  # m^2/s, thermal diffusivity
SOURCE = 100.0  # K/s, temperature-equation source (q/k = S/alpha = 1000 K/m^2)

CASE_DIR = Path(__file__).resolve().parent.parent
OUT = CASE_DIR / "visible" / "drawing.png"


def main() -> None:
    fig, ax = plt.subplots(figsize=(9, 5.2), dpi=150)

    # Wall body.
    ax.add_patch(
        Rectangle((0, 0), L, H, facecolor="#fdeacc", edgecolor="none", zorder=0)
    )
    ax.plot([0, L], [H, H], color="black", lw=2)
    ax.plot([0, L], [0, 0], color="black", lw=2)

    # Isothermal faces.
    ax.plot([0, 0], [0, H], color="#1f77b4", lw=4)
    ax.plot([L, L], [0, H], color="#1f77b4", lw=4)
    ax.text(-0.03, H + 0.06, f"face x = 0\nT = {T_S:.0f} K (fixed)",
            ha="center", va="bottom", fontsize=10, color="#1f77b4")
    ax.text(L + 0.03, H + 0.06, f"face x = L\nT = {T_S:.0f} K (fixed)",
            ha="center", va="bottom", fontsize=10, color="#1f77b4")

    # Internal heat source marks.
    for i in range(1, 8):
        for j in range(1, 4):
            ax.plot(i * L / 8, j * H / 4, marker="o", ms=4, color="#d62728",
                    alpha=0.55)
    ax.text(L * 0.5, -0.13,
            "solid, uniform volumetric heat source\n"
            "dT/dt = alpha d2T/dx2 + S\n"
            f"alpha = {ALPHA} m^2/s    S = {SOURCE:.0f} K/s\n"
            "(q'''/k = S/alpha = 1000 K/m^2)\n"
            "lateral sides adiabatic / symmetry (strictly 1D)",
            ha="center", va="top", fontsize=10,
            bbox=dict(facecolor="white", alpha=0.85, edgecolor="none"))

    # Steady parabolic profile hint (plotted sideways above the wall).
    xs = [L * i / 100 for i in range(101)]
    prof = [T_S + 500.0 * x * (1 - x) for x in xs]
    scale = 0.9 / (max(prof) - T_S)
    ax.plot(xs, [H + 0.16 + (t - T_S) * scale for t in prof],
            color="#d62728", lw=1.6, ls="--")
    ax.text(L * 0.5, H + 0.16 + (max(prof) - T_S) * scale + 0.05,
            "expected steady profile: parabola (shape hint, not to scale)",
            ha="center", va="bottom", fontsize=9, color="#d62728")

    # Dimension: L.
    y_dim = -0.78
    ax.annotate("", xy=(L, y_dim), xytext=(0, y_dim),
                arrowprops=dict(arrowstyle="<->", color="black", lw=1.2))
    ax.plot([0, 0], [y_dim - 0.04, 0], color="black", lw=0.7, ls=":")
    ax.plot([L, L], [y_dim - 0.04, 0], color="black", lw=0.7, ls=":")
    ax.text(L / 2, y_dim - 0.08, "L = 1 m", ha="center", va="top", fontsize=11)

    # Midplane marker (labelled with a leader arrow to keep the wall clear).
    ax.plot([X := L / 2, X], [0, H], color="#2ca02c", lw=1.2, ls=":")
    ax.annotate("midplane x = L/2 (QoI probe)", xy=(X, H * 0.72),
                xytext=(L + 0.3, H * 0.72), ha="left", va="center",
                fontsize=9, color="#2ca02c",
                arrowprops=dict(arrowstyle="->", color="#2ca02c", lw=0.9))

    # Axis hint.
    ax.annotate("x", xy=(0.99, -0.94), xytext=(0.87, -0.94),
                arrowprops=dict(arrowstyle="->", lw=1), fontsize=10)

    ax.set_xlim(-0.22, L + 0.95)
    ax.set_ylim(-1.05, H + 1.35)
    ax.set_aspect("equal")
    ax.axis("off")
    ax.set_title("Plane solid wall (1D) — conduction with uniform heat source",
                 fontsize=12, pad=10)

    OUT.parent.mkdir(parents=True, exist_ok=True)
    fig.savefig(OUT, bbox_inches="tight")
    print(f"wrote {OUT}")


if __name__ == "__main__":
    main()
