#!/usr/bin/env python3
"""Compute QoIs shock_x_t02 and rho_plateau_t02 for the
sod_shock_from_brief case (case_setup, EVIDENCE mode).

Reads the submitted density profile at t = 0.2 s:

    <submission>/evidence/samples/density_profile.csv   header: x,rho
        x    sample coordinate along the tube [m], strictly increasing,
             covering [0, 1]
        rho  density at that point [kg/m^3]

Reductions (the same conventions the verified source case
cases/verification/sod_shock_tube froze with its 2026-08-11 measurement,
made mesh-agnostic — the source script used a uniform 1000-cell grid so
cell indices become sample pairs here):

  shock_x_t02     midpoint of the consecutive sample pair with the
                  largest density jump |rho[i+1] - rho[i]| (the
                  conventional max-gradient shock locator; on a uniform
                  cell-centred grid this is exactly the source case's
                  (i_shock + 1) * dx).
  rho_plateau_t02 rho of the sample nearest the star-region probe
                  x = 0.6.

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
PROBE_X = 0.6
MIN_POINTS = 200

PROFILE = Path("evidence") / "samples" / "density_profile.csv"


def load_profile(path: Path) -> list[tuple[float, float]]:
    try:
        text = path.read_text(encoding="utf-8")
    except (OSError, UnicodeDecodeError) as e:
        raise SystemExit(f"cannot read {path}: {e}")
    rows = [row for row in csv.reader(text.splitlines()) if len(row) > 0]
    if len(rows) < 2:
        raise SystemExit(f"{path}: needs a header row and at least one data row")
    header = [cell.strip() for cell in rows[0]]
    if header != ["x", "rho"]:
        raise SystemExit(f"{path}: header must be exactly 'x,rho', got {header!r}")
    samples: list[tuple[float, float]] = []
    for lineno, row in enumerate(rows[1:], start=2):
        if len(row) != 2:
            raise SystemExit(f"{path} line {lineno}: expected 2 columns, got {len(row)}")
        try:
            x = float(row[0])
            rho = float(row[1])
        except ValueError:
            raise SystemExit(f"{path} line {lineno}: non-numeric cell {row!r}")
        if not (math.isfinite(x) and math.isfinite(rho)):
            raise SystemExit(f"{path} line {lineno}: non-finite value {row!r}")
        samples.append((x, rho))
    return samples


def main() -> None:
    submission_dir = Path(sys.argv[1]) if len(sys.argv) > 1 else Path.cwd()
    samples = load_profile(submission_dir / PROFILE)
    if len(samples) < MIN_POINTS:
        raise SystemExit(f"profile has {len(samples)} points, need at least {MIN_POINTS}")
    for (x0, _), (x1, _) in zip(samples, samples[1:]):
        if x1 <= x0:
            raise SystemExit(f"profile x coordinates not strictly increasing at x={x0:g}")
    if samples[0][0] > 0.25 * LENGTH or samples[-1][0] < 0.75 * LENGTH:
        raise SystemExit(
            f"profile range [{samples[0][0]:g}, {samples[-1][0]:g}] does not cover "
            "the tube interior (need coverage of [0, 1])"
        )

    # Shock position: midpoint of the consecutive pair with the largest
    # density jump (max-gradient locator, same convention as the source
    # case's verified measurement).
    i_shock = max(
        range(len(samples) - 1), key=lambda i: abs(samples[i + 1][1] - samples[i][1])
    )
    shock_x = 0.5 * (samples[i_shock][0] + samples[i_shock + 1][0])

    rho_plateau = min(samples, key=lambda s: abs(s[0] - PROBE_X))[1]
    print(json.dumps({"shock_x_t02": shock_x, "rho_plateau_t02": rho_plateau}))


if __name__ == "__main__":
    main()
