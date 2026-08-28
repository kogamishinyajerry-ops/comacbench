#!/usr/bin/env python3
"""Compute QoI midplane_T for the heat_conduction_from_brief case
(case_setup, EVIDENCE mode).

Reads the submitted steady-state temperature profile:

    <submission>/evidence/samples/profile.csv     header: x,temperature
        x            sample coordinate along the wall thickness [m],
                     strictly increasing, covering [0, 1]
        temperature  temperature at that point [K] (named 'temperature',
                     NOT 'T': the judge's generic CSV check treats any
                     case-insensitive 't' header as a time axis)

midplane_T is the linear interpolation of the profile at x = L/2 = 0.5 m
(on a uniform cell-centred grid this is the plain mean of the two
bracketing cells — the same reduction as the verified source case
cases/verification/heat_conduction_1d, whose post/compute_qoi.py takes
the mean of cells 49/50 at x = 0.495 / 0.505). Analytical value 425.0 K
(T(x) = 300 + 500*x*(1-x); Incropera & DeWitt plane wall with uniform
generation).

cfdb qoi_script protocol: ``python3 reference/compute_qoi.py <submission
dir>``; the last non-empty stdout line is a JSON object. Pure Python
standard library; exits non-zero when the evidence is missing or
malformed (never fabricates a value).
"""

from __future__ import annotations

import csv
import json
import math
import sys
from pathlib import Path

LENGTH = 1.0
X_MID = 0.5 * LENGTH
MIN_POINTS = 20

PROFILE = Path("evidence") / "samples" / "profile.csv"


def load_profile(path: Path) -> list[tuple[float, float]]:
    try:
        text = path.read_text(encoding="utf-8")
    except (OSError, UnicodeDecodeError) as e:
        raise SystemExit(f"cannot read {path}: {e}")
    rows = [row for row in csv.reader(text.splitlines()) if len(row) > 0]
    if len(rows) < 2:
        raise SystemExit(f"{path}: needs a header row and at least one data row")
    header = [cell.strip() for cell in rows[0]]
    if header != ["x", "temperature"]:
        raise SystemExit(
            f"{path}: header must be exactly 'x,temperature', got {header!r}"
        )
    samples: list[tuple[float, float]] = []
    for lineno, row in enumerate(rows[1:], start=2):
        if len(row) != 2:
            raise SystemExit(f"{path} line {lineno}: expected 2 columns, got {len(row)}")
        try:
            x = float(row[0])
            t = float(row[1])
        except ValueError:
            raise SystemExit(f"{path} line {lineno}: non-numeric cell {row!r}")
        if not (math.isfinite(x) and math.isfinite(t)):
            raise SystemExit(f"{path} line {lineno}: non-finite value {row!r}")
        samples.append((x, t))
    return samples


def main() -> None:
    submission_dir = Path(sys.argv[1]) if len(sys.argv) > 1 else Path.cwd()
    samples = load_profile(submission_dir / PROFILE)
    if len(samples) < MIN_POINTS:
        raise SystemExit(f"profile has {len(samples)} points, need at least {MIN_POINTS}")
    for (x0, _), (x1, _) in zip(samples, samples[1:]):
        if x1 <= x0:
            raise SystemExit(f"profile x coordinates not strictly increasing at x={x0:g}")
    if samples[0][0] > X_MID or samples[-1][0] < X_MID:
        raise SystemExit(
            f"profile range [{samples[0][0]:g}, {samples[-1][0]:g}] does not cover "
            f"the midplane x={X_MID:g}"
        )
    # Linear interpolation at x = L/2 between the bracketing samples.
    for (x0, t0), (x1, t1) in zip(samples, samples[1:]):
        if x0 <= X_MID <= x1:
            frac = 0.0 if x1 == x0 else (X_MID - x0) / (x1 - x0)
            midplane_t = t0 + frac * (t1 - t0)
            break
    else:  # pragma: no cover - the coverage check above guarantees a hit
        raise SystemExit("no bracketing samples for the midplane")
    print(json.dumps({"midplane_T": midplane_t}))


if __name__ == "__main__":
    main()
