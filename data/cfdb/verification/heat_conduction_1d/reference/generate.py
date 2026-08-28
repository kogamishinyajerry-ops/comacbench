#!/usr/bin/env python3
"""Generate the analytical reference CSV for heat_conduction_1d.

1D steady heat conduction in a plane wall (thickness L) with a uniform
volumetric heat source and both faces held at T_s (Dirichlet BCs):

    -k * d2T/dx2 = q   (q = volumetric heat generation [W/m^3])
    T(0) = T(L) = T_s

Closed-form solution (Incropera & DeWitt, plane wall with generation):

    T(x) = T_s + (q / (2 k)) * x * (L - x)

In the OpenFOAM setup laplacianFoam solves dT/dt = alpha * Laplacian(T) + S
with alpha = DT = k/(rho*cp) [m^2/s] and S the per-unit-volume temperature
source [K/s] (system/fvOptions, volumeMode specific). The steady solution
depends only on the ratio q/k = S/alpha:

    q/k = S/alpha = 100 / 0.1 = 1000 K/m^2
    T(x) = 300 + 500 * x * (1 - x)   [K]
    midplane (x = L/2): T = T_s + (q/k) * L^2 / 8 = 300 + 125 = 425 K

Every number in reference/t_profile.csv is evaluated from this formula by
this script; nothing is hand-typed. Pure Python standard library.

Usage: python3 generate.py   (writes t_profile.csv next to this script)
"""

import csv
import os

# --- Case parameters (must match the OpenFOAM dictionaries) ---------------
L = 1.0          # wall thickness [m]            (blockMeshDict, x in [0, 1])
T_S = 300.0      # fixed wall temperature [K]    (0/T, both walls)
ALPHA = 0.1      # DT, thermal diffusivity [m^2/s] (constant/transportProperties)
S = 100.0        # volumetric source [K/s]       (system/fvOptions, specific)
N_CELLS = 100    # cells along x                 (blockMeshDict)

Q_OVER_K = S / ALPHA  # q/k [K/m^2] = 1000


def t_analytic(x):
    """Closed-form steady-state temperature at position x [K]."""
    return T_S + (Q_OVER_K / 2.0) * x * (L - x)


def main():
    out = os.path.join(os.path.dirname(os.path.abspath(__file__)),
                       "t_profile.csv")
    # Sample at the cell centres of the 100-cell blockMesh so the CSV lines
    # up 1:1 with the cell values laplacianFoam writes.
    with open(out, "w", newline="") as f:
        w = csv.writer(f)
        w.writerow(["x", "T_analytic"])
        for i in range(N_CELLS):
            x = (i + 0.5) * L / N_CELLS
            w.writerow([f"{x:.6f}", f"{t_analytic(x):.6f}"])
    midplane = t_analytic(0.5 * L)
    print(f"wrote {out}: {N_CELLS} cell-centre samples")
    print(f"q/k = {Q_OVER_K} K/m^2")
    print(f"midplane QoI T(L/2) = {midplane} K "
          f"(= T_s + (q/k)*L^2/8 = {T_S} + {Q_OVER_K * L * L / 8.0})")


if __name__ == "__main__":
    main()
