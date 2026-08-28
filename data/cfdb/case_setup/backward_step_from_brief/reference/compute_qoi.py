#!/usr/bin/env python3
"""Compute QoI reattachment_x_over_h for backward_step_from_brief (evidence mode).

Reads the evidence bundle's bottom-wall shear distribution:

    <submission>/evidence/samples/wall_shear.csv

Contract (documented column-by-column in visible/task.md): header
exactly ``x,tau_w``; one row per wall station downstream of the step.

- ``x``: streamwise coordinate [m] from the step face (x = 0), x >= 0,
  strictly increasing, at least 10 stations, coverage to x >= 0.05 m
  (5h);
- ``tau_w``: signed wall shear stress [Pa] (positive = near-wall flow in
  +x, negative inside the recirculation bubble).

The primary reattachment point x_r is the first negative-to-positive
zero crossing of tau_w, located by linear interpolation between the
bracketing stations. The QoI is x_r / h with h = 0.01 m (step height) —
the same definition as the source validation case
backward_facing_step_laminar (near-wall sign-change proxy standard in
the BFS literature).

cfdb qoi_script protocol: ``python3 reference/compute_qoi.py <submission
dir>``; the last non-empty stdout line is a JSON object. Pure Python
standard library; exits non-zero when the evidence is missing, violates
the documented contract, or shows no recirculation (never fabricates a
value).
"""

from __future__ import annotations

import csv
import json
import math
import sys
from pathlib import Path

STEP_HEIGHT = 0.01  # h [m]
MIN_STATIONS = 10
MIN_COVERAGE = 0.05  # m, stations must reach at least x = 5h

SAMPLE = Path("evidence") / "samples" / "wall_shear.csv"


def load_stations(path: Path) -> list[tuple[float, float]]:
    rows = [r for r in csv.reader(path.read_text(encoding="utf-8").splitlines()) if r]
    if len(rows) == 0:
        raise SystemExit(f"{path}: empty file")
    header = [c.strip() for c in rows[0]]
    if header != ["x", "tau_w"]:
        raise SystemExit(f"{path}: header must be exactly 'x,tau_w', got {header!r}")
    stations: list[tuple[float, float]] = []
    for lineno, row in enumerate(rows[1:], start=2):
        if len(row) != 2:
            raise SystemExit(f"{path} line {lineno}: expected 2 columns, got {len(row)}")
        try:
            x, tau = (float(c) for c in row)
        except ValueError as e:
            raise SystemExit(f"{path} line {lineno}: non-numeric cell: {e}")
        if not math.isfinite(x) or not math.isfinite(tau):
            raise SystemExit(f"{path} line {lineno}: non-finite value")
        stations.append((x, tau))
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
    xs = [s[0] for s in stations]
    if xs[0] < 0.0:
        raise SystemExit(f"{path}: stations must start at or downstream of the step face (x >= 0)")
    for i in range(1, len(xs)):
        if xs[i] <= xs[i - 1]:
            raise SystemExit(
                f"{path}: x must be strictly increasing "
                f"({xs[i - 1]:g} -> {xs[i]:g} at row {i + 1})"
            )
    if xs[-1] < MIN_COVERAGE:
        raise SystemExit(
            f"{path}: last station x={xs[-1]:g} m does not reach the documented "
            f"coverage x >= {MIN_COVERAGE} m (5h)"
        )
    taus = [s[1] for s in stations]
    for i in range(len(stations) - 1):
        if taus[i] < 0.0 <= taus[i + 1]:
            frac = -taus[i] / (taus[i + 1] - taus[i])
            x_r = xs[i] + frac * (xs[i + 1] - xs[i])
            print(json.dumps({"reattachment_x_over_h": x_r / STEP_HEIGHT}))
            return
    raise SystemExit(
        "no negative->positive tau_w zero crossing found: either the "
        "recirculation bubble is absent (unconverged / wrong physics) or it "
        "extends past the sampled wall. Refusing to fabricate a QoI value."
    )


if __name__ == "__main__":
    main()
