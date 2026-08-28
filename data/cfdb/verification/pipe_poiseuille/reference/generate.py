#!/usr/bin/env python3
"""Generate the Hagen-Poiseuille analytical reference profile (stdlib only).

Closed-form solution for fully developed laminar flow in a circular pipe:

    u(r) = 2 * U_mean * (1 - (r/R)^2)      (u_max = 2 * U_mean at r = 0)

Case parameters (must match case.yaml / system/ dictionaries):
    R      = 0.005 m   (pipe radius)
    L      = 0.12 m    (pipe length)
    U_mean = 0.1 m/s   (cross-section mean velocity)
    nu     = 5e-5 m2/s -> Re_D = U_mean * 2R / nu = 20

The script writes reference/radial_profile.csv deterministically and runs
self-checks so the file can never silently encode a wrong formula:
  1. u(0) == 2 * U_mean exactly (u_max = 0.2 m/s)
  2. u(R) == 0 exactly (no-slip wall point, r_over_R = 1.0)
  3. high-resolution area average of the tabulated profile recovers U_mean
     (the defining property that u_max = 2 * U_mean is mass-consistent)

Usage:  python3 reference/generate.py   (from the case directory)
"""

import csv
import math
from pathlib import Path

R = 0.005        # pipe radius [m]
L = 0.12         # pipe length [m]
U_MEAN = 0.1     # cross-section mean velocity [m/s]
NU = 5e-5        # kinematic viscosity [m^2/s]

N_POINTS = 21    # r_over_R = 0.00, 0.05, ..., 1.00 (includes axis and wall)

OUT = Path(__file__).resolve().parent / "radial_profile.csv"


def u_analytical(r: float) -> float:
    """Axial velocity at radius r (Hagen-Poiseuille)."""
    return 2.0 * U_MEAN * (1.0 - (r / R) ** 2)


def main() -> None:
    re_d = U_MEAN * 2.0 * R / NU
    print(f"Re_D = U_mean * D / nu = {re_d:.6g} (expect 20)")
    assert abs(re_d - 20.0) < 1e-9, "parameters no longer give Re_D = 20"

    rows = []
    for i in range(N_POINTS):
        r_over_R = i / (N_POINTS - 1)
        rows.append((r_over_R, u_analytical(r_over_R * R)))

    with OUT.open("w", newline="", encoding="utf-8") as f:
        w = csv.writer(f)
        w.writerow(["r_over_R", "u_ms"])
        for r_over_R, u in rows:
            w.writerow([f"{r_over_R:.2f}", f"{u:.8f}"])
    print(f"wrote {OUT} ({len(rows)} points)")

    # --- self-checks (fail loudly, never emit a quietly wrong reference) ---
    assert rows[0][1] == 2.0 * U_MEAN, "u(0) must equal u_max = 2*U_mean"
    assert rows[-1][1] == 0.0, "u(R) must be exactly 0 (no-slip)"

    # area-average self-consistency: (2/R^2) * integral(u*r, 0..R) == U_mean
    n = 20000
    dr = R / n
    integral = 0.0
    for i in range(n):
        r_mid = (i + 0.5) * dr
        integral += u_analytical(r_mid) * r_mid * dr
    u_avg = 2.0 / R**2 * integral
    err = abs(u_avg - U_MEAN) / U_MEAN
    print(f"area-average check: U_avg = {u_avg:.10f} m/s "
          f"(target {U_MEAN}, rel err {err:.2e})")
    assert err < 1e-6, "profile does not integrate back to U_mean"

    print(f"u_max = {rows[0][1]:.8f} m/s (reference QoI)")
    print("all self-checks passed")


if __name__ == "__main__":
    main()
