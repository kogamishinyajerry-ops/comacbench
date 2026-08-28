#!/usr/bin/env python3
"""Compute QoI cf_bulk for turbulent_channel_from_brief (evidence mode).

Reads the submission's wall-shear sample file:

    <submission>/evidence/samples/wall_shear.csv

Documented format (visible/task.md): one header row
``surface,tau_w_x_pa`` followed by one row per wall-shear sample.
``surface`` is ``lower`` or ``upper`` (the two channel walls);
``tau_w_x_pa`` is the streamwise wall-shear-stress component in pascals
at that sample location. Fully developed channel flow is statistically
homogeneous in x and z, so the plain mean over all samples of both walls
is the area-averaged wall shear stress.

QoI (task-brief convention): Cf = mean(|tau_w,x|) / (0.5 * rho * U_b^2)
with the brief's reference density rho = 1 kg/m^3 and imposed bulk
velocity U_b = 1 m/s, i.e. Cf = 2 * mean(|tau_w,x|).

cfdb qoi_script protocol: ``python3 reference/compute_qoi.py <submission
dir>``; the last non-empty stdout line is a JSON object. Pure Python
standard library; exits non-zero when the evidence file is missing or
malformed (never fabricates a value).
"""

from __future__ import annotations

import csv
import json
import math
import sys
from pathlib import Path

WALL_SHEAR_CSV = Path("evidence") / "samples" / "wall_shear.csv"
SURFACES = ("lower", "upper")
RHO_REF = 1.0  # kg/m^3, brief's reference density (incompressible)
U_BULK = 1.0  # m/s, imposed bulk velocity


def fail(message: str) -> "SystemExit":
    return SystemExit(f"compute_qoi: {message}")


def main() -> None:
    submission_dir = Path(sys.argv[1]) if len(sys.argv) > 1 else Path.cwd()
    path = submission_dir / WALL_SHEAR_CSV
    if not path.is_file():
        raise fail(f"required evidence file missing: {WALL_SHEAR_CSV}")

    rows = list(csv.reader(path.read_text(encoding="utf-8").splitlines()))
    rows = [row for row in rows if len(row) > 0]
    if len(rows) < 2:
        raise fail(f"{WALL_SHEAR_CSV} has no data rows")
    header = [cell.strip() for cell in rows[0]]
    if header != ["surface", "tau_w_x_pa"]:
        raise fail(
            f"{WALL_SHEAR_CSV} header must be exactly 'surface,tau_w_x_pa', "
            f"got {rows[0]!r}"
        )

    per_surface: dict[str, list[float]] = {name: [] for name in SURFACES}
    for lineno, row in enumerate(rows[1:], start=2):
        if len(row) != 2:
            raise fail(f"{WALL_SHEAR_CSV} line {lineno}: expected 2 columns, got {len(row)}")
        surface = row[0].strip()
        if surface not in per_surface:
            raise fail(
                f"{WALL_SHEAR_CSV} line {lineno}: surface must be one of "
                f"{SURFACES}, got {surface!r}"
            )
        try:
            tau = float(row[1].strip())
        except ValueError:
            raise fail(f"{WALL_SHEAR_CSV} line {lineno}: tau_w_x_pa not numeric: {row[1]!r}")
        if not math.isfinite(tau):
            raise fail(f"{WALL_SHEAR_CSV} line {lineno}: tau_w_x_pa not finite: {row[1]!r}")
        per_surface[surface].append(abs(tau))

    missing = [name for name, values in per_surface.items() if len(values) == 0]
    if missing:
        raise fail(f"{WALL_SHEAR_CSV} has no samples for wall(s): {missing}")

    all_samples = [v for values in per_surface.values() for v in values]
    tau_w_mean = sum(all_samples) / len(all_samples)
    cf_bulk = tau_w_mean / (0.5 * RHO_REF * U_BULK**2)
    print(json.dumps({"cf_bulk": cf_bulk}))


if __name__ == "__main__":
    main()
