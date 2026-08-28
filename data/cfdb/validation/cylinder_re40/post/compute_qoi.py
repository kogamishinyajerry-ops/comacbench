#!/usr/bin/env python3
"""Compute QoIs drag_coeff_cd and wake_length_lw_over_d for the
cylinder_re40 case.

Inputs (both produced by the shipped case config):

  postProcessing/forceCoeffs1/<time>/coefficient.dat
      forceCoeffs time series (system/controlDict; Aref = D x 1 m depth,
      lRef = D = 1, rhoInf = 1). drag_coeff_cd = Cd of the LAST data line
      (steady SIMPLE — the run is converged by endTime, see case.yaml).

  postProcessing/sampleDict/<time>/wakeLine_U.csv
      wake-centerline sample (system/sampleDict, run by the sample_wake
      step: postProcess -func sampleDict -latestTime). The recirculation
      bubble sits on y = 0 behind the cylinder (rear stagnation point at
      x = D/2 = 0.5) with Ux < 0; wake_length_lw_over_d = (x_r - D/2)/D
      where x_r is the negative-to-positive Ux zero crossing, linearly
      interpolated between the bracketing sample points.

cfdb qoi_script protocol: ``python3 post/compute_qoi.py <run_case_dir>``;
the last non-empty stdout line is a JSON object. Pure Python standard
library; exits non-zero when an input is missing, malformed, or shows no
recirculation bubble (never fabricates a value).
"""

from __future__ import annotations

import csv
import json
import sys
from pathlib import Path

DIAMETER = 1.0
REAR_STAGNATION_X = 0.5  # D/2, cylinder centred at the origin
LINE_START_X = 0.51  # sampleDict wakeLine start (axis-distance origin)


def latest_time_dir(root: Path, dat_glob: str) -> Path:
    """Return the latest time dir under root containing a dat_glob file."""
    if not root.is_dir():
        raise SystemExit(f"no directory: {root} (did the solver run?)")
    candidates = []
    for time_dir in root.iterdir():
        if time_dir.is_dir() and any(time_dir.glob(dat_glob)):
            try:
                candidates.append((float(time_dir.name), time_dir))
            except ValueError:
                candidates.append((0.0, time_dir))
    if not candidates:
        raise SystemExit(f"no {dat_glob} found under {root}")
    return max(candidates)[1]


def last_cd(coeff_dat: Path) -> float:
    """Return Cd from the last data line, located via the header columns."""
    header_cols: list[str] | None = None
    last_data: list[str] | None = None
    for line in coeff_dat.read_text(encoding="utf-8").splitlines():
        stripped = line.strip()
        if not stripped:
            continue
        if stripped.startswith("#"):
            tokens = stripped.lstrip("#").split()
            lowered = [t.lower() for t in tokens]
            if "cd" in lowered:
                header_cols = tokens
            continue
        last_data = stripped.split()
    if header_cols is None or last_data is None:
        raise SystemExit(f"no header/data parsed from {coeff_dat}")
    i_cd = [t.lower() for t in header_cols].index("cd")
    if len(last_data) <= i_cd:
        raise SystemExit(f"last data line of {coeff_dat} has no Cd column")
    return float(last_data[i_cd])


def wake_length_over_d(sample_csv: Path) -> float:
    """Locate the Ux sign change (negative -> positive) on the wake line.

    Tolerates both v2312 csv header schemas: ``distance,U_0,U_1,U_2``
    (axis distance — the shipped sampleDict) and ``x,y,z,U_x,U_y,U_z``.
    """
    xs: list[float] = []
    uxs: list[float] = []
    with sample_csv.open(newline="", encoding="utf-8") as fh:
        for row in csv.DictReader(fh):
            if "distance" in row:
                xs.append(LINE_START_X + float(row["distance"]))
                uxs.append(float(row["U_0"]))
            else:
                xs.append(float(row["x"]))
                uxs.append(float(row["U_x"]))
    if len(xs) < 2:
        raise SystemExit(f"sample file {sample_csv} has fewer than 2 points")
    for i in range(len(xs) - 1):
        if uxs[i] < 0.0 <= uxs[i + 1]:
            frac = -uxs[i] / (uxs[i + 1] - uxs[i])
            x_r = xs[i] + frac * (xs[i + 1] - xs[i])
            return (x_r - REAR_STAGNATION_X) / DIAMETER
    raise SystemExit(
        "no negative->positive Ux sign change found on the wake centerline: "
        "either the recirculation bubble is absent (unconverged / wrong "
        "physics) or it extends past the sampled line. Refusing to "
        "fabricate a QoI value."
    )


def main() -> None:
    case_dir = Path(sys.argv[1]) if len(sys.argv) > 1 else Path.cwd()

    fc_dir = latest_time_dir(case_dir / "postProcessing" / "forceCoeffs1", "coefficient.dat")
    cd = last_cd(next(fc_dir.glob("coefficient.dat")))

    sample_root = case_dir / "postProcessing" / "sampleDict"
    sample_dir = latest_time_dir(sample_root, "wakeLine_U.csv")
    lw = wake_length_over_d(next(sample_dir.glob("wakeLine_U.csv")))

    print(json.dumps({"drag_coeff_cd": cd, "wake_length_lw_over_d": lw}))


if __name__ == "__main__":
    main()
