#!/usr/bin/env python3
"""Compute QoI bottom_wall_shear_normalized for couette_from_brief (evidence mode).

Physics and QoI definition are inherited from the verified
cases/verification/couette_shear/post/compute_qoi.py; the input side is
re-expressed against the solver-agnostic evidence bundle (see
provenance.yaml for the lineage).

Reads the sampled wall-normal profile from the submission's evidence bundle:

    <submission>/evidence/samples/profile.csv

Evidence contract (documented per-column in visible/task.md): CSV with
header ``y,u`` — ``y`` is the wall-normal distance from the STATIONARY
wall [m], ``u`` the streamwise velocity [m/s] at the final (steady)
state. The sample line spans the full gap wall-to-wall: the first point
sits on the stationary wall (y = 0) and the last on the moving wall
(y = H = 0.01 m), with at least 10 points ordered by ascending y.

The QoI is the stationary-wall velocity slope from the first two sample
points, normalised by the analytical slope U_lid/H = 10 1/s
(U_lid = 0.1 m/s, H = 0.01 m):

    bottom_wall_shear_normalized = (du/dy|_0) / (U_lid / H)

Analytical value 1.0 (the developed profile u = U_lid*y/H is linear and
exactly representable on any mesh).

cfdb qoi_script protocol (evidence mode): the judge runs
``python3 reference/compute_qoi.py <submission_dir>`` on the host; the
last non-empty stdout line must be a JSON object. Pure Python standard
library; exits non-zero when the evidence is missing or malformed
(never fabricates a value).
"""

from __future__ import annotations

import csv
import json
import math
import sys
from pathlib import Path

U_LID = 0.1  # m/s, moving-wall speed
H = 0.01  # m, gap height
PROFILE_REL = Path("evidence") / "samples" / "profile.csv"
ENDPOINT_TOL = 1e-9  # m; endpoint anchoring tolerance
MIN_POINTS = 10


def load_profile(path: Path) -> list[tuple[float, float]]:
    """Parse (y, u) rows from the evidence profile CSV."""
    if not path.is_file():
        raise SystemExit(f"evidence profile missing: {path}")
    points: list[tuple[float, float]] = []
    with path.open(newline="", encoding="utf-8") as fh:
        reader = csv.DictReader(fh)
        fields = set(reader.fieldnames or [])
        if "y" not in fields or "u" not in fields:
            raise SystemExit(
                f"profile header must contain columns 'y' and 'u', got {reader.fieldnames}"
            )
        for lineno, row in enumerate(reader, start=2):
            try:
                y = float(row["y"])
                u = float(row["u"])
            except (TypeError, ValueError) as e:
                raise SystemExit(f"profile line {lineno}: non-numeric y/u cell: {e}")
            if not (math.isfinite(y) and math.isfinite(u)):
                raise SystemExit(f"profile line {lineno}: non-finite value")
            points.append((y, u))
    if len(points) < MIN_POINTS:
        raise SystemExit(f"profile has {len(points)} points, need >= {MIN_POINTS}")
    points.sort()
    return points


def main() -> None:
    submission = Path(sys.argv[1]) if len(sys.argv) > 1 else Path.cwd()
    points = load_profile(submission / PROFILE_REL)
    if abs(points[0][0]) > ENDPOINT_TOL:
        raise SystemExit(
            f"profile must start ON the stationary wall (y=0); first y={points[0][0]}"
        )
    if abs(points[-1][0] - H) > ENDPOINT_TOL:
        raise SystemExit(
            f"profile must end ON the moving wall (y=H={H}); last y={points[-1][0]}"
        )
    (y0, u0), (y1, u1) = points[0], points[1]
    if y1 <= y0:
        raise SystemExit("profile ordinate is not increasing at the stationary wall")
    slope = (u1 - u0) / (y1 - y0)
    qoi = slope / (U_LID / H)
    print(json.dumps({"bottom_wall_shear_normalized": qoi}))


if __name__ == "__main__":
    main()
