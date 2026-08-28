#!/usr/bin/env python3
"""Generate the reference Cf distribution for turbulent_flat_plate.

Reference is the engineering 1/7-power-law correlation for the local skin
friction on a smooth flat plate in a zero-pressure-gradient turbulent
boundary layer (fully turbulent from the leading edge):

    Cf(x) = 0.0592 * Re_x^(-1/5),   valid for 5e5 < Re_x < 1e7

This is an ENGINEERING CORRELATION, not raw experimental data. The
correlation form was cross-checked against independent published sources
(see provenance.yaml notes):
  - Anderson, "Introduction to Flight", 8th ed., Eq. (4.100):
    Cf_x = 0.0592 / Re_x^0.2 (turbulent)
  - Univ. of Iowa fluids course notes (Turbulent_BL): same power law,
    stated validity Re_L = 5e5..1e7 for smooth flat plates.

Every number in powerlaw_cf.csv is computed here pointwise by the formula;
nothing is hand-typed. Pure Python standard library.

Flow conditions of the case (must match case.yaml / constant/transportProperties):
  U_inf = 10 m/s, nu = 1e-5 m^2/s  ->  Re_x = 1e6 * x[m]
Stations x = 0.5 .. 2.0 m all satisfy 5e5 < Re_x < 1e7.
"""

import csv
import math
from pathlib import Path

U_INF = 10.0      # m/s, freestream velocity
NU = 1.0e-5       # m^2/s, kinematic viscosity
X_MIN = 0.5       # m, first station (Re_x = 5e5, lower validity bound)
X_MAX = 2.0       # m, plate trailing edge (Re_x = 2e6)
N_STATIONS = 7

OUT = Path(__file__).resolve().parent / "powerlaw_cf.csv"


def cf_powerlaw(re_x: float) -> float:
    """Local Cf from the 1/7-power-law engineering correlation."""
    return 0.0592 * re_x ** (-0.2)


def main() -> None:
    stations = [
        X_MIN + (X_MAX - X_MIN) * i / (N_STATIONS - 1) for i in range(N_STATIONS)
    ]
    with OUT.open("w", newline="", encoding="utf-8") as f:
        writer = csv.writer(f)
        writer.writerow(["x_m", "Re_x", "cf"])
        for x in stations:
            re_x = U_INF * x / NU
            # station Re_x = 5e5 exactly is kept (inclusive guard with a
            # 1e-6 relative epsilon for floating-point roundoff).
            eps = 1e-6 * re_x
            if not (5e5 - eps <= re_x <= 1e7 + eps):
                raise ValueError(f"station x={x} m out of correlation validity range")
            writer.writerow([f"{x:.3f}", f"{re_x:.6g}", f"{cf_powerlaw(re_x):.6f}"])
    print(f"wrote {OUT.name}: {N_STATIONS} stations, x={X_MIN}..{X_MAX} m")


if __name__ == "__main__":
    main()
