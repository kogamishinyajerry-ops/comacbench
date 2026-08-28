#!/usr/bin/env python3
"""Compute QoI bottom_wall_shear_normalized for the couette_shear case.

Reads the latest profileSample sets output (see system/controlDict):

    postProcessing/profileSample/<time>/lineY_U.raw

v2312 raw set format writes one line per sample point:
``y ux uy uz`` (plain space-separated columns, no parentheses). The QoI
is the bottom-wall velocity slope from the first two sample points (the
first point sits ON the bottom wall, cellPoint interpolation), normalised
by the analytical slope U_lid/H = 10 1/s (U_lid = 0.1 m/s, H = 0.01 m):

    bottom_wall_shear_normalized = (du/dy|_0) / (U_lid / H)

Analytical value 1.0 (the linear profile is exact on any mesh).

cfdb qoi_script protocol: ``python3 post/compute_qoi.py <run_case_dir>``;
the last non-empty stdout line is a JSON object. Pure Python standard
library; exits non-zero when the sample is missing or malformed (never
fabricates a value).
"""

from __future__ import annotations

import json
import sys
from pathlib import Path

U_LID = 0.1  # m/s
H = 0.01  # m


def find_sample(case_dir: Path) -> Path:
    """Return the latest lineY_U sample file."""
    root = case_dir / "postProcessing" / "profileSample"
    if not root.is_dir():
        raise SystemExit(f"no sample directory: {root} (did the solver run?)")
    candidates: list[tuple[float, Path]] = []
    for time_dir in root.iterdir():
        if not time_dir.is_dir():
            continue
        for f in time_dir.glob("lineY_U.*"):
            try:
                t = float(time_dir.name)
            except ValueError:
                t = 0.0
            candidates.append((t, f))
    if not candidates:
        raise SystemExit(f"no lineY_U sample found under {root}")
    return max(candidates)[1]


def load_profile(sample_file: Path) -> list[tuple[float, float]]:
    """Parse (y, ux) rows from the raw sample file."""
    points: list[tuple[float, float]] = []
    for line in sample_file.read_text(encoding="utf-8").splitlines():
        stripped = line.strip().replace("(", " ").replace(")", " ")
        if not stripped or stripped.startswith("#"):
            continue
        parts = stripped.split()
        if len(parts) < 2:
            continue
        points.append((float(parts[0]), float(parts[1])))
    if len(points) < 2:
        raise SystemExit(f"sample file {sample_file} has fewer than 2 points")
    points.sort()
    return points


def main() -> None:
    case_dir = Path(sys.argv[1]) if len(sys.argv) > 1 else Path.cwd()
    points = load_profile(find_sample(case_dir))
    (y0, u0), (y1, u1) = points[0], points[1]
    if y1 <= y0:
        raise SystemExit("sample ordinate is not increasing at the bottom wall")
    slope = (u1 - u0) / (y1 - y0)
    qoi = slope / (U_LID / H)
    print(json.dumps({"bottom_wall_shear_normalized": qoi}))


if __name__ == "__main__":
    main()
