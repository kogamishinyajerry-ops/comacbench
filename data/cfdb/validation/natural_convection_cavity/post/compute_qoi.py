#!/usr/bin/env python3
"""Compute QoI hot_wall_nu_avg for the natural_convection_cavity case.

Reads the FINAL time directory's wallHeatFlux field (written by the
wallHeatFluxHot functionObject, writeControl writeTime):

    <latest_time>/wallHeatFlux     boundaryField hotWall value
                                   nonuniform List<scalar>

The QoI (case.yaml convention): Nu_avg = |q''|_avg * H / (k * dT) with
H = 1 m, k = mu*Cp/Pr = 6.437 W/(m K), dT = 10 K, i.e.
Nu_avg = |q''|_avg / 64.37. The patch average is the plain mean over the
hotWall patch values: the 64x64 mesh uses simpleGrading (1 1 1), so every
hotWall face has the same area and the plain mean IS the area average.

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

PATCH = "hotWall"
# k * dT / H = (mu*Cp/Pr) * 10 / 1 = 6.437 * 10 (see case.yaml).
K_DT_OVER_H = 64.37


def latest_time_dir(case_dir: Path) -> Path:
    times = []
    for child in case_dir.iterdir():
        if child.is_dir():
            try:
                times.append((float(child.name), child))
            except ValueError:
                continue
    if not times:
        raise SystemExit(f"no time directories found in {case_dir} — run buoyantSimpleFoam first")
    return max(times)[1]


def parse_patch_scalars(field_path: Path, patch: str) -> list[float]:
    """Parse the patch's nonuniform List<scalar> value from a field file."""
    text = field_path.read_text(encoding="utf-8")
    m = re.search(
        patch + r"\s*\{[^{}]*?value\s+nonuniform\s+List<scalar>\s+(\d+)\s*\(",
        text,
        re.DOTALL,
    )
    if not m:
        raise SystemExit(f"cannot find scalar value list for patch '{patch}' in {field_path}")
    n = int(m.group(1))
    start = text.index("(", m.end() - 1)
    end = text.index("\n)", start)
    values = [float(v) for v in text[start + 1 : end].split()]
    if len(values) != n:
        raise SystemExit(f"{field_path}: patch '{patch}' expected {n} scalars, parsed {len(values)}")
    return values


def main() -> None:
    case_dir = Path(sys.argv[1]) if len(sys.argv) > 1 else Path.cwd()
    field = latest_time_dir(case_dir) / "wallHeatFlux"
    flux = parse_patch_scalars(field, PATCH)
    q_avg = sum(abs(v) for v in flux) / len(flux)
    print(json.dumps({"hot_wall_nu_avg": q_avg / K_DT_OVER_H}))


if __name__ == "__main__":
    main()
