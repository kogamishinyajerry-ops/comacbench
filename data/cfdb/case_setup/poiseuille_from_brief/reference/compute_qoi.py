#!/usr/bin/env python3
"""Compute QoI centerline_umax for the poiseuille_from_brief case.

Adapted verbatim (module docstring aside) from the verified
cases/verification/channel_poiseuille/post/compute_qoi.py; see
provenance.yaml for the lineage and the anchor hashes.

Reads the probes functionObject output (the submitted case must sample U
on a vertical line at x/H = 10, i.e. x = 0.1 m):

    postProcessing/probes/<time>/U

Each data line is ``t (ux uy uz) (ux uy uz) ...`` — one parenthesised
vector per probe on the probe line. The QoI is max |Ux| over the probes
at the FINAL recorded time (a correctly built case is fully developed and
steady by endTime — see visible/task.md).

cfdb qoi_script protocol: ``python3 reference/compute_qoi.py <case_dir>``;
the last non-empty stdout line is a JSON object. Pure Python standard
library; exits non-zero when the probe data is missing or malformed
(never fabricates a value).
"""

from __future__ import annotations

import json
import re
import sys
from pathlib import Path

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


def last_line_ux(probes_file: Path) -> list[float]:
    """Return the Ux of every probe at the final recorded time."""
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
    return [float(v[0]) for v in vectors]


def main() -> None:
    case_dir = Path(sys.argv[1]) if len(sys.argv) > 1 else Path.cwd()
    uxs = last_line_ux(find_probes_file(case_dir))
    centerline_umax = max(abs(u) for u in uxs)
    print(json.dumps({"centerline_umax": centerline_umax}))


if __name__ == "__main__":
    main()
