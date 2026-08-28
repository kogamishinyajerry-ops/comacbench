#!/usr/bin/env python3
"""Compute QoI centerline_umax for the lid_driven_cavity_re1000 case.

Reads the probes functionObject output (see system/controlDict):

    postProcessing/probes/<time>/U

Each data line is ``t (ux uy uz) (ux uy uz) ...`` — one parenthesised
vector per probe on the vertical centerline (x = 0.05 m, y/H up to 0.95).
The QoI is max |U|/U_lid over the 20 probes at the FINAL recorded time,
with U_lid = 1 m/s (Ghia et al. 1982 normalisation, see case.yaml).

cfdb qoi_script protocol: ``python3 post/compute_qoi.py <run_case_dir>``;
the last non-empty stdout line is a JSON object. Pure Python standard
library; exits non-zero when the probe data is missing or malformed
(never fabricates a value).
"""

from __future__ import annotations

import json
import math
import re
import sys
from pathlib import Path

U_LID = 1.0  # m/s

VECTOR = re.compile(
    r"\(\s*([0-9.eE+\-]+)\s+([0-9.eE+\-]+)\s+([0-9.eE+\-]+)\s*\)"
)


def find_probes_file(case_dir: Path) -> Path:
    """Return the U probes file from the latest time dir."""
    root = case_dir / "postProcessing" / "probes"
    if not root.is_dir():
        raise SystemExit(f"no probes directory: {root} (did the solver run?)")
    candidates: list[tuple[float, Path]] = []
    for time_dir in root.iterdir():
        f = time_dir / "U"
        if f.is_file():
            try:
                t = float(time_dir.name)
            except ValueError:
                t = 0.0
            candidates.append((t, f))
    if not candidates:
        raise SystemExit(f"no U probes file found under {root}")
    return max(candidates)[1]


def last_line_speeds(probes_file: Path) -> list[float]:
    """Return |U| of every probe at the final recorded time."""
    last_data = ""
    for line in probes_file.read_text(encoding="utf-8").splitlines():
        stripped = line.strip()
        # Skip comments: '# Probe 0 (x y z)' also carries a parenthesised
        # vector and must not be parsed as data.
        if stripped and not stripped.startswith("#"):
            last_data = stripped
    if not last_data:
        raise SystemExit(f"no data lines in {probes_file}")
    vectors = VECTOR.findall(last_data)
    if not vectors:
        raise SystemExit(f"no velocity vectors parsed from last line of {probes_file}")
    return [
        math.sqrt(float(ux) ** 2 + float(uy) ** 2 + float(uz) ** 2)
        for ux, uy, uz in vectors
    ]


def main() -> None:
    case_dir = Path(sys.argv[1]) if len(sys.argv) > 1 else Path.cwd()
    speeds = last_line_speeds(find_probes_file(case_dir))
    print(json.dumps({"centerline_umax": max(speeds) / U_LID}))


if __name__ == "__main__":
    main()
