#!/usr/bin/env python3
"""Compute QoI hot_wall_nu_avg for natural_convection_from_brief (evidence mode).

Reads the evidence bundle's hot-wall heat flux distribution:

    <submission>/evidence/samples/hot_wall_flux.csv

Contract (documented column-by-column in visible/task.md): header
exactly ``y,q``; one row per station on the hot wall (x = 0).

- ``y``: vertical coordinate [m] along the hot wall (0 at the bottom),
  0 <= y <= 1, strictly increasing, uniformly spaced (each spacing
  within 5% of the mean spacing — equal-height strips, so the plain
  average IS the area average), full-height coverage (first station
  y <= 0.02, last y >= 0.98), at least 16 stations;
- ``q``: wall heat flux [W/m^2] (sign convention free; magnitudes are
  used).

The QoI is hot_wall_nu_avg = mean(|q|) * H / (k * dT) with H = 1 m,
k = mu*Cp/Pr = 6.437 W/(m K), dT = 10 K, i.e. mean(|q|) / 64.37 — the
same definition as the source validation case natural_convection_cavity
(dimensionless conductive heat flux across the cavity, the Nu definition
of de Vahl Davis 1983).

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

K_DT_OVER_H = 64.37  # k * dT / H = (mu*Cp/Pr) * 10 / 1 (see case.yaml)
MIN_STATIONS = 16
Y_FIRST_MAX = 0.02  # m, full-height coverage: first station near the bottom
Y_LAST_MIN = 0.98  # m, ... and last station near the top
SPACING_TOL = 0.05  # each dy within 5% of the mean dy (uniform strips)

SAMPLE = Path("evidence") / "samples" / "hot_wall_flux.csv"


def load_stations(path: Path) -> list[tuple[float, float]]:
    rows = [r for r in csv.reader(path.read_text(encoding="utf-8").splitlines()) if r]
    if len(rows) == 0:
        raise SystemExit(f"{path}: empty file")
    header = [c.strip() for c in rows[0]]
    if header != ["y", "q"]:
        raise SystemExit(f"{path}: header must be exactly 'y,q', got {header!r}")
    stations: list[tuple[float, float]] = []
    for lineno, row in enumerate(rows[1:], start=2):
        if len(row) != 2:
            raise SystemExit(f"{path} line {lineno}: expected 2 columns, got {len(row)}")
        try:
            y, q = (float(c) for c in row)
        except ValueError as e:
            raise SystemExit(f"{path} line {lineno}: non-numeric cell: {e}")
        if not math.isfinite(y) or not math.isfinite(q):
            raise SystemExit(f"{path} line {lineno}: non-finite value")
        stations.append((y, q))
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
    if ys[0] < 0.0 or ys[-1] > 1.0 + 1e-12:
        raise SystemExit(f"{path}: stations must lie in [0, 1] m (the hot wall height)")
    for i in range(1, len(ys)):
        if ys[i] <= ys[i - 1]:
            raise SystemExit(
                f"{path}: y must be strictly increasing "
                f"({ys[i - 1]:g} -> {ys[i]:g} at row {i + 1})"
            )
    if ys[0] > Y_FIRST_MAX or ys[-1] < Y_LAST_MIN:
        raise SystemExit(
            f"{path}: stations must cover the full wall height "
            f"(first y <= {Y_FIRST_MAX}, last y >= {Y_LAST_MIN}; "
            f"got {ys[0]:g} .. {ys[-1]:g})"
        )
    spacings = [ys[i + 1] - ys[i] for i in range(len(ys) - 1)]
    mean_dy = sum(spacings) / len(spacings)
    for i, dy in enumerate(spacings):
        if abs(dy - mean_dy) > SPACING_TOL * mean_dy:
            raise SystemExit(
                f"{path}: stations must be uniformly spaced (spacing at row "
                f"{i + 2} is {dy:g} m, mean {mean_dy:g} m, tolerance "
                f"{SPACING_TOL:.0%}) — equal-height strips make the plain "
                "average the area average"
            )
    q_avg = sum(abs(q) for _, q in stations) / len(stations)
    print(json.dumps({"hot_wall_nu_avg": q_avg / K_DT_OVER_H}))


if __name__ == "__main__":
    main()
