#!/usr/bin/env python3
"""Generate the analytical reference data for the oblique_shock case.

Solves the theta-beta-M relation for a Mach-2 flow deflected by a 10-degree
wedge (weak-solution branch) and writes:

  reference/oblique_shock_x06_profile.csv
      Exact inviscid solution sampled on the vertical probe line x = 0.6
      (the line used to compare against a CFD run): below the shock the
      post-shock (region-2) state, above it the freestream (region-1) state.

  held_out/qoi.json
      The QoI value(s), written by the same script so no number is ever
      hand-transcribed.

Gas model matches constant/thermophysicalProperties: the normalised gas of
the OpenFOAM rhoCentralFoam wedge15Ma5 tutorial (molWeight 11640.3, Cp 2.5,
i.e. gamma = 1.4 with R ~ 0.7143, T1 = 1, p1 = 1, U1 = 2 -> M1 ~ 2).

Pure Python standard library; deterministic output.

Run from the case directory:  python3 gen_reference.py
"""

import csv
import json
import math
from pathlib import Path

# --- gas / flow conditions (must match the OpenFOAM case dictionaries) ---
GAMMA = 1.4
RR = 8314.462618          # OpenFOAM universal gas constant, J/(kmol K)
MOL_WEIGHT = 11640.3      # normalised gas (wedge15Ma5 tutorial)
R = RR / MOL_WEIGHT       # specific gas constant
T1 = 1.0
P1 = 1.0
U1 = 2.0
THETA_DEG = 10.0

# --- geometry (must match constant/polyMesh/blockMeshDict) ---
X_WEDGE_START = 0.2
X_PROBE = 0.6
Y_TOP = 0.8
N_PROFILE_POINTS = 41


def theta_of_beta(beta: float, m1: float) -> float:
    """Theta-beta-M relation: flow deflection for a given shock angle."""
    return math.atan(
        2.0 / math.tan(beta)
        * (m1**2 * math.sin(beta) ** 2 - 1.0)
        / (m1**2 * (GAMMA + math.cos(2.0 * beta)) + 2.0)
    )


def solve_weak_beta(m1: float, theta: float) -> float:
    """Weak-solution shock angle by bisection on the rising branch.

    theta(beta) rises from 0 at the Mach angle mu to theta_max, then falls
    back to 0 at beta = 90 deg. The weak solution lies on [mu, beta_peak].
    """
    mu = math.asin(1.0 / m1)
    # locate the peak (theta_max) with a plain scan
    n = 4000
    betas = [mu + (0.5 * math.pi - mu) * i / n for i in range(1, n)]
    b_peak = max(betas, key=lambda b: theta_of_beta(b, m1))
    if theta_of_beta(b_peak, m1) < theta:
        raise ValueError("deflection exceeds theta_max: shock is detached")
    lo, hi = mu + 1e-12, b_peak
    for _ in range(200):
        mid = 0.5 * (lo + hi)
        if theta_of_beta(mid, m1) < theta:
            lo = mid
        else:
            hi = mid
    return 0.5 * (lo + hi)


def main() -> None:
    case_dir = Path(__file__).resolve().parent

    a1 = math.sqrt(GAMMA * R * T1)
    m1 = U1 / a1
    theta = math.radians(THETA_DEG)

    beta = solve_weak_beta(m1, theta)

    # Rankine-Hugoniot jump across the shock (normal component)
    mn1 = m1 * math.sin(beta)
    mn2 = math.sqrt(
        (1.0 + 0.5 * (GAMMA - 1.0) * mn1**2) / (GAMMA * mn1**2 - 0.5 * (GAMMA - 1.0))
    )
    m2 = mn2 / math.sin(beta - theta)
    p2_over_p1 = 1.0 + 2.0 * GAMMA / (GAMMA + 1.0) * (mn1**2 - 1.0)
    rho2_over_rho1 = (GAMMA + 1.0) * mn1**2 / ((GAMMA - 1.0) * mn1**2 + 2.0)
    t2_over_t1 = p2_over_p1 / rho2_over_rho1

    rho1 = P1 / (R * T1)
    p2, rho2, t2 = P1 * p2_over_p1, rho1 * rho2_over_rho1, T1 * t2_over_t1
    a2 = math.sqrt(GAMMA * R * t2)
    u2 = m2 * a2  # post-shock flow is parallel to the wedge (theta = 10 deg)
    ux2, uy2 = u2 * math.cos(theta), u2 * math.sin(theta)

    # shock line: straight from the wedge corner (X_WEDGE_START, 0)
    y_wedge = (X_PROBE - X_WEDGE_START) * math.tan(theta)
    y_shock = (X_PROBE - X_WEDGE_START) * math.tan(beta)

    csv_path = case_dir / "reference" / "oblique_shock_x06_profile.csv"
    csv_path.parent.mkdir(exist_ok=True)
    with csv_path.open("w", newline="") as f:
        w = csv.writer(f)
        w.writerow(["y", "region", "rho", "p", "T", "Ux", "Uy", "Mach"])
        for i in range(N_PROFILE_POINTS):
            y = y_wedge + (Y_TOP - y_wedge) * i / (N_PROFILE_POINTS - 1)
            if y < y_shock:
                w.writerow(
                    [f"{y:.6f}", "post_shock", f"{rho2:.6f}", f"{p2:.6f}",
                     f"{t2:.6f}", f"{ux2:.6f}", f"{uy2:.6f}", f"{m2:.6f}"]
                )
            else:
                w.writerow(
                    [f"{y:.6f}", "freestream", f"{rho1:.6f}", f"{P1:.6f}",
                     f"{T1:.6f}", f"{U1:.6f}", "0.000000", f"{m1:.6f}"]
                )

    qoi = {"post_shock_mach": round(m2, 6)}
    qoi_path = case_dir / "held_out" / "qoi.json"
    qoi_path.parent.mkdir(exist_ok=True)
    with qoi_path.open("w") as f:
        json.dump(qoi, f, indent=2)
        f.write("\n")

    print(f"M1            = {m1:.6f}  (U1={U1}, a1={a1:.6f}, R={R:.6f})")
    print(f"beta (weak)   = {math.degrees(beta):.5f} deg")
    print(f"M2            = {m2:.6f}")
    print(f"p2/p1         = {p2_over_p1:.6f}")
    print(f"rho2/rho1     = {rho2_over_rho1:.6f}")
    print(f"T2/T1         = {t2_over_t1:.6f}")
    print(f"U2            = {u2:.6f}  (Ux={ux2:.6f}, Uy={uy2:.6f})")
    print(f"y_shock(x={X_PROBE}) = {y_shock:.6f}   y_wedge = {y_wedge:.6f}")
    print(f"shock exits outlet at y = {(1.0 - X_WEDGE_START) * math.tan(beta):.6f} (< {Y_TOP})")
    print(f"wrote {csv_path.relative_to(case_dir)} and {qoi_path.relative_to(case_dir)}")


if __name__ == "__main__":
    main()
