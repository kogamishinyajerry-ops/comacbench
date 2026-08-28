#!/usr/bin/env python3
"""Generate reference/uplus_yplus.csv from the official MKM1999 DNS data file.

Source (frozen in this repo as reference/chan180.means):
    Moser, Kim & Mansour (1999), "Direct numerical simulation of turbulent
    channel flow up to Re_tau=590", Phys. Fluids 11(4), 943-945.
    DOI: 10.1063/1.869966
    Data file: https://turbulence.oden.utexas.edu/data/MKM/chan180/profiles/chan180.means
    (official turbulence fileserver of the authors, UT Austin)

This script performs a pure machine transformation (parse -> select columns ->
write CSV). No digits are hand-edited. It also derives the bulk quantities
used as QoI reference values by trapezoidal integration of the DNS mean
profile over the half channel (normalization of the file: u_tau, h):

    U_b/u_tau = integral_0^1 U+ d(y/h)
    Cf        = tau_w / (0.5 rho U_b^2) = 2 / (U_b/u_tau)^2
    Re_b      = U_b h / nu = (U_b/u_tau) * Re_tau   (Re_tau = 178.12 per file header)

Run:  python3 generate_reference.py
Stdlib only.
"""

from __future__ import annotations

import csv
import math
from pathlib import Path

HERE = Path(__file__).resolve().parent
RAW = HERE / "reference" / "chan180.means"
OUT = HERE / "reference" / "uplus_yplus.csv"


def parse_means(path: Path) -> list[tuple[float, float, float]]:
    """Parse chan180.means -> list of (y_over_h, y_plus, U_plus)."""
    rows: list[tuple[float, float, float]] = []
    for line in path.read_text().splitlines():
        line = line.strip()
        if not line or line.startswith("#"):
            continue
        cols = line.split()
        # columns: y, y+, Umean, dUmean/dy, Wmean, dWmean/dy, Pmean
        rows.append((float(cols[0]), float(cols[1]), float(cols[2])))
    return rows


def main() -> None:
    rows = parse_means(RAW)
    assert rows[0][0] == 0.0 and math.isclose(rows[-1][0], 1.0), (
        "expected half-channel profile from y/h=0 (wall) to y/h=1 (centerline)"
    )

    with OUT.open("w", newline="") as f:
        w = csv.writer(f)
        w.writerow(["y_over_h", "y_plus", "u_plus"])
        for y, yp, up in rows:
            w.writerow([f"{y:.6e}", f"{yp:.6e}", f"{up:.6e}"])

    # Trapezoidal bulk velocity over the half channel (symmetric: same bulk
    # as the full channel).
    ub_plus = sum(
        0.5 * (rows[i][2] + rows[i - 1][2]) * (rows[i][0] - rows[i - 1][0])
        for i in range(1, len(rows))
    )
    re_tau = 178.12  # from the data file header ("Re_tau = 178.12")
    re_b = ub_plus * re_tau
    cf = 2.0 / ub_plus**2

    print(f"wrote {OUT.relative_to(HERE)} ({len(rows)} stations)")
    print(f"U_b/u_tau = {ub_plus:.6f}")
    print(f"Re_b      = {re_b:.1f}  (bulk, based on half-height h)")
    print(f"Re_tau    = {re_tau}")
    print(f"Cf        = {cf:.6e}  (based on bulk velocity)")
    print(f"U_cl/u_tau= {rows[-1][2]:.4f} (centerline)")
    # a couple of well-known spot values for cross-checking the literature
    for target in (30.0, 100.0, 178.12):
        y, yp, up = min(rows, key=lambda r: abs(r[1] - target))
        print(f"  spot: y+={yp:8.2f}  u+={up:.4f}")


if __name__ == "__main__":
    main()
