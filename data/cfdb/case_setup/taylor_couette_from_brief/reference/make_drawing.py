#!/usr/bin/env python3
"""Generate visible/drawing.png for taylor_couette_from_brief.

Annotated schematic of the concentric-cylinder annulus: R_i = 0.05 m
rotating at omega = 1 rad/s, R_o = 0.10 m stationary, and the radial
sample line on the +x ray (theta = 0) with the mid-gap station
r = 0.075 m. Every annotated number MUST match the engineering brief
(visible/task.md) — the drawing is part of the frozen visible/ task
surface.

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
from matplotlib.patches import Circle, Wedge

R_I = 0.05  # m, inner cylinder radius
R_O = 0.10  # m, outer cylinder radius
OMEGA = 1.0  # rad/s, inner cylinder angular velocity
R_MID = 0.075  # m, mid-gap sample station

CASE_DIR = Path(__file__).resolve().parent.parent
OUT = CASE_DIR / "visible" / "drawing.png"


def main() -> None:
    fig, ax = plt.subplots(figsize=(7.2, 7.0), dpi=150)

    # Annular gap (fluid region).
    ax.add_patch(Wedge((0, 0), R_O, 0, 360, width=R_O - R_I,
                       facecolor="#eaf3fb", edgecolor="none", zorder=0))
    # Cylinder walls.
    ax.add_patch(Circle((0, 0), R_O, fill=False, edgecolor="black", lw=3))
    ax.add_patch(Circle((0, 0), R_I, fill=False, edgecolor="black", lw=3))
    ax.add_patch(Circle((0, 0), R_I * 0.96, facecolor="#dddddd",
                        edgecolor="none", zorder=1))

    # Rotation arrow on the inner cylinder (curved).
    import numpy as np

    th = np.linspace(0.35, 1.45, 40)
    rr = R_I * 0.72
    ax.plot(rr * np.cos(th), rr * np.sin(th), color="#d62728", lw=2, zorder=2)
    ax.annotate("", xy=(rr * np.cos(th[-1]) - 0.004, rr * np.sin(th[-1]) + 0.010),
                xytext=(rr * np.cos(th[-1]), rr * np.sin(th[-1])),
                arrowprops=dict(arrowstyle="-|>", color="#d62728", lw=2), zorder=2)
    ax.text(0, -0.014, "inner cylinder\nomega = 1 rad/s\n(wall speed 0.05 m/s)",
            ha="center", va="center", fontsize=9.5, color="#d62728", zorder=3)
    ax.text(-R_O * 1.02, R_O * 0.98, "outer cylinder\nstationary (no-slip)",
            ha="left", va="center", fontsize=9.5)

    # Radial sample line on the +x ray (theta = 0).
    ax.plot([R_I, R_O], [0, 0], color="#2ca02c", lw=2, zorder=2)
    for i in range(10):
        r = R_I + (R_O - R_I) * (i + 0.5) / 10
        ax.plot(r, 0, marker="o", ms=3.5, color="#2ca02c", zorder=3)
    ax.plot(R_MID, 0, marker="s", ms=6, color="#d62728", zorder=4)
    ax.annotate("mid-gap station\nr = 0.075 m", xy=(R_MID, 0),
                xytext=(0.098, -0.033), fontsize=9.5, color="#d62728",
                arrowprops=dict(arrowstyle="->", color="#d62728", lw=1))
    ax.text(0.062, 0.008, "radial sample line (theta = 0, +x ray)",
            fontsize=9.5, color="#2ca02c", ha="center")

    # u_theta direction hint at the sample line (tangent = +y at theta=0).
    ax.annotate("", xy=(0.062, 0.020), xytext=(0.062, 0.008),
                arrowprops=dict(arrowstyle="-|>", color="#2ca02c", lw=1.4))
    ax.text(0.0665, 0.017, "u_theta > 0", fontsize=9, color="#2ca02c")

    # Dimension: R_i.
    ax.annotate("", xy=(R_I * np.cos(3.6), R_I * np.sin(3.6)), xytext=(0, 0),
                arrowprops=dict(arrowstyle="<->", color="black", lw=1.2))
    ax.text(-0.028, -0.052, "R_i = 0.05 m", fontsize=10, ha="center")

    # Dimension: R_o.
    ax.annotate("", xy=(R_O * np.cos(2.25), R_O * np.sin(2.25)), xytext=(0, 0),
                arrowprops=dict(arrowstyle="<->", color="black", lw=1.2))
    ax.text(-0.075, 0.062, "R_o = 0.10 m", fontsize=10, ha="center")

    # Fluid annotation.
    ax.text(0, -R_O * 1.14,
            "incompressible laminar flow in the gap   nu = 1e-3 m^2/s   Re = 2.5",
            ha="center", va="center", fontsize=10)

    # Axes hints.
    ax.annotate("x", xy=(0.024, -R_O * 1.24), xytext=(0.004, -R_O * 1.24),
                arrowprops=dict(arrowstyle="->", lw=1), fontsize=10)
    ax.annotate("y", xy=(-0.016, -R_O * 1.24 + 0.020), xytext=(-0.016, -R_O * 1.24),
                arrowprops=dict(arrowstyle="->", lw=1), fontsize=10)

    lim = R_O * 1.32
    ax.set_xlim(-lim, lim)
    ax.set_ylim(-lim, lim * 0.98)
    ax.set_aspect("equal")
    ax.axis("off")
    ax.set_title("Taylor-Couette (circular Couette, laminar) — case setup",
                 fontsize=12, pad=10)

    OUT.parent.mkdir(parents=True, exist_ok=True)
    fig.savefig(OUT, bbox_inches="tight")
    print(f"wrote {OUT}")


if __name__ == "__main__":
    main()
