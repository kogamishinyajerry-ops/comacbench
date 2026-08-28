#!/usr/bin/env python3
"""Compute QoIs (Strouhal, Cd mean, Cl rms) from the forceCoeffs time series.

Wired into the cfdb judging path as this case's outputs.qoi_script —
pure Python standard library so it runs inside minimal solver images.

Input: postProcessing/forceCoeffs1/0/coefficient.dat (written every timestep
by the forceCoeffs function object in system/controlDict). Column names are
read from the header comment (the line naming both Cd and Cl), so the layout
differences between OpenFOAM versions do not matter.

Method (documented in case.yaml):
  1. Discard the startup transient: only t >= transient_time (default 150 s,
     ~25 shedding cycles) is used. The earlier 60 s default was found too
     short in the first full 300 s run (2026-08-11, runs/
     20260811T115926Z_cylinder_re100_openfoam_c45efbd2): on this 6000-cell
     O-grid the impulsively started wake keeps saturating until t~150 s
     (cl_rms 0.181 for t>=60 vs 0.212 for t>=150, then flat), so a 60 s
     discard systematically UNDER-predicts cl_rms by ~15%.
  2. cd_mean  = mean of Cd over the window.
  3. cl_rms   = standard deviation of Cl over the window (mean Cl ~ 0 by
     symmetry, so this is the rms of the fluctuating lift).
  4. strouhal = f_peak * D / U_inf, where f_peak is the dominant frequency of
     the Cl spectrum, searched in 0.05..0.35 Hz. The original helper used a
     numpy FFT; this stdlib version replaces it with a Goertzel power scan
     on the uniformly sampled series (forceCoeffs writes every timeStep, so
     the signal is uniform by construction) plus parabolic interpolation on
     the peak — the same peak-location estimator, evaluated directly.

Usage:
  python3 post/compute_qoi.py [case_dir] [--transient 150]
Prints a JSON object {"strouhal": ..., "cd_mean": ..., "cl_rms": ...} as the
last stdout line. Exits non-zero when the series is missing or malformed
(never fabricates a value).
"""

from __future__ import annotations

import argparse
import json
import math
import sys
from pathlib import Path

F_LO = 0.05  # Hz, search band lower bound (documented in case.yaml)
F_HI = 0.35  # Hz, search band upper bound
F_STEP = 2e-4  # Hz, coarse scan grid (parabolic refinement follows)


def load_cl_cd(coeff_dat: Path) -> tuple[list[float], list[float], list[float]]:
    """Parse coefficient.dat -> (time, cd, cl) columns via header names."""
    header_cols: list[str] | None = None
    rows: list[list[str]] = []
    for line in coeff_dat.read_text(encoding="utf-8").splitlines():
        stripped = line.strip()
        if not stripped:
            continue
        if stripped.startswith("#"):
            tokens = stripped.lstrip("#").split()
            lowered = [t.lower() for t in tokens]
            if "cd" in lowered and "cl" in lowered:
                header_cols = tokens
            continue
        rows.append(stripped.split())
    if header_cols is None or not rows:
        raise SystemExit(f"no header/data parsed from {coeff_dat}")
    lowered = [t.lower() for t in header_cols]
    i_t = lowered.index("time")
    i_cd = lowered.index("cd")
    i_cl = lowered.index("cl")
    t, cd, cl = [], [], []
    for row in rows:
        if len(row) < len(header_cols):
            continue
        try:
            t.append(float(row[i_t]))
            cd.append(float(row[i_cd]))
            cl.append(float(row[i_cl]))
        except ValueError:
            continue
    return t, cd, cl


def goertzel_power(samples: list[float], freq: float, dt: float) -> float:
    """Single-frequency DFT power via the Goertzel recurrence."""
    omega = 2.0 * math.pi * freq * dt
    coeff = 2.0 * math.cos(omega)
    s_prev = 0.0
    s_prev2 = 0.0
    for x in samples:
        s = x + coeff * s_prev - s_prev2
        s_prev2 = s_prev
        s_prev = s
    return s_prev * s_prev + s_prev2 * s_prev2 - coeff * s_prev * s_prev2


def dominant_frequency(t: list[float], cl: list[float]) -> float:
    """Peak frequency of the Cl spectrum in [F_LO, F_HI].

    Goertzel power scan on a coarse grid + parabolic interpolation on the
    peak bin. The series is uniformly sampled (forceCoeffs writes every
    timeStep); it is mean-removed and downsampled to ~0.05 s spacing —
    Nyquist 10 Hz is decades above the 0.35 Hz search band, so no
    aliasing into the band is possible from the shedding signal.
    """
    n = len(t)
    if n < 100:
        raise SystemExit(f"only {n} post-transient samples — too few for a spectrum")
    dt = (t[-1] - t[0]) / (n - 1)
    if dt <= 0.0:
        raise SystemExit("non-increasing time column in coefficient.dat")
    stride = max(1, round(0.05 / dt))
    samples = cl[::stride]
    dt_s = dt * stride
    mean = sum(samples) / len(samples)
    samples = [x - mean for x in samples]

    freqs = []
    f = F_LO
    while f <= F_HI + 1e-12:
        freqs.append(f)
        f += F_STEP
    powers = [goertzel_power(samples, f, dt_s) for f in freqs]
    i_peak = max(range(len(freqs)), key=lambda i: powers[i])
    if powers[i_peak] <= 0.0:
        raise SystemExit("degenerate Cl spectrum (zero power everywhere)")
    if 0 < i_peak < len(freqs) - 1:
        y0, y1, y2 = powers[i_peak - 1], powers[i_peak], powers[i_peak + 1]
        denom = y0 - 2.0 * y1 + y2
        if denom != 0.0:
            offset = 0.5 * (y0 - y2) / denom
            if abs(offset) <= 1.0:
                return freqs[i_peak] + offset * F_STEP
    return freqs[i_peak]


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("case_dir", nargs="?", default=".")
    ap.add_argument("--transient", type=float, default=150.0,
                    help="discard t < transient (default 150 s, ~25 cycles — see docstring)")
    ap.add_argument("--diameter", type=float, default=1.0)
    ap.add_argument("--u-inf", type=float, default=1.0)
    args = ap.parse_args()

    case_dir = Path(args.case_dir)
    root = case_dir / "postProcessing" / "forceCoeffs1"
    if not root.is_dir():
        raise SystemExit(f"no forceCoeffs1 directory: {root} (did the solver run?)")
    candidates = sorted(root.glob("*/coefficient.dat"))
    if not candidates:
        raise SystemExit(f"no coefficient.dat found under {root}")

    t, cd, cl = load_cl_cd(candidates[-1])
    window = [(ti, cdi, cli) for ti, cdi, cli in zip(t, cd, cl) if ti >= args.transient]
    if not window:
        raise SystemExit(f"no samples at t >= {args.transient} s — run too short")
    t_w = [w[0] for w in window]
    cd_w = [w[1] for w in window]
    cl_w = [w[2] for w in window]

    cd_mean = sum(cd_w) / len(cd_w)
    cl_mean = sum(cl_w) / len(cl_w)
    cl_rms = math.sqrt(sum((x - cl_mean) ** 2 for x in cl_w) / len(cl_w))
    f_peak = dominant_frequency(t_w, cl_w)
    strouhal = f_peak * args.diameter / args.u_inf

    print(json.dumps({"strouhal": strouhal, "cd_mean": cd_mean, "cl_rms": cl_rms}))


if __name__ == "__main__":
    main()
