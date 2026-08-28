#!/usr/bin/env python3
"""Compute QoI utheta_midgap for taylor_couette_from_brief (evidence mode).

Physics and QoI definition are inherited from the verified
cases/verification/taylor_couette/post/compute_qoi.py; the input side is
re-expressed against the solver-agnostic evidence bundle (see
provenance.yaml for the lineage).

Reads the sampled radial tangential-velocity profile from the
submission's evidence bundle:

    <submission>/evidence/samples/profile.csv

Evidence contract (documented per-column in visible/task.md): CSV with
header ``r,u_theta`` — ``r`` is the radial distance from the common
cylinder axis [m], ``u_theta`` the circumferential velocity component
(positive in the inner cylinder's rotation direction) [m/s] at the final
(steady) state. At least 10 points with R_i <= r <= R_o, ordered by
ascending r, and one point MUST sit at the mid-gap radius
r = 0.075 m (within 1e-6 m).

QoI:

    utheta_midgap = u_theta at r = 0.075 m
                  (closed-form reference A*r + B/r = 0.0194444... m/s)

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

R_I = 0.05  # m, inner cylinder radius
R_O = 0.10  # m, outer cylinder radius
R_MIDGAP = 0.075  # m
PROFILE_REL = Path("evidence") / "samples" / "profile.csv"
STATION_TOL = 1e-6  # m; the mid-gap station must be an actual sample point
MIN_POINTS = 10


def load_profile(path: Path) -> list[tuple[float, float]]:
    """Parse (r, u_theta) rows from the evidence profile CSV."""
    if not path.is_file():
        raise SystemExit(f"evidence profile missing: {path}")
    points: list[tuple[float, float]] = []
    with path.open(newline="", encoding="utf-8") as fh:
        reader = csv.DictReader(fh)
        fields = set(reader.fieldnames or [])
        if "r" not in fields or "u_theta" not in fields:
            raise SystemExit(
                "profile header must contain columns 'r' and 'u_theta', "
                f"got {reader.fieldnames}"
            )
        for lineno, row in enumerate(reader, start=2):
            try:
                r = float(row["r"])
                u = float(row["u_theta"])
            except (TypeError, ValueError) as e:
                raise SystemExit(
                    f"profile line {lineno}: non-numeric r/u_theta cell: {e}"
                )
            if not (math.isfinite(r) and math.isfinite(u)):
                raise SystemExit(f"profile line {lineno}: non-finite value")
            if r < R_I - 1e-9 or r > R_O + 1e-9:
                raise SystemExit(
                    f"profile line {lineno}: r={r} outside [R_i={R_I}, R_o={R_O}]"
                )
            points.append((r, u))
    if len(points) < MIN_POINTS:
        raise SystemExit(f"profile has {len(points)} points, need >= {MIN_POINTS}")
    points.sort()
    return points


def main() -> None:
    submission = Path(sys.argv[1]) if len(sys.argv) > 1 else Path.cwd()
    points = load_profile(submission / PROFILE_REL)
    best_r, u_theta = min(points, key=lambda p: abs(p[0] - R_MIDGAP))
    dist = abs(best_r - R_MIDGAP)
    if dist > STATION_TOL:
        raise SystemExit(
            f"no sample point at the mid-gap station r = {R_MIDGAP} m "
            f"(nearest is {dist:g} m off)"
        )
    print(json.dumps({"utheta_midgap": u_theta}))


if __name__ == "__main__":
    main()
