#!/usr/bin/env python3
"""Extract this case's QoIs from a finished OpenFOAM run and compare with
the analytic reference. Pure Python standard library.

Usage:
    python3 compare.py [case_dir]

`case_dir` defaults to the directory containing this script and must hold a
completed icoFoam run (time dirs + postProcessing/sampleLine). Prints a JSON
object with the two QoIs declared in case.yaml:

    ke_ratio_end       KE(t_end)/KE(0), KE = domain mean of 0.5*|U|^2
                       (uniform cells -> plain mean; the discrete mean of the
                       analytic t=0 field on this grid equals U0^2/4 exactly,
                       since the trapezoidal rule is exact for these periodic
                       modes, so dividing the computed KE by U0^2/4 is not an
                       approximation).
    u_line_l2_rel_end  relative L2 error of (u, v) along the t=5 sample line
                       vs reference/tgv_sample_line_t5.csv.

This script is a convenience extractor for manual verification; it is NOT
wired into the cfdb judging path (see card.yaml / provenance.yaml notes).
"""

import csv
import json
import math
import re
import sys
from pathlib import Path

CASE_DIR = Path(__file__).resolve().parent
U0 = 1.0
KE0 = 0.25 * U0 * U0  # exact (and grid-exact) initial mean kinetic energy


def latest_time_dir(case_dir: Path) -> Path:
    times = []
    for child in case_dir.iterdir():
        if child.is_dir():
            try:
                times.append((float(child.name), child))
            except ValueError:
                continue
    if not times:
        raise SystemExit(f"no time directories found in {case_dir} — run icoFoam first")
    return max(times)[1]


def parse_vector_field(path: Path) -> list[tuple[float, float, float]]:
    """Parse the internalField nonuniform List<vector> of an OpenFOAM U file."""
    text = path.read_text(encoding="utf-8")
    m = re.search(r"internalField\s+nonuniform\s+List<vector>\s+(\d+)\s*\(", text)
    if not m:
        raise SystemExit(f"cannot find nonuniform vector internalField in {path}")
    n = int(m.group(1))
    start = text.index("(", m.end() - 1)
    end = text.index("\n)", start)  # list-closing paren, not a vector's
    values = []
    for line in text[start + 1 : end].splitlines():
        line = line.strip().strip("()")
        if line:
            values.append(tuple(float(v) for v in line.split()))
    if len(values) != n:
        raise SystemExit(f"{path}: expected {n} vectors, parsed {len(values)}")
    return values


def find_sample_file(case_dir: Path, time_name: str) -> Path:
    candidates = sorted(case_dir.glob(f"postProcessing/*/{time_name}/line_*.*"))
    if not candidates:
        raise SystemExit(
            f"no sampleLine output under postProcessing/*/{time_name}/ — "
            "is the sampleLine functionObject enabled in system/controlDict?"
        )
    return candidates[0]


def load_reference_line() -> list[tuple[float, float, float, float]]:
    path = CASE_DIR / "reference" / "tgv_sample_line_t5.csv"
    with path.open(newline="", encoding="utf-8") as fh:
        rows = list(csv.DictReader(fh))
    return [
        (float(r["x"]), float(r["u_exact"]), float(r["v_exact"]), float(r["p_exact"]))
        for r in rows
    ]


def main() -> None:
    case_dir = Path(sys.argv[1]).resolve() if len(sys.argv) > 1 else CASE_DIR

    time_dir = latest_time_dir(case_dir)
    field = parse_vector_field(time_dir / "U")
    ke = 0.5 * sum(u * u + v * v for u, v, _ in field) / len(field)
    ke_ratio_end = ke / KE0

    sample_path = find_sample_file(case_dir, time_dir.name)
    reference = load_reference_line()
    # Sample file carries only writePrecision digits (10), the reference 17 —
    # match points by sorted order, not by exact float key.
    samples = []
    with sample_path.open(encoding="utf-8") as fh:
        for line in fh:
            parts = line.split()
            # setFormat raw with fields (U p) writes columns: x p ux uy uz
            # (OpenFOAM sorts field names alphabetically in the file name
            # and columns: line_p_U.xy).
            if len(parts) >= 5:
                samples.append((float(parts[0]), float(parts[2]), float(parts[3])))
    samples.sort()
    reference = sorted(load_reference_line())
    if len(samples) != len(reference):
        raise SystemExit(
            f"{sample_path}: {len(samples)} sample points, reference has {len(reference)}"
        )

    err2 = 0.0
    ref2 = 0.0
    for (x_num, u_num, v_num), (x_ref, u_ex, v_ex, _) in zip(samples, reference):
        if abs(x_num - x_ref) > 1e-6:
            raise SystemExit(f"sample abscissa mismatch: {x_num} vs {x_ref}")
        err2 += (u_num - u_ex) ** 2 + (v_num - v_ex) ** 2
        ref2 += u_ex**2 + v_ex**2
    u_line_l2_rel_end = math.sqrt(err2 / ref2)

    print(
        json.dumps(
            {
                "time": time_dir.name,
                "cells": len(field),
                "ke_ratio_end": ke_ratio_end,
                "u_line_l2_rel_end": u_line_l2_rel_end,
            },
            indent=2,
        )
    )


if __name__ == "__main__":
    main()
