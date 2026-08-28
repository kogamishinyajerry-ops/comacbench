#!/usr/bin/env python3
"""Compute QoIs ke_ratio_end and u_line_l2_rel_end for the
taylor_green_from_brief case (case_setup, EVIDENCE mode).

Reads the submitted evidence files:

    <submission>/evidence/samples/ke_history.csv   header: time,ke
        time  physical time [s]; first row must be t = 0, last row
              t = T_END = 5 s (both within TIME_TOL), monotonically
              non-decreasing (also enforced by the judge's generic CSV
              check)
        ke    domain-averaged kinetic energy 0.5*<|u|^2> [m^2/s^2]
    <submission>/evidence/samples/line_end.csv     header: x,u,v
        x,u,v velocity samples [m, m/s, m/s] along the horizontal line
              y = Y_LINE at t = T_END

Reductions (adapted from the verified source case
cases/verification/taylor_green_vortex/post/compute_qoi.py to read the
evidence bundle instead of OpenFOAM run products):

  ke_ratio_end      ke(T_END)/ke(0) — both endpoints come from the
                    submitted history, so the ratio is self-normalising
                    (the discrete mean of the analytic t=0 field on a
                    uniform grid equals U0^2/4 exactly, cf. the source
                    case's KE0 = 0.25).
  u_line_l2_rel_end relative L2 error of (u, v) along the sample line vs
                    the frozen analytic field at T_END:
                    u = U0 sin(kx) cos(k y0) e^{-2 nu k^2 t},
                    v = -U0 cos(kx) sin(k y0) e^{-2 nu k^2 t}
                    with U0 = 1, k = 1, nu = 0.01, y0 = 11*pi/64 (the
                    source case's controlDict sampleLine ordinate — mesh
                    row j = 5 centre on the 64x64 demo mesh).

cfdb qoi_script protocol: ``python3 reference/compute_qoi.py <submission
dir>``; the last non-empty stdout line is a JSON object. Pure Python
standard library; exits non-zero when the evidence is missing or
malformed (never fabricates a value).
"""

from __future__ import annotations

import csv
import json
import math
import sys
from pathlib import Path

U0 = 1.0
K = 1.0
NU = 0.01
T_END = 5.0
TIME_TOL = 0.01
Y_LINE = 5.5 * 2.0 * math.pi / 64.0  # 11*pi/64 = 0.5399612...
MIN_LINE_POINTS = 16

KE_HISTORY = Path("evidence") / "samples" / "ke_history.csv"
LINE_END = Path("evidence") / "samples" / "line_end.csv"


def load_csv(path: Path, expected_header: list[str]) -> list[list[str]]:
    try:
        text = path.read_text(encoding="utf-8")
    except (OSError, UnicodeDecodeError) as e:
        raise SystemExit(f"cannot read {path}: {e}")
    rows = [row for row in csv.reader(text.splitlines()) if len(row) > 0]
    if len(rows) < 2:
        raise SystemExit(f"{path}: needs a header row and at least one data row")
    header = [cell.strip() for cell in rows[0]]
    if header != expected_header:
        raise SystemExit(f"{path}: header must be exactly {expected_header}, got {header!r}")
    return rows[1:]


def parse_numeric_rows(path: Path, rows: list[list[str]], ncols: int) -> list[list[float]]:
    parsed: list[list[float]] = []
    for lineno, row in enumerate(rows, start=2):
        if len(row) != ncols:
            raise SystemExit(f"{path} line {lineno}: expected {ncols} columns, got {len(row)}")
        try:
            values = [float(cell) for cell in row]
        except ValueError:
            raise SystemExit(f"{path} line {lineno}: non-numeric cell {row!r}")
        if not all(math.isfinite(v) for v in values):
            raise SystemExit(f"{path} line {lineno}: non-finite value {row!r}")
        parsed.append(values)
    return parsed


def main() -> None:
    submission_dir = Path(sys.argv[1]) if len(sys.argv) > 1 else Path.cwd()

    # --- ke_ratio_end ---
    ke_rows = parse_numeric_rows(
        submission_dir / KE_HISTORY,
        load_csv(submission_dir / KE_HISTORY, ["time", "ke"]),
        2,
    )
    if len(ke_rows) < 2:
        raise SystemExit(f"{KE_HISTORY}: need at least 2 rows (t=0 and t={T_END:g})")
    t_first, ke_first = ke_rows[0]
    t_last, ke_last = ke_rows[-1]
    for (t0, _), (t1, _) in zip(ke_rows, ke_rows[1:]):
        if t1 < t0:
            raise SystemExit(f"{KE_HISTORY}: time not monotonically non-decreasing at t={t0:g}")
    if abs(t_first) > TIME_TOL:
        raise SystemExit(f"{KE_HISTORY}: first row must be t=0 (got {t_first:g})")
    if abs(t_last - T_END) > TIME_TOL:
        raise SystemExit(f"{KE_HISTORY}: last row must be t={T_END:g} (got {t_last:g})")
    if ke_first <= 0.0:
        raise SystemExit(f"{KE_HISTORY}: initial KE must be positive (got {ke_first:g})")
    ke_ratio_end = ke_last / ke_first

    # --- u_line_l2_rel_end ---
    line_rows = parse_numeric_rows(
        submission_dir / LINE_END,
        load_csv(submission_dir / LINE_END, ["x", "u", "v"]),
        3,
    )
    if len(line_rows) < MIN_LINE_POINTS:
        raise SystemExit(
            f"{LINE_END}: {len(line_rows)} sample points, need at least {MIN_LINE_POINTS}"
        )
    decay = math.exp(-2.0 * NU * K * K * T_END)
    err2 = 0.0
    ref2 = 0.0
    for x_num, u_num, v_num in line_rows:
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
