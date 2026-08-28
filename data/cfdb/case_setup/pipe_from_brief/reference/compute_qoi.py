#!/usr/bin/env python3
"""Compute QoIs u_max and wall_u_avg for pipe_from_brief (evidence mode).

Physics and QoI definitions are inherited from the verified
cases/verification/pipe_poiseuille (u_max = 2*U_mean, wall value exactly 0
on a correct no-slip wall); the input side is re-expressed against the
solver-agnostic evidence bundle (see provenance.yaml for the lineage).

Reads the sampled radial profile from the submission's evidence bundle:

    <submission>/evidence/samples/profile.csv

Evidence contract (documented per-column in visible/task.md): CSV with
header ``r,u`` — ``r`` is the radial distance from the pipe axis [m],
``u`` the axial velocity [m/s] at the axial station x = 0.1 m at the
final (developed) state. At least 10 points with 0 <= r <= R, ordered by
ascending r. The LAST point must sit ON the wall (r = R = 0.005 m) and
carry the wall BOUNDARY value — for a correct no-slip wall that is
exactly 0. (Interior points may be cell-centre or node values; the wall
endpoint is anchored to the boundary value because interior line
sampling on a coarse mesh extrapolates a spurious slip velocity — the
pit documented by the source verification case.)

QoIs:

    u_max      = max(u) over the profile rows   (reference 2*U_mean = 0.2)
    wall_u_avg = u at the wall endpoint r = R   (reference 0.0, absolute)

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

R = 0.005  # m, pipe radius
PROFILE_REL = Path("evidence") / "samples" / "profile.csv"
ENDPOINT_TOL = 1e-9  # m; wall-endpoint anchoring tolerance
MIN_POINTS = 10


def load_profile(path: Path) -> list[tuple[float, float]]:
    """Parse (r, u) rows from the evidence profile CSV."""
    if not path.is_file():
        raise SystemExit(f"evidence profile missing: {path}")
    points: list[tuple[float, float]] = []
    with path.open(newline="", encoding="utf-8") as fh:
        reader = csv.DictReader(fh)
        fields = set(reader.fieldnames or [])
        if "r" not in fields or "u" not in fields:
            raise SystemExit(
                f"profile header must contain columns 'r' and 'u', got {reader.fieldnames}"
            )
        for lineno, row in enumerate(reader, start=2):
            try:
                r = float(row["r"])
                u = float(row["u"])
            except (TypeError, ValueError) as e:
                raise SystemExit(f"profile line {lineno}: non-numeric r/u cell: {e}")
            if not (math.isfinite(r) and math.isfinite(u)):
                raise SystemExit(f"profile line {lineno}: non-finite value")
            if r < -ENDPOINT_TOL or r > R + ENDPOINT_TOL:
                raise SystemExit(
                    f"profile line {lineno}: r={r} outside [0, R={R}]"
                )
            points.append((r, u))
    if len(points) < MIN_POINTS:
        raise SystemExit(f"profile has {len(points)} points, need >= {MIN_POINTS}")
    points.sort()
    return points


def main() -> None:
    submission = Path(sys.argv[1]) if len(sys.argv) > 1 else Path.cwd()
    points = load_profile(submission / PROFILE_REL)
    r_wall, u_wall = points[-1]
    if abs(r_wall - R) > ENDPOINT_TOL:
        raise SystemExit(
            f"profile must end ON the wall (r=R={R}) with the wall boundary "
            f"value; last r={r_wall}"
        )
    u_max = max(u for _, u in points)
    print(json.dumps({"u_max": u_max, "wall_u_avg": u_wall}))


if __name__ == "__main__":
    main()
