#!/usr/bin/env python3
"""Generate visible/drawing.png for blasius_plate_from_brief.

Annotated schematic of the laminar flat-plate domain: plate from x=0 to
x=1.2 m at y=0, slip fetch upstream to x=-0.2 m, domain height 0.2 m,
boundary roles, the Blasius boundary-layer edge (delta = 5x/sqrt(Re_x),
dashed) and the four QoI stations x = 0.2/0.5/0.8/1.0 m. Every annotated
number MUST match the engineering brief (visible/task.md) and the source
verification case cases/verification/flat_plate_blasius_of — the drawing
is part of the frozen visible/ task surface.

Host-side authoring tool (matplotlib); NOT part of the scoring path —
the frozen QoI script is reference/compute_qoi.py (stdlib-only).
All labels are ASCII/English to avoid CJK glyph issues.

Run:  python3 reference/make_drawing.py
"""

from __future__ import annotations

import math
from pathlib import Path

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt

# Geometry/physics (must match visible/task.md and the source case).
X_IN = -0.2
X_LE = 0.0
X_OUT = 1.2
H = 0.2
U_INF = 1.0
NU = 1e-5
STATIONS = (0.2, 0.5, 0.8, 1.0)

CASE_DIR = Path(__file__).resolve().parent.parent
OUT = CASE_DIR / "visible" / "drawing.png"


def blasius_delta(x: float) -> float:
    return 5.0 * x / math.sqrt(U_INF * x / NU)


def main() -> None:
    fig, ax = plt.subplots(figsize=(12, 4.6), dpi=150)

    # Domain.
    ax.add_patch(
        plt.Rectangle((X_IN, 0), X_OUT - X_IN, H, facecolor="#eaf3fb",
                      edgecolor="none", zorder=0)
    )

    # Blasius boundary-layer edge (orientation only).
    xs = [0.02 + i * (1.18 / 100) for i in range(101)]
    ax.plot(xs, [blasius_delta(x) for x in xs], color="#d62728", lw=1.4,
            ls="--")
    ax.text(0.52, blasius_delta(0.52) + 0.012,
            "Blasius BL edge: delta = 5x / sqrt(Re_x)",
            color="#d62728", fontsize=9)

    # Plate and upstream slip fetch.
    ax.plot([X_LE, X_OUT], [0, 0], color="black", lw=3.5,
            solid_capstyle="butt")
    for x in [X_LE + i * (X_OUT - X_LE) / 30 for i in range(31)]:
        ax.plot([x, x - 0.02], [0, -0.018], color="black", lw=0.7)
    ax.text(0.6, -0.038, "plate (no-slip wall), x = 0 .. 1.2 m", ha="center",
            fontsize=10)
    ax.plot([X_IN, X_LE], [0, 0], color="black", lw=1.5, ls="-.")
    ax.text(-0.1, -0.038, "slip fetch", ha="center", fontsize=9)

    # Boundaries.
    ax.plot([X_IN, X_IN], [0, H], color="#1f77b4", lw=2.5)
    ax.text(X_IN - 0.025, 0.10, "inlet: uniform U_inf = 1 m/s", rotation=90,
            va="center", ha="right", color="#1f77b4", fontsize=10)
    ax.plot([X_OUT, X_OUT], [0, H], color="#2ca02c", lw=2.5)
    ax.text(X_OUT + 0.025, 0.10, "outlet", rotation=270, va="center",
            ha="right", color="#2ca02c", fontsize=10)
    ax.plot([X_IN, X_OUT], [H, H], color="black", lw=2)
    ax.text(0.5, H + 0.012, "top: symmetry / far field (H = 0.2 m ~ 12*delta)",
            ha="center", fontsize=9)

    # Freestream arrows.
    for y in (0.10, 0.15):
        ax.annotate("", xy=(0.12, y), xytext=(-0.14, y),
                    arrowprops=dict(arrowstyle="-|>", color="#1f77b4", lw=1.6))

    # QoI stations.
    for x0 in STATIONS:
        ax.plot([x0, x0], [0, blasius_delta(x0) * 1.35], color="#9467bd",
                lw=1.6)
        ax.plot(x0, 0, marker="v", ms=6, color="#9467bd")
    ax.text(0.30, 0.115, "QoI stations x = 0.2 / 0.5 / 0.8 / 1.0 m\n"
            "(cf_distribution.csv: x, cf)", ha="center", fontsize=9,
            color="#9467bd")

    # Flow annotation.
    ax.text(0.88, 0.115,
            "incompressible LAMINAR flow\nnu = 1e-5 m^2/s,  U_inf = 1 m/s\n"
            "Re_x = 1e5 * x[m]  (stations: 2e4 .. 1e5)",
            ha="center", fontsize=10)

    # Leading edge marker.
    ax.annotate("leading edge x = 0", xy=(0, 0), xytext=(0.02, 0.175),
                fontsize=9,
                arrowprops=dict(arrowstyle="->", lw=1))

    # Dimensions.
    y_dim = -0.075
    ax.annotate("", xy=(X_OUT, y_dim), xytext=(X_LE, y_dim),
                arrowprops=dict(arrowstyle="<->", color="black", lw=1.2))
    ax.plot([X_LE, X_LE], [y_dim - 0.01, 0], color="black", lw=0.7, ls=":")
    ax.plot([X_OUT, X_OUT], [y_dim - 0.01, 0], color="black", lw=0.7, ls=":")
    ax.text(0.6, y_dim - 0.018, "plate L = 1.2 m", ha="center", va="top",
            fontsize=10)
    ax.annotate("", xy=(X_LE, y_dim + 0.045), xytext=(X_IN, y_dim + 0.045),
                arrowprops=dict(arrowstyle="<->", color="black", lw=1.0))
    ax.plot([X_IN, X_IN], [y_dim + 0.03, 0], color="black", lw=0.7, ls=":")
    ax.text(-0.1, y_dim + 0.052, "0.2 m", ha="center", va="bottom",
            fontsize=9)

    # Axes hints.
    ax.annotate("x", xy=(-0.05, -0.11), xytext=(-0.14, -0.11),
                arrowprops=dict(arrowstyle="->", lw=1), fontsize=10)
    ax.annotate("y", xy=(-0.19, -0.04), xytext=(-0.19, -0.11),
                arrowprops=dict(arrowstyle="->", lw=1), fontsize=10)

    ax.set_xlim(-0.32, 1.38)
    ax.set_ylim(-0.14, 0.26)
    ax.set_aspect("equal")
    ax.axis("off")
    ax.set_title("Laminar flat-plate boundary layer (Blasius) — case setup",
                 fontsize=12, pad=10)

    OUT.parent.mkdir(parents=True, exist_ok=True)
    fig.savefig(OUT, bbox_inches="tight")
    print(f"wrote {OUT}")


if __name__ == "__main__":
    main()
