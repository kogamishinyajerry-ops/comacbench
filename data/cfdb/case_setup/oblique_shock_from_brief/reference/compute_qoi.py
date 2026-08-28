#!/usr/bin/env python3
"""Compute QoI post_shock_mach for oblique_shock_from_brief (evidence mode).

Reads the submitted vertical Mach profile at x = 0.6 m:

    evidence/samples/mach_profile.csv     header: y,mach

from the evidence bundle, linearly interpolates the local Mach number to
the QoI probe height y = 0.15 m (between the wedge surface y = 0.0705 and
the analytical weak-solution shock y = 0.3276 at x = 0.6), and emits

    {"post_shock_mach": M(0.6, 0.15)}

Reference: theta-beta-M weak solution for M1=2, theta=10 deg gives
M2 = 1.640526 (see the source verification case
cases/verification/oblique_shock, gen_reference.py); held_out/qoi.json
carries that value.

cfdb qoi_script protocol (evidence mode):
``python3 reference/compute_qoi.py <submission_dir>``; the last non-empty
stdout line is a JSON object. Pure Python standard library; exits non-zero
when the profile is missing, malformed, or does not bracket y = 0.15
(never fabricates a value).
"""

from __future__ import annotations

import csv
import json
import math
import sys
from pathlib import Path

PROFILE = Path("evidence") / "samples" / "mach_profile.csv"
PROBE_Y = 0.15  # m, QoI probe height on the x = 0.6 m cut


def load_profile(path: Path) -> list[tuple[float, float]]:
    try:
        text = path.read_text(encoding="utf-8")
    except (OSError, UnicodeDecodeError) as e:
        raise SystemExit(f"cannot read {path}: {e}")
    rows = [row for row in csv.reader(text.splitlines()) if len(row) > 0]
    if len(rows) < 3:
        raise SystemExit(f"{path}: need a header row plus at least 2 data rows")
    header = [c.strip().lower() for c in rows[0]]
    try:
        iy = header.index("y")
        im = header.index("mach")
    except ValueError:
        raise SystemExit(f"{path}: header must contain 'y' and 'mach' columns, got {rows[0]}")
    points: list[tuple[float, float]] = []
    for lineno, row in enumerate(rows[1:], start=2):
        try:
            y = float(row[iy])
            m = float(row[im])
        except (ValueError, IndexError) as e:
            raise SystemExit(f"{path} line {lineno}: non-numeric y/mach cell: {e}")
        if not (math.isfinite(y) and math.isfinite(m)):
            raise SystemExit(f"{path} line {lineno}: non-finite value")
        points.append((y, m))
    points.sort()
    deduped: list[tuple[float, float]] = []
    for y, m in points:
        if deduped and y == deduped[-1][0]:
            deduped[-1] = (y, 0.5 * (deduped[-1][1] + m))
        else:
            deduped.append((y, m))
    if len(deduped) < 2:
        raise SystemExit(f"{path}: fewer than 2 distinct y stations")
    return deduped


def main() -> None:
    submission_dir = Path(sys.argv[1]) if len(sys.argv) > 1 else Path.cwd()
    profile = load_profile(submission_dir / PROFILE)
    ys = [p[0] for p in profile]
    if PROBE_Y < ys[0] or PROBE_Y > ys[-1]:
        raise SystemExit(
            f"probe y={PROBE_Y} outside profile range {ys[0]:g}..{ys[-1]:g} "
            f"(the cut must cover the post-shock region)"
        )
    mach = None
    for i in range(len(profile) - 1):
        y0, m0 = profile[i]
        y1, m1 = profile[i + 1]
        if y0 <= PROBE_Y <= y1:
            span = y1 - y0
            frac = 0.0 if span == 0.0 else (PROBE_Y - y0) / span
            mach = m0 + frac * (m1 - m0)
            break
    if mach is None:
        raise SystemExit("interpolation failed (unreachable)")
    print(json.dumps({"post_shock_mach": mach}))


if __name__ == "__main__":
    main()
