#!/usr/bin/env python3
"""Generate visible/drawing.png for sod_shock_from_brief.

Annotated schematic of the Sod shock tube: tube x in [0, 1] m, diaphragm
at x = 0.5, left/right initial states (p, rho), gamma = 1.4, evaluation
time t = 0.2 s, and the star-region probe at x = 0.6. Every annotated
number MUST match the brief (visible/task.md) and the golden source
configuration (cases/verification/sod_shock_tube) — the drawing is part
of the frozen visible/ task surface.

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

L = 1.0  # m, tube length
H = 0.4  # m, drawing height of the tube cross-section (arbitrary)
X_DIA = 0.5  # m, diaphragm position
X_PROBE = 0.6  # m, star-region density probe

CASE_DIR = Path(__file__).resolve().parent.parent
OUT = CASE_DIR / "visible" / "drawing.png"


def main() -> None:
    fig, ax = plt.subplots(figsize=(11, 4.6), dpi=150)

    # Tube body: left / right initial states shaded differently.
    ax.add_patch(Rectangle((0, 0), X_DIA, H, facecolor="#dceefb",
                           edgecolor="none", zorder=0))
    ax.add_patch(Rectangle((X_DIA, 0), L - X_DIA, H, facecolor="#f3f3f3",
                           edgecolor="none", zorder=0))
    ax.plot([0, L], [H, H], color="black", lw=2.5)
    ax.plot([0, L], [0, 0], color="black", lw=2.5)
    ax.plot([0, 0], [0, H], color="black", lw=2.5)
    ax.plot([L, L], [0, H], color="black", lw=2.5)

    # Diaphragm.
    ax.plot([X_DIA, X_DIA], [0, H], color="#d62728", lw=3)
    ax.text(X_DIA, H + 0.05, "diaphragm at x = 0.5 m\n(removed at t = 0)",
            ha="center", va="bottom", fontsize=10, color="#d62728")

    # Initial states.
    ax.text(X_DIA * 0.5, H * 0.52,
            "LEFT state (at rest)\np = 1 Pa\nrho = 1 kg/m^3",
            ha="center", va="center", fontsize=11)
    ax.text(X_DIA + (L - X_DIA) * 0.5, H * 0.52,
            "RIGHT state (at rest)\np = 0.1 Pa\nrho = 0.125 kg/m^3",
            ha="center", va="center", fontsize=11)

    # Physics note.
    ax.text(L * 0.5, -0.17,
            "inviscid compressible Euler, ideal gas, gamma = 1.4 (exact); "
            "run to t = 0.2 s",
            ha="center", va="top", fontsize=10)

    # Star-region probe.
    ax.plot([X_PROBE], [0], marker="^", ms=9, color="#2ca02c",
            clip_on=False)
    ax.annotate("density probe x = 0.6 m\n(star-region plateau at t = 0.2 s)",
                xy=(X_PROBE, 0), xytext=(X_PROBE + 0.16, -0.42),
                ha="left", va="top", fontsize=9, color="#2ca02c",
                arrowprops=dict(arrowstyle="->", color="#2ca02c", lw=0.9))

    # Dimension: L.
    y_dim = -0.62
    ax.annotate("", xy=(L, y_dim), xytext=(0, y_dim),
                arrowprops=dict(arrowstyle="<->", color="black", lw=1.2))
    ax.plot([0, 0], [y_dim - 0.05, 0], color="black", lw=0.7, ls=":")
    ax.plot([L, L], [y_dim - 0.05, 0], color="black", lw=0.7, ls=":")
    ax.text(L / 2, y_dim - 0.07, "L = 1 m", ha="center", va="top",
            fontsize=11)

    # Axis hint.
    ax.annotate("x", xy=(0.14, -0.85), xytext=(0.02, -0.85),
                arrowprops=dict(arrowstyle="->", lw=1), fontsize=10)

    ax.set_xlim(-0.08, L + 0.08)
    ax.set_ylim(-1.0, H + 0.35)
    ax.axis("off")
    ax.set_title("Sod shock tube (1D, inviscid compressible Euler)",
                 fontsize=12, pad=10)

    OUT.parent.mkdir(parents=True, exist_ok=True)
    fig.savefig(OUT, bbox_inches="tight")
    print(f"wrote {OUT}")


if __name__ == "__main__":
    main()
