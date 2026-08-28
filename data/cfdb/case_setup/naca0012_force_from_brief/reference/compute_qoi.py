#!/usr/bin/env python3
"""Compute QoIs cl/cd for naca0012_force_from_brief (evidence mode).

Reads the submission's force-coefficient convergence history:

    <submission>/evidence/force_history.csv

Documented format (visible/task.md): one header row ``iter,cl,cd``
followed by one row per recorded solver iteration of the STEADY solve.
``iter`` is the iteration counter (numeric, monotonically
non-decreasing); ``cl`` and ``cd`` are the sectional lift and drag
coefficients of the airfoil at that iteration (reference area = chord x
span per the brief).

Reduction: the QoIs are the means over the converged tail of the
history — the last 20% of the rows, at least 5 rows (fewer than 10 data
rows total is refused outright: a handful of points is not a converged
steady history).

cfdb qoi_script protocol: ``python3 reference/compute_qoi.py <submission
dir>``; the last non-empty stdout line is a JSON object. Pure Python
standard library; exits non-zero when the evidence file is missing or
malformed (never fabricates a value).
"""

from __future__ import annotations

import csv
import json
import math
import sys
from pathlib import Path

FORCE_HISTORY_CSV = Path("evidence") / "force_history.csv"
MIN_ROWS = 10
TAIL_FRACTION = 0.2
TAIL_MIN = 5


def fail(message: str) -> "SystemExit":
    return SystemExit(f"compute_qoi: {message}")


def main() -> None:
    submission_dir = Path(sys.argv[1]) if len(sys.argv) > 1 else Path.cwd()
    path = submission_dir / FORCE_HISTORY_CSV
    if not path.is_file():
        raise fail(f"required evidence file missing: {FORCE_HISTORY_CSV}")

    rows = list(csv.reader(path.read_text(encoding="utf-8").splitlines()))
    rows = [row for row in rows if len(row) > 0]
    if len(rows) < 2:
        raise fail(f"{FORCE_HISTORY_CSV} has no data rows")
    if [cell.strip() for cell in rows[0]] != ["iter", "cl", "cd"]:
        raise fail(
            f"{FORCE_HISTORY_CSV} header must be exactly 'iter,cl,cd', got {rows[0]!r}"
        )

    iters: list[float] = []
    cls: list[float] = []
    cds: list[float] = []
    for lineno, row in enumerate(rows[1:], start=2):
        if len(row) != 3:
            raise fail(f"{FORCE_HISTORY_CSV} line {lineno}: expected 3 columns, got {len(row)}")
        try:
            it, cl, cd = (float(cell.strip()) for cell in row)
        except ValueError:
            raise fail(f"{FORCE_HISTORY_CSV} line {lineno}: non-numeric cell in {row!r}")
        for name, value in (("iter", it), ("cl", cl), ("cd", cd)):
            if not math.isfinite(value):
                raise fail(f"{FORCE_HISTORY_CSV} line {lineno}: {name} not finite")
        if iters and it < iters[-1]:
            raise fail(f"{FORCE_HISTORY_CSV} line {lineno}: iter decreases ({iters[-1]:g} -> {it:g})")
        iters.append(it)
        cls.append(cl)
        cds.append(cd)

    n = len(iters)
    if n < MIN_ROWS:
        raise fail(f"{FORCE_HISTORY_CSV} has only {n} data rows (need >= {MIN_ROWS})")
    n_tail = max(TAIL_MIN, int(n * TAIL_FRACTION))
    cl = sum(cls[-n_tail:]) / n_tail
    cd = sum(cds[-n_tail:]) / n_tail
    print(json.dumps({"cl": cl, "cd": cd}))


if __name__ == "__main__":
    main()
