#!/usr/bin/env python3
"""Compute QoI utheta_midgap for the taylor_couette case.

Reads the radial sample line written by the sample_profile step
(``postProcess -func sampleDict -latestTime``, see system/sampleDict):

    postProcessing/sampleDict/<time>/radial_U.csv

CSV columns depend on the sampleDict axis: with ``axis distance`` v2312
writes ``distance,U_0,U_1,U_2`` (distance from the line start, then the
vector components); with a coordinate axis it writes ``x,y,z,U_x,U_y,U_z``.
Both are accepted. The line sits at theta = 0 (positive x axis), where the
tangential direction is +y, so u_theta = U_y exactly. The QoI is U_y at the
mid-gap radius r = 0.075 m (an exact sample point: start 0.051, 49 points,
spacing 0.001). Analytical value A*r + B/r = 0.0194444... m/s (see
reference/generate.py).

cfdb qoi_script protocol: ``python3 post/compute_qoi.py <run_case_dir>``;
the last non-empty stdout line is a JSON object. Pure Python standard
library; exits non-zero when the sample is missing or malformed (never
fabricates a value).
"""

from __future__ import annotations

import csv
import json
import sys
from pathlib import Path

R_MIDGAP = 0.075  # m
LINE_START_R = 0.051  # m (sampleDict start point, axis-distance origin)


def find_sample(case_dir: Path) -> Path:
    """Return the latest radial_U csv sample file."""
    root = case_dir / "postProcessing" / "sampleDict"
    if not root.is_dir():
        raise SystemExit(f"no sample directory: {root} (did sample_profile run?)")
    candidates: list[tuple[float, Path]] = []
    for time_dir in root.iterdir():
        if not time_dir.is_dir():
            continue
        for f in time_dir.glob("radial_U.csv"):
            try:
                t = float(time_dir.name)
            except ValueError:
                t = 0.0
            candidates.append((t, f))
    if not candidates:
        raise SystemExit(f"no radial_U.csv found under {root}")
    return max(candidates)[1]


def main() -> None:
    case_dir = Path(sys.argv[1]) if len(sys.argv) > 1 else Path.cwd()
    sample = find_sample(case_dir)
    best: tuple[float, float] | None = None  # (|r - R_MIDGAP|, u_theta)
    with sample.open(newline="", encoding="utf-8") as fh:
        for row in csv.DictReader(fh):
            # axis distance writes 'distance,U_0,U_1,U_2'; a coordinate axis
            # writes 'x,y,z,U_x,U_y,U_z' — accept both.
            if "distance" in row:
                r = LINE_START_R + float(row["distance"])
                u_theta = float(row["U_1"])
            else:
                r = float(row["x"])
                u_theta = float(row["U_y"])
            dist = abs(r - R_MIDGAP)
            if best is None or dist < best[0]:
                best = (dist, u_theta)
    if best is None:
        raise SystemExit(f"no sample rows parsed from {sample}")
    if best[0] > 1e-6:
        raise SystemExit(
            f"no sample point at r = {R_MIDGAP} m (nearest is {best[0]} m off)"
        )
    print(json.dumps({"utheta_midgap": best[1]}))


if __name__ == "__main__":
    main()
