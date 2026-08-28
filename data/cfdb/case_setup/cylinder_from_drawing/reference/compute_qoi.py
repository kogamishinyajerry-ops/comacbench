#!/usr/bin/env python3
"""Frozen QoI script for the case_setup task cylinder_from_drawing.

Computes drag_coeff_cd from the submission's solver output:

  postProcessing/forceCoeffs1/<time>/coefficient.dat
      forceCoeffs time series (the task requires a forceCoeffs function
      object named forceCoeffs1 on the cylinder wall patches, with
      Aref = D x unit depth). drag_coeff_cd = Cd of the LAST data line
      (steady SIMPLE — the run is converged by endTime).

Adapted from cases/validation/cylinder_re40/post/compute_qoi.py with the
wake-length QoI dropped: the case_setup execution protocol runs blockMesh
and the controlDict solver only (no postProcess sampleDict step), so the
wake-centerline sample the wake_length QoI needs is never produced.

cfdb qoi_script protocol: ``python3 compute_qoi.py <run_case_dir>``; the
last non-empty stdout line is a JSON object. Pure Python standard library;
exits non-zero when an input is missing or malformed (never fabricates a
value).
"""

from __future__ import annotations

import json
import sys
from pathlib import Path


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


def main() -> None:
    case_dir = Path(sys.argv[1]) if len(sys.argv) > 1 else Path.cwd()

    fc_dir = latest_time_dir(case_dir / "postProcessing" / "forceCoeffs1", "coefficient.dat")
    cd = last_cd(next(fc_dir.glob("coefficient.dat")))

    print(json.dumps({"drag_coeff_cd": cd}))


if __name__ == "__main__":
    main()
