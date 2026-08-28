#!/usr/bin/env python3
"""Compute QoIs shock_x_t02 and rho_plateau_t02 for the sod_shock_tube case.

Reads the FINAL time directory (t = 0.2 s, the Sod evaluation time) written
by rhoCentralFoam:

    <latest_time>/rho     internalField nonuniform List<scalar> (1000 cells)
    (fallback: rho = p/(R*T) from the p and T fields, R = 287.10187 —
    RR/28.96, see constant/thermophysicalProperties)

The mesh is a uniform 1000-cell strip over x in [0, 1] m, so cell i centre
sits at x_i = (i + 0.5)/1000.

  shock_x_t02     = argmax |d rho/dx|, located at the midpoint of the
                    cell pair with the largest density jump (the
                    conventional shock-position convention; the case's
                    provenance notes froze this convention with the
                    2026-08-11 measurement shock_x_t02 = 0.850).
  rho_plateau_t02 = rho of the cell nearest the star-region probe x = 0.6.

cfdb qoi_script protocol: ``python3 post/compute_qoi.py <run_case_dir>``;
the last non-empty stdout line is a JSON object. Pure Python standard
library; exits non-zero when the fields are missing or malformed (never
fabricates a value).
"""

from __future__ import annotations

import json
import re
import sys
from pathlib import Path

N_CELLS = 1000
LENGTH = 1.0
R_GAS = 287.10187  # RR/28.96 [J/(kg K)], see case.yaml
PROBE_X = 0.6


def latest_time_dir(case_dir: Path) -> Path:
    times = []
    for child in case_dir.iterdir():
        if child.is_dir():
            try:
                times.append((float(child.name), child))
            except ValueError:
                continue
    if not times:
        raise SystemExit(f"no time directories found in {case_dir} — run rhoCentralFoam first")
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
    time_dir = latest_time_dir(case_dir)

    rho_path = time_dir / "rho"
    if rho_path.is_file():
        rho = parse_scalar_field(rho_path)
    else:
        # rhoCentralFoam versions that do not write rho: rebuild it from
        # the perfect-gas relation (case gas, R = RR/28.96).
        p = parse_scalar_field(time_dir / "p")
        temperature = parse_scalar_field(time_dir / "T")
        if len(p) != len(temperature):
            raise SystemExit("p and T internalFields have different lengths")
        rho = [pi / (R_GAS * ti) for pi, ti in zip(p, temperature)]
    if len(rho) != N_CELLS:
        raise SystemExit(f"expected {N_CELLS} cells, parsed {len(rho)}")

    dx = LENGTH / N_CELLS
    # Shock position: cell pair with the largest density jump.
    i_shock = max(range(N_CELLS - 1), key=lambda i: abs(rho[i + 1] - rho[i]))
    shock_x = (i_shock + 1) * dx  # midpoint of the bracketing centres

    i_probe = min(range(N_CELLS), key=lambda i: abs((i + 0.5) * dx - PROBE_X))
    print(json.dumps({"shock_x_t02": shock_x, "rho_plateau_t02": rho[i_probe]}))


if __name__ == "__main__":
    main()
