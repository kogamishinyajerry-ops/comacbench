#!/usr/bin/env python3
"""Compute QoI post_shock_mach for the oblique_shock case.

Reads the postShockProbe functionObject output (see system/controlDict):

    postProcessing/postShockProbe/<time>/{U,p,T}

Probe data lines are ``t (ux uy uz)`` for U and ``t value`` for the
scalars; the LAST data line is the steady long-time state. The QoI is

    post_shock_mach = |U| / sqrt(gamma * R * T)

with the case-normalised gas (constant/thermophysicalProperties):
Cp = 2.5, R = RR/molWeight = 8314.4621/11640.3 ~ 0.7143, so
gamma = Cp/(Cp - R) = 1.4 exactly and gamma*R*T1 ~ 1 (a1 ~ 1).

cfdb qoi_script protocol: ``python3 post/compute_qoi.py <run_case_dir>``;
the last non-empty stdout line is a JSON object. Pure Python standard
library; exits non-zero when the probe data is missing or malformed
(never fabricates a value).
"""

from __future__ import annotations

import json
import math
import re
import sys
from pathlib import Path

RR = 8314.4621  # universal gas constant, OpenFOAM value [J/(kmol K)]
MOL_WEIGHT = 11640.3  # constant/thermophysicalProperties
CP = 2.5

R_GAS = RR / MOL_WEIGHT
GAMMA = CP / (CP - R_GAS)

VECTOR = re.compile(
    r"\(\s*([0-9.eE+\-]+)\s+([0-9.eE+\-]+)\s+([0-9.eE+\-]+)\s*\)"
)


def probe_dir(case_dir: Path) -> Path:
    """Return the latest postShockProbe time directory."""
    root = case_dir / "postProcessing" / "postShockProbe"
    if not root.is_dir():
        raise SystemExit(f"no probe directory: {root} (did the solver run?)")
    candidates = []
    for time_dir in root.iterdir():
        if time_dir.is_dir():
            try:
                candidates.append((float(time_dir.name), time_dir))
            except ValueError:
                continue
    if not candidates:
        raise SystemExit(f"no time directories under {root}")
    return max(candidates)[1]


def last_data_line(path: Path) -> str:
    last = ""
    for line in path.read_text(encoding="utf-8").splitlines():
        stripped = line.strip()
        if stripped and not stripped.startswith("#"):
            last = stripped
    if not last:
        raise SystemExit(f"no data lines in {path}")
    return last


def main() -> None:
    case_dir = Path(sys.argv[1]) if len(sys.argv) > 1 else Path.cwd()
    pdir = probe_dir(case_dir)

    u_line = last_data_line(pdir / "U")
    m = VECTOR.search(u_line)
    if not m:
        raise SystemExit(f"no velocity vector parsed from {pdir / 'U'}")
    ux, uy, uz = (float(m.group(i)) for i in (1, 2, 3))
    speed = math.sqrt(ux * ux + uy * uy + uz * uz)

    t_val = float(last_data_line(pdir / "T").split()[-1])
    if t_val <= 0.0:
        raise SystemExit(f"non-positive probe temperature {t_val}")

    mach = speed / math.sqrt(GAMMA * R_GAS * t_val)
    print(json.dumps({"post_shock_mach": mach}))


if __name__ == "__main__":
    main()
