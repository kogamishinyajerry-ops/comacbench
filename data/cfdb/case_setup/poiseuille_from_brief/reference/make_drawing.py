#!/usr/bin/env python3
"""Generate visible/drawing.png for poiseuille_from_brief.

Annotated schematic of the plane channel: dimensions H = 0.01 m,
L = 0.12 m, uniform inlet velocity U0 = 0.1 m/s, walls, and the
x/H = 10 probe line. Every annotated number MUST match the golden case
configuration (cases/verification/channel_poiseuille) — the drawing is
part of the frozen visible/ task surface.

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

H = 0.01  # m, channel height (y)
L = 0.12  # m, channel length (x)
U0 = 0.1  # m/s, uniform inlet velocity
X_PROBE = 0.1  # m, probe line at x/H = 10

CASE_DIR = Path(__file__).resolve().parent.parent
OUT = CASE_DIR / "visible" / "drawing.png"


def main() -> None:
    fig, ax = plt.subplots(figsize=(11, 3.6), dpi=150)

    # Channel body (drawing units: metres, equal aspect).
    ax.add_patch(
        Rectangle((0, 0), L, H, facecolor="#eaf3fb", edgecolor="none", zorder=0)
    )

    # Walls (thick lines top/bottom with hatching marks).
    ax.plot([0, L], [H, H], color="black", lw=3, solid_capstyle="butt")
    ax.plot([0, L], [0, 0], color="black", lw=3, solid_capstyle="butt")
    for x in [i * L / 24 for i in range(25)]:
        ax.plot([x, x - 0.002], [H, H + 0.0012], color="black", lw=0.8)
        ax.plot([x, x - 0.002], [0, -0.0012], color="black", lw=0.8)
    ax.text(L * 0.5, H + 0.0028, "walls (noSlip)", ha="center", fontsize=10)

    # Inlet / outlet.
    ax.plot([0, 0], [0, H], color="#1f77b4", lw=2)
    ax.plot([L, L], [0, H], color="#2ca02c", lw=2)
    ax.text(-0.004, H * 0.5, "inlet", rotation=90, va="center", ha="right",
            color="#1f77b4", fontsize=10)
    ax.text(L + 0.004, H * 0.5, "outlet", rotation=270, va="center", ha="right",
            color="#2ca02c", fontsize=10)

    # Uniform inlet velocity arrows (plug profile).
    for y in [0.2 * H, 0.4 * H, 0.6 * H, 0.8 * H]:
        ax.annotate("", xy=(0.018, y), xytext=(0.004, y),
                    arrowprops=dict(arrowstyle="-|>", color="#1f77b4", lw=1.6))
    ax.text(0.011, H + 0.0028, f"U0 = {U0} m/s (uniform)",
            ha="center", fontsize=10, color="#1f77b4")

    # Developed parabolic profile hint near the probe line.
    import math

    ys = [H * i / 40 for i in range(41)]
    prof = [X_PROBE + 0.06 * (6 * U0 * (y / H) * (1 - y / H)) / (1.5 * U0) * 0.25
            for y in ys]
    ax.plot(prof, ys, color="#d62728", lw=1.4, ls="--")

    # Probe line at x/H = 10.
    ax.plot([X_PROBE, X_PROBE], [0, H], color="#d62728", lw=1.8)
    for i in range(20):
        y = H * (i + 0.5) / 20
        ax.plot(X_PROBE, y, marker="o", ms=3, color="#d62728")
    ax.text(X_PROBE, -0.0045, "probe line\nx/H = 10 (x = 0.1 m)",
            ha="center", va="top", fontsize=9, color="#d62728")

    # Dimension: L (below, offset under the probe-line label).
    y_dim = -0.0095
    ax.annotate("", xy=(L, y_dim), xytext=(0, y_dim),
                arrowprops=dict(arrowstyle="<->", color="black", lw=1.2))
    ax.plot([0, 0], [y_dim - 0.001, 0], color="black", lw=0.7, ls=":")
    ax.plot([L, L], [y_dim - 0.001, 0], color="black", lw=0.7, ls=":")
    ax.text(L / 2, y_dim - 0.0022, "L = 0.12 m (= 12H)", ha="center",
            va="top", fontsize=10)

    # Dimension: H (left).
    x_dim = -0.014
    ax.annotate("", xy=(x_dim, H), xytext=(x_dim, 0),
                arrowprops=dict(arrowstyle="<->", color="black", lw=1.2))
    ax.plot([x_dim - 0.0015, 0], [0, 0], color="black", lw=0.7, ls=":")
    ax.plot([x_dim - 0.0015, 0], [H, H], color="black", lw=0.7, ls=":")
    ax.text(x_dim - 0.0035, H / 2, "H = 0.01 m", rotation=90, va="center",
            ha="center", fontsize=10)

    # Fluid annotation.
    ax.text(L * 0.62, H * 0.5,
            "incompressible laminar flow\nν = 5e-5 m²/s   Re_H = 20",
            ha="center", va="center", fontsize=10)

    # Axes hints.
    ax.annotate("x", xy=(0.012, -0.0028), xytext=(0.002, -0.0028),
                arrowprops=dict(arrowstyle="->", lw=1), fontsize=10)
    ax.annotate("y", xy=(-0.004, 0.0022), xytext=(-0.004, -0.0028),
                arrowprops=dict(arrowstyle="->", lw=1), fontsize=10)

    ax.set_xlim(-0.026, L + 0.014)
    ax.set_ylim(-0.016, H + 0.007)
    ax.set_aspect("equal")
    ax.axis("off")
    ax.set_title("Plane channel (2D) — Poiseuille laminar flow case setup",
                 fontsize=12, pad=10)

    OUT.parent.mkdir(parents=True, exist_ok=True)
    fig.savefig(OUT, bbox_inches="tight")
    print(f"wrote {OUT}")


if __name__ == "__main__":
    main()
