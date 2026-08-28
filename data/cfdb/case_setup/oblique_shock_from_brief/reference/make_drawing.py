#!/usr/bin/env python3
"""Generate visible/drawing.png for oblique_shock_from_brief.

Annotated schematic of the 10-degree wedge channel: domain 1.0 m x 0.8 m,
wedge apex at (0.2, 0), wedge surface at theta = 10 deg, boundary roles
(inlet / supersonic outlet / slip walls / symmetry), the analytical
weak-solution shock position (beta = 39.31384 deg, dashed) and the
x = 0.6 m sampling line with the y = 0.15 m probe point. Every annotated
number MUST match the engineering brief (visible/task.md) and the source
verification case cases/verification/oblique_shock — the drawing is part
of the frozen visible/ task surface.

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
from matplotlib.patches import Polygon

# Geometry (must match visible/task.md and the source case blockMeshDict).
X_MAX = 1.0
Y_MAX = 0.8
APEX_X = 0.2
THETA_DEG = 10.0
BETA_DEG = 39.31384  # weak-solution shock angle (gen_reference.py)
X_CUT = 0.6
PROBE_Y = 0.15

THETA = math.radians(THETA_DEG)
BETA = math.radians(BETA_DEG)
WEDGE_Y_OUT = (X_MAX - APEX_X) * math.tan(THETA)  # ~0.1411
WEDGE_Y_CUT = (X_CUT - APEX_X) * math.tan(THETA)  # ~0.0705
SHOCK_Y_OUT = (X_MAX - APEX_X) * math.tan(BETA)  # ~0.655 < 0.8
SHOCK_Y_CUT = (X_CUT - APEX_X) * math.tan(BETA)  # ~0.3276

CASE_DIR = Path(__file__).resolve().parent.parent
OUT = CASE_DIR / "visible" / "drawing.png"


def main() -> None:
    fig, ax = plt.subplots(figsize=(11, 7), dpi=150)

    # Flow domain.
    domain = Polygon(
        [(0, 0), (APEX_X, 0), (X_MAX, WEDGE_Y_OUT), (X_MAX, Y_MAX), (0, Y_MAX)],
        closed=True, facecolor="#eaf3fb", edgecolor="none", zorder=0,
    )
    ax.add_patch(domain)
    # Wedge body (below the wedge surface).
    wedge = Polygon(
        [(APEX_X, -0.12), (X_MAX, -0.12), (X_MAX, WEDGE_Y_OUT), (APEX_X, 0)],
        closed=True, facecolor="#d9d9d9", edgecolor="black", lw=2, zorder=1,
    )
    ax.add_patch(wedge)
    ax.text(0.7, -0.055, "wedge (inviscid slip wall)", ha="center", fontsize=10)
    # Wedge angle arc annotation.
    ax.annotate(
        "", xy=(0.62, 0.4 * math.tan(THETA)), xytext=(0.62, 0),
        arrowprops=dict(arrowstyle="-", color="black", lw=0.8, ls=":"),
    )
    ax.plot([APEX_X, 0.62], [0, 0], color="black", lw=0.8, ls=":")
    ax.text(0.66, 0.022, "theta = 10 deg", fontsize=10)

    # Analytical weak-solution shock (dashed, for orientation only).
    ax.plot(
        [APEX_X, X_MAX], [0, SHOCK_Y_OUT], color="#d62728", lw=1.6, ls="--",
    )
    ax.text(
        0.82, (0.82 - APEX_X) * math.tan(BETA) + 0.03,
        "oblique shock (weak solution, beta ~ 39.3 deg)",
        color="#d62728", fontsize=10, rotation=math.degrees(BETA),
        rotation_mode="anchor",
    )
    ax.text(0.45, 0.45, "freestream\nM1 = 2.0, gamma = 1.4\n(inviscid, steady)",
            ha="center", fontsize=11)
    ax.text(0.30, 0.115, "post-shock region (M2 ~ 1.64)", ha="center",
            fontsize=9, color="#555555", rotation=THETA_DEG)

    # Freestream arrows.
    for y in (0.45, 0.6, 0.72):
        ax.annotate("", xy=(0.30, y), xytext=(0.06, y),
                    arrowprops=dict(arrowstyle="-|>", color="#1f77b4", lw=1.8))

    # Boundaries.
    ax.plot([0, 0], [0, Y_MAX], color="#1f77b4", lw=2.5)
    ax.text(-0.02, 0.42, "inlet: uniform M1 = 2.0", rotation=90, va="center",
            ha="right", color="#1f77b4", fontsize=10)
    ax.plot([X_MAX, X_MAX], [WEDGE_Y_OUT, Y_MAX], color="#2ca02c", lw=2.5)
    ax.text(X_MAX + 0.05, 0.30, "outlet: supersonic outflow", rotation=270,
            va="center", ha="center", color="#2ca02c", fontsize=10)
    ax.plot([0, APEX_X], [0, 0], color="black", lw=2.5)
    ax.text(0.1, -0.045, "symmetry / slip", ha="center", fontsize=9)
    ax.plot([0, X_MAX], [Y_MAX, Y_MAX], color="black", lw=2.5)
    ax.text(0.5, Y_MAX + 0.025, "top: symmetry / slip (stays pure freestream)",
            ha="center", fontsize=9)

    # Sampling line and probe point.
    ax.plot([X_CUT, X_CUT], [WEDGE_Y_CUT, 0.45], color="#9467bd", lw=2)
    ax.plot(X_CUT, PROBE_Y, marker="o", ms=7, color="#9467bd", zorder=5)
    ax.annotate(
        "sampling line x = 0.6 m\n(mach_profile.csv: y, mach)",
        xy=(X_CUT, 0.45), xytext=(0.335, 0.60),
        fontsize=9, color="#9467bd",
        arrowprops=dict(arrowstyle="->", color="#9467bd", lw=1),
    )
    ax.annotate(
        "QoI probe y = 0.15 m",
        xy=(X_CUT, PROBE_Y), xytext=(0.68, 0.19),
        fontsize=9, color="#9467bd",
        arrowprops=dict(arrowstyle="->", color="#9467bd", lw=1),
    )

    # Dimensions.
    y_dim = -0.20
    ax.annotate("", xy=(X_MAX, y_dim), xytext=(0, y_dim),
                arrowprops=dict(arrowstyle="<->", color="black", lw=1.2))
    ax.plot([0, 0], [y_dim - 0.02, 0], color="black", lw=0.7, ls=":")
    ax.plot([X_MAX, X_MAX], [y_dim - 0.02, WEDGE_Y_OUT], color="black", lw=0.7, ls=":")
    ax.text(0.5, y_dim - 0.035, "L = 1.0 m", ha="center", va="top", fontsize=10)

    x_dim = -0.10
    ax.annotate("", xy=(x_dim, Y_MAX), xytext=(x_dim, 0),
                arrowprops=dict(arrowstyle="<->", color="black", lw=1.2))
    ax.plot([x_dim - 0.02, 0], [0, 0], color="black", lw=0.7, ls=":")
    ax.plot([x_dim - 0.02, 0], [Y_MAX, Y_MAX], color="black", lw=0.7, ls=":")
    ax.text(x_dim - 0.03, 0.4, "H = 0.8 m", rotation=90, va="center",
            ha="center", fontsize=10)

    y_dim2 = -0.20
    ax.annotate("", xy=(APEX_X, y_dim2 + 0.09), xytext=(0, y_dim2 + 0.09),
                arrowprops=dict(arrowstyle="<->", color="black", lw=1.0))
    ax.plot([APEX_X, APEX_X], [y_dim2 + 0.07, 0], color="black", lw=0.7, ls=":")
    ax.text(APEX_X / 2, y_dim2 + 0.115, "apex x = 0.2 m", ha="center",
            va="bottom", fontsize=9)

    # Axes hints.
    ax.annotate("x", xy=(0.10, -0.28), xytext=(0.0, -0.28),
                arrowprops=dict(arrowstyle="->", lw=1), fontsize=10)
    ax.annotate("y", xy=(-0.05, -0.20), xytext=(-0.05, -0.28),
                arrowprops=dict(arrowstyle="->", lw=1), fontsize=10)

    ax.set_xlim(-0.22, 1.22)
    ax.set_ylim(-0.36, 0.92)
    ax.set_aspect("equal")
    ax.axis("off")
    ax.set_title(
        "Supersonic flow over a 10 deg wedge (M1 = 2, inviscid) — case setup",
        fontsize=12, pad=10,
    )

    OUT.parent.mkdir(parents=True, exist_ok=True)
    fig.savefig(OUT, bbox_inches="tight")
    print(f"wrote {OUT}")


if __name__ == "__main__":
    main()
