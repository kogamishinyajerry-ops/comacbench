#!/usr/bin/env python3
"""Compute QoIs cf_rex_5e5 and cf_rex_1e6 for turbulent_plate_from_brief
(evidence mode).

Reads the submitted wall skin-friction distribution along the plate:

    evidence/samples/cf_distribution.csv     header: x,cf

from the evidence bundle, linearly interpolates Cf to the QoI stations
x = 0.5 m (Re_x = 5e5) and x = 1.0 m (Re_x = 1e6), and emits

    {"cf_rex_5e5": ..., "cf_rex_1e6": ...}

Reference: 1/7-power-law engineering correlation
Cf = 0.0592*Re_x^(-1/5) with U_inf = 10 m/s, nu = 1e-5 m^2/s (see the
source validation case cases/validation/turbulent_flat_plate,
reference/generate.py); held_out/qoi.json carries those values.

cfdb qoi_script protocol (evidence mode):
``python3 reference/compute_qoi.py <submission_dir>``; the last non-empty
stdout line is a JSON object. Pure Python standard library; exits non-zero
when the distribution is missing, malformed, or does not bracket a QoI
station (never fabricates a value).
"""

from __future__ import annotations

import csv
import json
import math
import sys
from pathlib import Path

PROFILE = Path("evidence") / "samples" / "cf_distribution.csv"
STATIONS = {"cf_rex_5e5": 0.5, "cf_rex_1e6": 1.0}


def load_distribution(path: Path) -> list[tuple[float, float]]:
    try:
        text = path.read_text(encoding="utf-8")
    except (OSError, UnicodeDecodeError) as e:
        raise SystemExit(f"cannot read {path}: {e}")
    rows = [row for row in csv.reader(text.splitlines()) if len(row) > 0]
    if len(rows) < 3:
        raise SystemExit(f"{path}: need a header row plus at least 2 data rows")
    header = [c.strip().lower() for c in rows[0]]
    try:
        ix = header.index("x")
        ic = header.index("cf")
    except ValueError:
        raise SystemExit(f"{path}: header must contain 'x' and 'cf' columns, got {rows[0]}")
    points: list[tuple[float, float]] = []
    for lineno, row in enumerate(rows[1:], start=2):
        try:
            x = float(row[ix])
            cf = float(row[ic])
        except (ValueError, IndexError) as e:
            raise SystemExit(f"{path} line {lineno}: non-numeric x/cf cell: {e}")
        if not (math.isfinite(x) and math.isfinite(cf)):
            raise SystemExit(f"{path} line {lineno}: non-finite value")
        points.append((x, cf))
    points.sort()
    deduped: list[tuple[float, float]] = []
    for x, cf in points:
        if deduped and x == deduped[-1][0]:
            deduped[-1] = (x, 0.5 * (deduped[-1][1] + cf))
        else:
            deduped.append((x, cf))
    if len(deduped) < 2:
        raise SystemExit(f"{path}: fewer than 2 distinct x stations")
    return deduped


def main() -> None:
    submission_dir = Path(sys.argv[1]) if len(sys.argv) > 1 else Path.cwd()
    dist = load_distribution(submission_dir / PROFILE)
    xs = [p[0] for p in dist]
    qoi: dict[str, float] = {}
    for name, x0 in STATIONS.items():
        if x0 < xs[0] or x0 > xs[-1]:
            raise SystemExit(
                f"station x={x0} outside distribution range {xs[0]:g}..{xs[-1]:g} "
                f"(the Cf evidence must cover all QoI stations)"
            )
        for i in range(len(dist) - 1):
            xa, ca = dist[i]
            xb, cb = dist[i + 1]
            if xa <= x0 <= xb:
                span = xb - xa
                frac = 0.0 if span == 0.0 else (x0 - xa) / span
                qoi[name] = ca + frac * (cb - ca)
                break
    print(json.dumps(qoi))


if __name__ == "__main__":
    main()
