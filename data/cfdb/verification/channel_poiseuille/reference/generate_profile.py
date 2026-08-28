#!/usr/bin/env python3
"""Generate the plane Poiseuille reference profile CSV (stdlib only).

Closed-form fully developed laminar profile between parallel plates:

    u(y) = 6 * U0 * (y/H) * (1 - y/H),   0 <= y <= H

so that the cross-sectional mean is exactly U0 and the centreline maximum
is u_max = 1.5 * U0 = 0.15 m/s for U0 = 0.1 m/s.

The CSV is computed pointwise from this formula -- no hand-typed numbers.
Run from the case directory:

    python3 reference/generate_profile.py

It rewrites reference/poiseuille_profile.csv deterministically and prints a
self-check line (grid max vs analytical 1.5*U0).
"""

from __future__ import annotations

import csv
from pathlib import Path

U0 = 0.1  # mean velocity [m/s]
H = 0.01  # channel height [m]
N = 40  # intervals -> 41 points, eta = 0, 0.025, ..., 1.0 (0.5 on grid)

OUT = Path(__file__).resolve().parent / "poiseuille_profile.csv"


def u_analytical(y_over_h: float) -> float:
    """Fully developed plane Poiseuille velocity [m/s] at y/H."""
    return 6.0 * U0 * y_over_h * (1.0 - y_over_h)


def main() -> None:
    rows = []
    for i in range(N + 1):
        eta = i / N
        rows.append((eta, u_analytical(eta)))

    with OUT.open("w", newline="", encoding="utf-8") as f:
        writer = csv.writer(f)
        writer.writerow(["y_over_H", "u_m_per_s"])
        for eta, u in rows:
            writer.writerow([f"{eta:.4f}", f"{u:.6f}"])

    grid_max = max(u for _, u in rows)
    analytical_umax = 1.5 * U0
    assert abs(grid_max - analytical_umax) < 1e-12, (grid_max, analytical_umax)
    print(
        f"wrote {OUT.name}: {len(rows)} points, "
        f"grid u_max={grid_max:.6f} m/s == 1.5*U0={analytical_umax:.6f} m/s"
    )


if __name__ == "__main__":
    main()
