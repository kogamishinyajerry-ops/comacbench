#!/usr/bin/env python3
"""Generate visible/drawing.png for turbulent_plate_from_brief.

Annotated schematic of the turbulent flat-plate domain: plate from x=0 to
x=2.0 m at y=0 (inlet AT the leading edge, fully turbulent), domain
height 0.5 m, boundary roles, the 1/7-power boundary-layer edge estimate
(dashed), the two QoI stations x = 0.5/1.0 m (Re_x = 5e5 / 1e6), and the
turbulence-model requirements (k-omega SST, I=5%, L=0.01 m, y+ ~ 30 wall
functions). Every annotated number MUST match the engineering brief
(visible/task.md) and the source validation case
cases/validation/turbulent_flat_plate — the drawing is part of the frozen
visible/ task surface.

Host-side authoring tool (matplotlib); NOT part of the scoring path —
the frozen QoI script is reference/compute_qoi.py (stdlib-only).
All labels are ASCII/English to avoid CJK glyph issues.

Run:  python3 reference/make_drawing.py
"""

from __future__ import annotations

from pathlib import Path

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt

# Geometry/physics (must match visible/task.md and the source case).
X_OUT = 2.0
H = 0.5
STATIONS = (0.5, 1.0)

CASE_DIR = Path(__file__).resolve().parent.parent
OUT = CASE_DIR / "visible" / "drawing.png"


def bl_edge(x: float) -> float:
    # 1/7-power estimate: delta ~ 0.37 * x / Re_x^(1/5), Re_x = 1e6 * x[m].
    return 0.37 * x / (1e6 * x) ** 0.2


def main() -> None:
    fig, ax = plt.subplots(figsize=(12, 5.2), dpi=150)

    # Domain.
    ax.add_patch(
        plt.Rectangle((0, 0), X_OUT, H, facecolor="#eaf3fb", edgecolor="none",
                      zorder=0)
    )

    # Turbulent BL edge estimate (orientation only).
    xs = [0.05 + i * (1.9 / 100) for i in range(101)]
    ax.plot(xs, [bl_edge(x) for x in xs], color="#d62728", lw=1.4, ls="--")
    ax.text(1.05, bl_edge(1.05) + 0.02,
            "turbulent BL edge ~ 0.37x / Re_x^(1/5)  (delta_TE ~ 0.04 m)",
            color="#d62728", fontsize=9)

    # Plate.
    ax.plot([0, X_OUT], [0, 0], color="black", lw=3.5, solid_capstyle="butt")
    for x in [i * X_OUT / 40 for i in range(41)]:
        ax.plot([x, x - 0.03], [0, -0.025], color="black", lw=0.7)
    ax.text(1.0, -0.055, "plate (no-slip wall, wall functions, y+ ~ 30),"
            " x = 0 .. 2.0 m", ha="center", fontsize=10)

    # Boundaries.
    ax.plot([0, 0], [0, H], color="#1f77b4", lw=2.5)
    ax.text(-0.04, 0.25, "inlet (= leading edge):\nU_inf = 10 m/s\n"
            "I = 5%, L = 0.01 m", rotation=90, va="center", ha="right",
            color="#1f77b4", fontsize=9)
    ax.plot([X_OUT, X_OUT], [0, H], color="#2ca02c", lw=2.5)
    ax.text(X_OUT + 0.04, 0.25, "outlet", rotation=270, va="center",
            ha="right", color="#2ca02c", fontsize=10)
    ax.plot([0, X_OUT], [H, H], color="black", lw=2)
    ax.text(1.0, H + 0.018, "top: symmetry / far field (H = 0.5 m >> delta)",
            ha="center", fontsize=9)

    # Freestream arrows.
    for y in (0.25, 0.36, 0.45):
        ax.annotate("", xy=(0.55, y), xytext=(0.10, y),
                    arrowprops=dict(arrowstyle="-|>", color="#1f77b4", lw=1.6))

    # QoI stations.
    for x0 in STATIONS:
        ax.plot([x0, x0], [0, bl_edge(x0) * 1.5], color="#9467bd", lw=1.8)
        ax.plot(x0, 0, marker="v", ms=6, color="#9467bd")
    ax.text(0.75, 0.115, "QoI stations x = 0.5 / 1.0 m\n"
            "(Re_x = 5e5 / 1e6;  cf_distribution.csv: x, cf)", ha="center",
            fontsize=9, color="#9467bd")

    # Flow / turbulence-model annotation.
    ax.text(1.42, 0.44,
            "incompressible TURBULENT flow (RANS)\n"
            "nu = 1e-5 m^2/s,  U_inf = 10 m/s\n"
            "Re_x = 1e6 * x[m]  (plate: 0 .. 2e6)\n"
            "model: k-omega SST, fully turbulent\n"
            "(no transition model)",
            ha="center", va="top", fontsize=10)

    # Dimension: plate length.
    y_dim = -0.115
    ax.annotate("", xy=(X_OUT, y_dim), xytext=(0, y_dim),
                arrowprops=dict(arrowstyle="<->", color="black", lw=1.2))
    ax.plot([0, 0], [y_dim - 0.015, 0], color="black", lw=0.7, ls=":")
    ax.plot([X_OUT, X_OUT], [y_dim - 0.015, 0], color="black", lw=0.7, ls=":")
    ax.text(1.0, y_dim - 0.025, "plate L = 2.0 m", ha="center", va="top",
            fontsize=10)

    # Dimension: height.
    x_dim = -0.16
    ax.annotate("", xy=(x_dim, H), xytext=(x_dim, 0),
                arrowprops=dict(arrowstyle="<->", color="black", lw=1.2))
    ax.plot([x_dim - 0.03, 0], [0, 0], color="black", lw=0.7, ls=":")
    ax.plot([x_dim - 0.03, 0], [H, H], color="black", lw=0.7, ls=":")
    ax.text(x_dim - 0.05, 0.25, "H = 0.5 m", rotation=90, va="center",
            ha="center", fontsize=10)

    # Axes hints.
    ax.annotate("x", xy=(0.14, -0.17), xytext=(0.0, -0.17),
                arrowprops=dict(arrowstyle="->", lw=1), fontsize=10)
    ax.annotate("y", xy=(-0.06, -0.06), xytext=(-0.06, -0.17),
                arrowprops=dict(arrowstyle="->", lw=1), fontsize=10)

    ax.set_xlim(-0.32, 2.28)
    ax.set_ylim(-0.22, 0.58)
    ax.set_aspect("equal")
    ax.axis("off")
    ax.set_title("Zero-pressure-gradient turbulent flat plate (RANS, k-omega"
                 " SST) — case setup", fontsize=12, pad=10)

    OUT.parent.mkdir(parents=True, exist_ok=True)
    fig.savefig(OUT, bbox_inches="tight")
    print(f"wrote {OUT}")


if __name__ == "__main__":
    main()
