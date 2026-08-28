#!/usr/bin/env python3
"""Compute QoIs ke_ratio_end and u_line_l2_rel_end for the
taylor_green_vortex case.

Adapted from the case's compare.py to the cfdb qoi_script protocol
(``python3 post/compute_qoi.py <run_case_dir>``; last non-empty stdout
line is a JSON object; pure Python standard library). Unlike compare.py
this script is self-contained: the reference along the sample line is
evaluated from the frozen analytic solution (case.yaml documents it) —
u = U0 sin(kx) cos(ky) exp(-2 nu k^2 t), v = -U0 cos(kx) sin(ky)
exp(-2 nu k^2 t) with U0 = 1, k = 1, nu = 0.01 — instead of reading
reference/tgv_sample_line_t5.csv, which is not copied into the run dir.

  ke_ratio_end      KE(t_end)/KE(0), KE = domain mean of 0.5*|U|^2
                    (uniform cells -> plain mean; the discrete mean of
                    the analytic t=0 field on this grid equals U0^2/4
                    exactly, so KE0 = 0.25 is not an approximation).
  u_line_l2_rel_end relative L2 error of (u, v) along the sample line
                    (postProcessing/*/<t_end>/line_*, mesh row j = 5 at
                    y = 11*pi/32) vs the analytic field at t_end.

Exits non-zero when the run products are missing or malformed (never
fabricates a value).
"""

from __future__ import annotations

import json
import math
import re
import sys
from pathlib import Path

U0 = 1.0
K = 1.0
NU = 0.01
KE0 = 0.25 * U0 * U0  # exact (and grid-exact) initial mean kinetic energy
# Sample-line ordinate: mesh row j = 5 -> y = (5 + 0.5) * 2*pi/64 = 11*pi/64
# = 0.5399612..., matching the sampleLine start/end in system/controlDict
# (the "11*pi/32" in reference/generate.py's docstring is a typo; the
# controlDict coordinates are authoritative).
Y_LINE = 5.5 * 2.0 * math.pi / 64.0


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


def main() -> None:
    case_dir = Path(sys.argv[1]).resolve() if len(sys.argv) > 1 else Path.cwd()

    time_dir = latest_time_dir(case_dir)
    t_end = float(time_dir.name)
    field = parse_vector_field(time_dir / "U")
    ke = 0.5 * sum(u * u + v * v for u, v, _ in field) / len(field)
    ke_ratio_end = ke / KE0

    # Analytic reference at t_end along the sample line (frozen formula,
    # same as reference/generate.py uses for tgv_sample_line_t5.csv).
    decay = math.exp(-2.0 * NU * K * K * t_end)
    sample_path = find_sample_file(case_dir, time_dir.name)
    samples = []
    with sample_path.open(encoding="utf-8") as fh:
        for line in fh:
            parts = line.split()
            # setFormat raw with fields (U p) writes plain columns:
            # x p ux uy uz (file name sorts field names: line_p_U.xy).
            if len(parts) >= 5:
                samples.append((float(parts[0]), float(parts[2]), float(parts[3])))
    if not samples:
        raise SystemExit(f"no sample points parsed from {sample_path}")

    err2 = 0.0
    ref2 = 0.0
    for x_num, u_num, v_num in samples:
        u_ex = U0 * math.sin(K * x_num) * math.cos(K * Y_LINE) * decay
        v_ex = -U0 * math.cos(K * x_num) * math.sin(K * Y_LINE) * decay
        err2 += (u_num - u_ex) ** 2 + (v_num - v_ex) ** 2
        ref2 += u_ex**2 + v_ex**2
    if ref2 <= 0.0:
        raise SystemExit("analytic reference along the line is zero — cannot normalise")
    u_line_l2_rel_end = math.sqrt(err2 / ref2)

    print(json.dumps({"ke_ratio_end": ke_ratio_end, "u_line_l2_rel_end": u_line_l2_rel_end}))


if __name__ == "__main__":
    main()
