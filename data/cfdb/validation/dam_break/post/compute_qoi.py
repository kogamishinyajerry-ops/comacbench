#!/usr/bin/env python3
"""Compute QoIs front_z_tau_* for the dam_break case.

Reads the alpha.water volScalarField at the write times nearest the
dimensionless targets tau = t*sqrt(2*g/a) in {1.0, 1.5, 2.0, 2.5, 2.8}
(a = 0.146 m column base, g = 9.81 m/s^2 — see case.yaml):

    <time>/alpha.water     internalField nonuniform List<scalar> (96x96x1)

The tank is a single uniform hex block (constant/polyMesh/blockMeshDict):
L = 4a = 0.584 m, 96 x 96 cells, x-fastest cell ordering, so cell (i, j)
centre sits at x = (i + 0.5)*L/96. Surge front (case.yaml convention):

    Z = max{x_cell : alpha.water >= 0.5},   QoI = Z / a

cfdb qoi_script protocol: ``python3 post/compute_qoi.py <run_case_dir>``;
the last non-empty stdout line is a JSON object. Pure Python standard
library; exits non-zero when a needed field is missing or malformed
(never fabricates a value).
"""

from __future__ import annotations

import json
import math
import re
import sys
from pathlib import Path

A = 0.146  # column base width [m]
G = 9.81  # [m/s^2]
L = 4.0 * A  # tank width [m]
NX = 96
N_CELLS = NX * NX
TAUS = {"front_z_tau_1_0": 1.0, "front_z_tau_1_5": 1.5,
        "front_z_tau_2_0": 2.0, "front_z_tau_2_5": 2.5, "front_z_tau_2_8": 2.8}


def time_dirs(case_dir: Path) -> dict[float, Path]:
    times = {}
    for child in case_dir.iterdir():
        if child.is_dir():
            try:
                times[float(child.name)] = child
            except ValueError:
                continue
    if not times:
        raise SystemExit(f"no time directories found in {case_dir} — run interFoam first")
    return times


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


def front_over_a(alpha: list[float]) -> float:
    """Z/a = max cell-centre x with alpha >= 0.5, normalised by a."""
    dx = L / NX
    front_x = 0.0
    found = False
    for idx, value in enumerate(alpha):
        if value >= 0.5:
            i = idx % NX  # x-fastest ordering of the single hex block
            front_x = max(front_x, (i + 0.5) * dx)
            found = True
    if not found:
        raise SystemExit("no cell with alpha.water >= 0.5 — field is empty of water")
    return front_x / A


def main() -> None:
    case_dir = Path(sys.argv[1]) if len(sys.argv) > 1 else Path.cwd()
    times = time_dirs(case_dir)
    tau_rate = math.sqrt(2.0 * G / A)  # tau = t * tau_rate (~11.596)

    qoi: dict[str, float] = {}
    for name, tau in sorted(TAUS.items()):
        t_target = tau / tau_rate
        t_near = min(times, key=lambda t: abs(t - t_target))
        alpha_path = times[t_near] / "alpha.water"
        if not alpha_path.is_file():
            raise SystemExit(f"{alpha_path} missing for tau target {tau}")
        alpha = parse_scalar_field(alpha_path)
        if len(alpha) != N_CELLS:
            raise SystemExit(f"expected {N_CELLS} cells, parsed {len(alpha)} at t={t_near}")
        qoi[name] = front_over_a(alpha)
    print(json.dumps(qoi))


if __name__ == "__main__":
    main()
