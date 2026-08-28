#!/usr/bin/env python3
"""Generate analytic Taylor-Green vortex reference CSVs for this case.

Pure Python standard library; every number is evaluated point-by-point from
the closed-form solution of the 2D incompressible Navier-Stokes equations
for the Taylor-Green decaying vortex (Taylor & Green 1937):

    u(x,y,t) =  U0 * sin(k x) * cos(k y) * exp(-2 nu k^2 t)
    v(x,y,t) = -U0 * cos(k x) * sin(k y) * exp(-2 nu k^2 t)
    p(x,y,t) = -(rho U0^2 / 4) * (cos(2 k x) + cos(2 k y)) * exp(-4 nu k^2 t)

(icoFoam solves kinematic pressure, i.e. rho = 1.) The domain-averaged
kinetic energy per unit mass is

    KE(t) = U0^2 / 4 * exp(-4 nu k^2 t)

so KE(t)/KE(0) = exp(-4 nu k^2 t).

Case parameters (must match system/ and constant/ dictionaries):
    domain [0, 2*pi]^2, 64x64x1 mesh, U0 = 1 m/s, k = 1 1/m, nu = 0.01 m^2/s
    -> Re = U0 / (k nu) = 100, endTime t = 5 s, write interval 0.5 s.

Outputs (written next to this script):
    tgv_sample_line_t5.csv  analytic (u, v, p) at t = 5 s sampled at the 64
                            cell centres of mesh row j = 5 (y = 11*pi/32),
                            the same points system/controlDict's `sets`
                            functionObject samples with cellPoint.
    tgv_ke_decay.csv        analytic mean kinetic energy and KE(t)/KE(0) at
                            every write time t = 0, 0.5, ..., 5.0 s.

Nothing here is hand-typed: values come straight from the formulas above.
Regenerate with:  python3 generate.py
"""

import csv
import math
from pathlib import Path

# --- case parameters (single source of truth) -------------------------------
U0 = 1.0            # vortex amplitude [m/s]
K = 1.0             # wave number [1/m]
NU = 0.01           # kinematic viscosity [m^2/s]  -> Re = U0/(K*NU) = 100
N = 64              # cells per direction (must match blockMeshDict)
LENGTH = 2.0 * math.pi
T_END = 5.0         # final time [s] (must match controlDict endTime)
WRITE_DT = 0.5      # write interval [s] (must match controlDict writeInterval)
J_LINE = 5          # mesh row sampled for the line reference (y = (j+0.5)*dx)
OUT_DIR = Path(__file__).resolve().parent


def decay(t: float) -> float:
    """Velocity amplitude decay factor exp(-2 nu k^2 t)."""
    return math.exp(-2.0 * NU * K * K * t)


def ke_ratio(t: float) -> float:
    """KE(t)/KE(0) = exp(-4 nu k^2 t)."""
    return math.exp(-4.0 * NU * K * K * t)


def u_exact(x: float, y: float, t: float) -> float:
    return U0 * math.sin(K * x) * math.cos(K * y) * decay(t)


def v_exact(x: float, y: float, t: float) -> float:
    return -U0 * math.cos(K * x) * math.sin(K * y) * decay(t)


def p_exact(x: float, y: float, t: float) -> float:
    """Kinematic pressure (rho = 1)."""
    return -0.25 * U0 * U0 * (math.cos(2.0 * K * x) + math.cos(2.0 * K * y)) * ke_ratio(t)


def fmt(value: float) -> str:
    """17 significant digits: exact double round-trip."""
    return f"{value:.17g}"


def write_sample_line() -> Path:
    dx = LENGTH / N
    y = (J_LINE + 0.5) * dx
    path = OUT_DIR / "tgv_sample_line_t5.csv"
    with path.open("w", newline="", encoding="utf-8") as fh:
        writer = csv.writer(fh)
        writer.writerow(["x", "y", "u_exact", "v_exact", "p_exact"])
        for i in range(N):
            x = (i + 0.5) * dx
            writer.writerow(
                [
                    fmt(x),
                    fmt(y),
                    fmt(u_exact(x, y, T_END)),
                    fmt(v_exact(x, y, T_END)),
                    fmt(p_exact(x, y, T_END)),
                ]
            )
    return path


def write_ke_decay() -> Path:
    path = OUT_DIR / "tgv_ke_decay.csv"
    n_writes = int(round(T_END / WRITE_DT))
    with path.open("w", newline="", encoding="utf-8") as fh:
        writer = csv.writer(fh)
        writer.writerow(["t", "ke_mean_exact", "ke_ratio_exact"])
        for w in range(n_writes + 1):
            t = w * WRITE_DT
            writer.writerow([fmt(t), fmt(0.25 * U0 * U0 * ke_ratio(t)), fmt(ke_ratio(t))])
    return path


def main() -> None:
    line = write_sample_line()
    ke = write_ke_decay()
    print(f"wrote {line.name}: {N} points at y={(J_LINE + 0.5) * LENGTH / N:.10f}, t={T_END}")
    print(f"wrote {ke.name}: t = 0..{T_END} step {WRITE_DT}")
    print(f"QoI anchors: ke_ratio_end = {ke_ratio(T_END):.17g}, "
          f"u_line amplitude at t={T_END} = {decay(T_END):.17g}")


if __name__ == "__main__":
    main()
