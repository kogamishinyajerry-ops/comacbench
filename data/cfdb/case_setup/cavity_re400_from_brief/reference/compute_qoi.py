#!/usr/bin/env python3
"""Compute QoI centerline_umax for cavity_re400_from_brief (evidence mode).

Reads the evidence bundle's centerline sample:

    <submission>/evidence/samples/centerline.csv

Contract (documented column-by-column in visible/task.md): header
exactly ``y,u,v``; one row per station on the vertical centerline
x = H/2 of the converged steady field.

- ``y``: vertical coordinate [m] above the bottom wall, 0 <= y <= 0.095
  (y/H <= 0.95 — the moving lid point is excluded by contract),
  strictly increasing, at least 10 stations, top station at y >= 0.09;
- ``u``: x-velocity component [m/s];
- ``v``: y-velocity component [m/s].

The QoI is max over stations of sqrt(u^2 + v^2) / U_LID with
U_LID = 1.0 m/s (Ghia et al. 1982 normalisation; same definition as the
source validation case lid_driven_cavity_re400).

cfdb qoi_script protocol: ``python3 reference/compute_qoi.py <submission
dir>``; the last non-empty stdout line is a JSON object. Pure Python
standard library; exits non-zero when the evidence is missing or
violates the documented contract (never fabricates a value).
"""

from __future__ import annotations

import csv
import json
import math
import sys
from pathlib import Path

H = 0.1  # m, cavity side
U_LID = 1.0  # m/s
Y_TOP = 0.095  # m, y/H = 0.95 — the moving lid is NOT sampled
Y_TOP_MIN = 0.09  # m, the sample line must reach the documented top
MIN_STATIONS = 10

SAMPLE = Path("evidence") / "samples" / "centerline.csv"


def load_stations(path: Path) -> list[tuple[float, float, float]]:
    rows = [r for r in csv.reader(path.read_text(encoding="utf-8").splitlines()) if r]
    if len(rows) == 0:
        raise SystemExit(f"{path}: empty file")
    header = [c.strip() for c in rows[0]]
    if header != ["y", "u", "v"]:
        raise SystemExit(f"{path}: header must be exactly 'y,u,v', got {header!r}")
    stations: list[tuple[float, float, float]] = []
    for lineno, row in enumerate(rows[1:], start=2):
        if len(row) != 3:
            raise SystemExit(f"{path} line {lineno}: expected 3 columns, got {len(row)}")
        try:
            y, u, v = (float(c) for c in row)
        except ValueError as e:
            raise SystemExit(f"{path} line {lineno}: non-numeric cell: {e}")
        if not all(math.isfinite(val) for val in (y, u, v)):
            raise SystemExit(f"{path} line {lineno}: non-finite value")
        stations.append((y, u, v))
    return stations


def main() -> None:
    submission = Path(sys.argv[1]) if len(sys.argv) > 1 else Path.cwd()
    path = submission / SAMPLE
    if not path.is_file():
        raise SystemExit(f"missing evidence file: {path}")
    stations = load_stations(path)
    if len(stations) < MIN_STATIONS:
        raise SystemExit(
            f"{path}: {len(stations)} stations < required minimum {MIN_STATIONS}"
        )
    ys = [s[0] for s in stations]
    for i in range(1, len(ys)):
        if ys[i] <= ys[i - 1]:
            raise SystemExit(
                f"{path}: y must be strictly increasing "
                f"({ys[i - 1]:g} -> {ys[i]:g} at row {i + 1})"
            )
    if ys[0] < 0.0 or ys[-1] > Y_TOP + 1e-12:
        raise SystemExit(
            f"{path}: stations must lie in [0, {Y_TOP}] m (bottom wall to "
            "y/H=0.95; the moving lid point is excluded by contract)"
        )
    if ys[-1] < Y_TOP_MIN:
        raise SystemExit(
            f"{path}: top station y={ys[-1]:g} m does not reach the documented "
            f"line top y/H=0.95 (need >= {Y_TOP_MIN} m)"
        )
    u_max = max(math.hypot(u, v) for _, u, v in stations) / U_LID
    print(json.dumps({"centerline_umax": u_max}))


if __name__ == "__main__":
    main()
