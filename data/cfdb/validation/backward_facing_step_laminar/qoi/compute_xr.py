#!/usr/bin/env python3
"""Compute the QoI reattachment_x_over_h for the backward_facing_step_laminar case.

Reads the latest near-bottom velocity sample written by the ``nearBottomU``
sets functionObject (see system/controlDict):

    postProcessing/nearBottomU/<time>/bottomLine_U.xy     (columns: x Ux Uy Uz)

The primary reattachment point x_r is where Ux along this near-wall line
changes sign from negative (recirculation bubble) to positive (reattached
flow), located by linear interpolation between the bracketing sample points.
The QoI is x_r / h with h = 0.01 m (step height).

Usage (from the OpenFOAM case directory after a run):

    python3 qoi/compute_xr.py [case_dir] [out_json]

Defaults: case_dir = current directory, out_json = <case_dir>/qoi.json.
Pure Python standard library; exits non-zero with a message when the sample
is missing or no recirculation is found (never fabricates a value).
"""

from __future__ import annotations

import json
import sys
from pathlib import Path

STEP_HEIGHT = 0.01  # h [m]


def find_sample(case_dir: Path) -> Path:
    """Return the latest bottomLine_U.xy sample file."""
    root = case_dir / "postProcessing" / "nearBottomU"
    if not root.is_dir():
        raise SystemExit(f"no sample directory: {root} (did the solver write time steps?)")
    candidates: list[tuple[float, Path]] = []
    for time_dir in root.iterdir():
        f = time_dir / "bottomLine_U.xy"
        if f.is_file():
            try:
                t = float(time_dir.name)
            except ValueError:
                t = 0.0
            candidates.append((t, f))
    if not candidates:
        raise SystemExit(f"no bottomLine_U.xy found under {root}")
    return max(candidates)[1]


def compute_xr(sample_file: Path) -> float:
    """Locate the Ux sign change (negative -> positive) and return x_r/h."""
    xs: list[float] = []
    uxs: list[float] = []
    for line in sample_file.read_text(encoding="utf-8").splitlines():
        line = line.strip()
        if not line or line.startswith("#"):
            continue
        parts = line.replace("(", " ").replace(")", " ").split()
        if len(parts) < 2:
            continue
        xs.append(float(parts[0]))
        uxs.append(float(parts[1]))
    if len(xs) < 2:
        raise SystemExit(f"sample file {sample_file} has fewer than 2 points")
    for i in range(len(xs) - 1):
        if uxs[i] < 0.0 <= uxs[i + 1]:
            # linear interpolation of the zero crossing
            frac = -uxs[i] / (uxs[i + 1] - uxs[i])
            x_r = xs[i] + frac * (xs[i + 1] - xs[i])
            return x_r / STEP_HEIGHT
    raise SystemExit(
        "no negative->positive Ux sign change found: either the recirculation "
        "bubble is absent (unconverged / wrong physics) or it extends past the "
        "sampled line. Refusing to fabricate a QoI value."
    )


def main() -> None:
    case_dir = Path(sys.argv[1]) if len(sys.argv) > 1 else Path.cwd()
    out_json = Path(sys.argv[2]) if len(sys.argv) > 2 else case_dir / "qoi.json"
    sample = find_sample(case_dir)
    xr_over_h = compute_xr(sample)
    qoi = {"reattachment_x_over_h": xr_over_h}
    out_json.write_text(json.dumps(qoi, indent=2) + "\n", encoding="utf-8")
    print(f"sample: {sample}")
    print(f"reattachment_x_over_h = {xr_over_h:.4f}  (x_r = {xr_over_h * STEP_HEIGHT:.6f} m)")
    print(f"written: {out_json}")
    # cfdb qoi_script protocol: the last non-empty stdout line is the QoI
    # JSON object (this case declares qoi/compute_xr.py as qoi_script).
    print(json.dumps(qoi))


if __name__ == "__main__":
    main()
