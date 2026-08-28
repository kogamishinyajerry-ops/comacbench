#!/usr/bin/env python3
"""Compute QoI midplane_T for the heat_conduction_1d case.

Reads the FINAL time directory's T field written by laplacianFoam
(endTime 40 s = 4 diffusion time scales, see system/controlDict):

    <latest_time>/T     internalField nonuniform List<scalar> (100 cells)

The mesh is a uniform 100-cell strip over x in [0, 1] m, so cell i centre
sits at x_i = (i + 0.5)/100. midplane_T is the linear interpolation of
the two cells bracketing x = 0.5 (their centres are equidistant, so this
is the plain mean of cells 49 and 50). Analytical value 425.0 K.

cfdb qoi_script protocol: ``python3 post/compute_qoi.py <run_case_dir>``;
the last non-empty stdout line is a JSON object. Pure Python standard
library; exits non-zero when the field is missing or malformed (never
fabricates a value).
"""

from __future__ import annotations

import json
import re
import sys
from pathlib import Path

N_CELLS = 100


def latest_time_dir(case_dir: Path) -> Path:
    times = []
    for child in case_dir.iterdir():
        if child.is_dir():
            try:
                times.append((float(child.name), child))
            except ValueError:
                continue
    if not times:
        raise SystemExit(f"no time directories found in {case_dir} — run laplacianFoam first")
    return max(times)[1]


def parse_scalar_field(path: Path) -> list[float]:
    """Parse the internalField nonuniform List<scalar> of an OpenFOAM field."""
    text = path.read_text(encoding="utf-8")
    m = re.search(r"internalField\s+nonuniform\s+List<scalar>\s+(\d+)\s*\(", text)
    if not m:
        raise SystemExit(f"cannot find nonuniform scalar internalField in {path}")
    n = int(m.group(1))
    start = text.index("(", m.end() - 1)
    end = text.index("\n)", start)
    values = [float(v) for v in text[start + 1 : end].split()]
    if len(values) != n:
        raise SystemExit(f"{path}: expected {n} scalars, parsed {len(values)}")
    return values


def main() -> None:
    case_dir = Path(sys.argv[1]) if len(sys.argv) > 1 else Path.cwd()
    values = parse_scalar_field(latest_time_dir(case_dir) / "T")
    if len(values) != N_CELLS:
        raise SystemExit(f"expected {N_CELLS} cells, parsed {len(values)}")
    mid = len(values) // 2
    midplane_t = 0.5 * (values[mid - 1] + values[mid])
    print(json.dumps({"midplane_T": midplane_t}))


if __name__ == "__main__":
    main()
