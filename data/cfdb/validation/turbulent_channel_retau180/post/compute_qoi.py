#!/usr/bin/env python3
"""Compute QoI cf_bulk for the turbulent_channel_retau180 case.

Reads the FINAL time directory's wallShearStress field (written by the
wallShearStress1 functionObject, writeControl writeTime):

    <latest_time>/wallShearStress     boundaryField bottom/top values
                                      nonuniform List<vector>

The QoI (case.yaml convention): Cf = mean(|tau_w,x|) / (0.5 * rho * U_b^2)
with rho = 1 (incompressible per-unit-density) and U_b = 1 m/s, i.e.
Cf = 2 * mean(|tau_w,x|), where the mean runs over the bottom AND top
wall patch faces (statistically symmetric). The plain mean over patch
faces equals the area average: the blockMesh is uniform in x and z
(simpleGrading 1 in both wall-parallel directions), so every wall face
has the same area.

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

PATCHES = ("bottom", "top")


def latest_time_dir(case_dir: Path) -> Path:
    times = []
    for child in case_dir.iterdir():
        if child.is_dir():
            try:
                times.append((float(child.name), child))
            except ValueError:
                continue
    if not times:
        raise SystemExit(f"no time directories found in {case_dir} — run simpleFoam first")
    return max(times)[1]


def parse_patch_vectors(field_path: Path, patch: str) -> list[tuple[float, float, float]]:
    """Parse the patch's nonuniform List<vector> value from a field file."""
    text = field_path.read_text(encoding="utf-8")
    m = re.search(
        patch + r"\s*\{[^{}]*?value\s+nonuniform\s+List<vector>\s+(\d+)\s*\(",
        text,
        re.DOTALL,
    )
    if not m:
        raise SystemExit(f"cannot find vector value list for patch '{patch}' in {field_path}")
    n = int(m.group(1))
    start = text.index("(", m.end() - 1)
    end = text.index("\n)", start)
    values = []
    for line in text[start + 1 : end].splitlines():
        line = line.strip().strip("()")
        if line:
            values.append(tuple(float(v) for v in line.split()))
    if len(values) != n:
        raise SystemExit(f"{field_path}: patch '{patch}' expected {n} vectors, parsed {len(values)}")
    return values


def main() -> None:
    case_dir = Path(sys.argv[1]) if len(sys.argv) > 1 else Path.cwd()
    field = latest_time_dir(case_dir) / "wallShearStress"
    tau_x: list[float] = []
    for patch in PATCHES:
        tau_x.extend(abs(v[0]) for v in parse_patch_vectors(field, patch))
    cf_bulk = 2.0 * sum(tau_x) / len(tau_x)  # 0.5 * rho * U_b^2 = 0.5
    print(json.dumps({"cf_bulk": cf_bulk}))


if __name__ == "__main__":
    main()
