#!/usr/bin/env python3
"""Interpolate the Martin & Moyce (1952) surge-front reference curve at the
QoI dimensionless times of the dam_break case.

Reads reference/martin_moyce_1952_front.csv (same directory) and prints the
reference QoI values as JSON on stdout. The output is what goes into
case.yaml reference.qoi_values and held_out/qoi.json — numbers are produced
by linear interpolation of the frozen digitization, never hand-computed.

Pure Python standard library. Usage:

    python3 reference/interpolate_qoi.py
"""

from __future__ import annotations

import csv
import json
from pathlib import Path

# QoI sampling points in dimensionless time tau = t*sqrt(2*g/a), chosen
# inside the digitized range [0.4103, 3.0929] and before the surge front
# reaches the opposite tank wall (Z/a = 4).
QOI = {
    "front_z_tau_1_0": 1.0,
    "front_z_tau_1_5": 1.5,
    "front_z_tau_2_0": 2.0,
    "front_z_tau_2_5": 2.5,
    "front_z_tau_2_8": 2.8,
}


def load_curve(path: Path) -> tuple[list[float], list[float]]:
    taus: list[float] = []
    zs: list[float] = []
    with path.open(encoding="utf-8") as f:
        rows = (line for line in f if not line.startswith("#"))
        for row in csv.DictReader(rows):
            taus.append(float(row["tau"]))
            zs.append(float(row["z_over_a"]))
    if taus != sorted(taus):
        raise ValueError("reference curve is not sorted by tau")
    return taus, zs


def interp(taus: list[float], zs: list[float], tau: float) -> float:
    if not taus[0] <= tau <= taus[-1]:
        raise ValueError(f"tau={tau} outside digitized range [{taus[0]}, {taus[-1]}]")
    for i in range(1, len(taus)):
        if tau <= taus[i]:
            t0, t1 = taus[i - 1], taus[i]
            z0, z1 = zs[i - 1], zs[i]
            return z0 + (z1 - z0) * (tau - t0) / (t1 - t0)
    raise AssertionError("unreachable")


def main() -> None:
    csv_path = Path(__file__).resolve().parent / "martin_moyce_1952_front.csv"
    taus, zs = load_curve(csv_path)
    qoi = {name: round(interp(taus, zs, tau), 4) for name, tau in QOI.items()}
    print(json.dumps(qoi, indent=2, sort_keys=True))


if __name__ == "__main__":
    main()
