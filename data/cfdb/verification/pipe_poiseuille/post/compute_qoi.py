#!/usr/bin/env python3
"""Compute QoIs u_max and wall_u_avg for the pipe_poiseuille case.

Reads the two functionObject time series (see system/controlDict):

    postProcessing/uMax/<time>/volFieldValue.dat      (operation max on U)
    postProcessing/wallU/<time>/surfaceFieldValue.dat (areaAverage on patch wall)

v2312 fieldValue .dat format: ``#`` comment header lines, then one data
line per write: ``t (vx vy vz)`` for vector fields. The LAST data line of
each series is the developed state.

  u_max      = x-component of the max vector (flow is axial, Ux > 0
               everywhere at developed state; reference 2*U_mean = 0.2)
  wall_u_avg = magnitude of the area-averaged wall velocity (exactly 0
               for a correct noSlip wall; reference 0, absolute gate)

cfdb qoi_script protocol: ``python3 post/compute_qoi.py <run_case_dir>``;
the last non-empty stdout line is a JSON object. Pure Python standard
library; exits non-zero when a series is missing or malformed (never
fabricates a value).
"""

from __future__ import annotations

import json
import math
import re
import sys
from pathlib import Path

VECTOR = re.compile(
    r"\(\s*([0-9.eE+\-]+)\s+([0-9.eE+\-]+)\s+([0-9.eE+\-]+)\s*\)"
)


def find_dat(case_dir: Path, fo_name: str, dat_name: str) -> Path:
    """Return the latest <dat_name> written by functionObject <fo_name>."""
    root = case_dir / "postProcessing" / fo_name
    if not root.is_dir():
        raise SystemExit(f"no {fo_name} directory: {root} (did the solver run?)")
    candidates: list[tuple[float, Path]] = []
    for time_dir in root.iterdir():
        f = time_dir / dat_name
        if f.is_file():
            try:
                t = float(time_dir.name)
            except ValueError:
                t = 0.0
            candidates.append((t, f))
    if not candidates:
        raise SystemExit(f"no {dat_name} found under {root}")
    return max(candidates)[1]


def last_vector(dat_file: Path) -> tuple[float, float, float]:
    """Return the vector on the last data line of a fieldValue .dat file."""
    last_data = ""
    for line in dat_file.read_text(encoding="utf-8").splitlines():
        stripped = line.strip()
        if stripped and not stripped.startswith("#"):
            last_data = stripped
    if not last_data:
        raise SystemExit(f"no data lines in {dat_file}")
    m = VECTOR.search(last_data)
    if not m:
        raise SystemExit(f"no vector parsed from last line of {dat_file}")
    return float(m.group(1)), float(m.group(2)), float(m.group(3))


def main() -> None:
    case_dir = Path(sys.argv[1]) if len(sys.argv) > 1 else Path.cwd()
    ux_max, _, _ = last_vector(find_dat(case_dir, "uMax", "volFieldValue.dat"))
    wx, wy, wz = last_vector(find_dat(case_dir, "wallU", "surfaceFieldValue.dat"))
    print(
        json.dumps(
            {
                "u_max": ux_max,
                "wall_u_avg": math.sqrt(wx * wx + wy * wy + wz * wz),
            }
        )
    )


if __name__ == "__main__":
    main()
