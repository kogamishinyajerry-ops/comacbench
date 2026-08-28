#!/usr/bin/env python3
"""Compute QoIs cf_rex_5e5 and cf_rex_1e6 for the turbulent_flat_plate case.

Reads the FINAL time directory's wallShearStress field (written by the
wallShearStress_plate functionObject, writeControl writeTime):

    <latest_time>/wallShearStress     boundaryField plate value
                                      nonuniform List<vector>

and the ascii polyMesh (constant/polyMesh/{points,faces,boundary}) to get
the plate patch face-centre x coordinates. Local skin friction:

    Cf(x) = |tau_w,x| / (0.5 * rho * U_inf^2) = |tau_w,x| / 50

(simpleFoam is incompressible per-unit-density, rho = 1, U_inf = 10 m/s).
The QoIs are Cf linearly interpolated to the stations x = 0.5 m
(Re_x = 5e5) and x = 1.0 m (Re_x = 1e6). Reference: 1/7-power-law
Cf = 0.0592*Re_x^(-1/5), see reference/generate.py.

cfdb qoi_script protocol: ``python3 post/compute_qoi.py <run_case_dir>``;
the last non-empty stdout line is a JSON object. Pure Python standard
library; exits non-zero when the field or mesh is missing or malformed
(never fabricates a value).
"""

from __future__ import annotations

import json
import re
import sys
from pathlib import Path

PATCH = "plate"
STATIONS = {"cf_rex_5e5": 0.5, "cf_rex_1e6": 1.0}
# Cf = |tau_x| / (0.5 * rho * U_inf^2); rho = 1 (per-unit-density), U_inf = 10.
DYN_PRESSURE = 50.0


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


def _read_count_list(text: str) -> tuple[int, int, int]:
    """Locate the first '<count>\\n(' list in an ascii polyMesh file.

    Returns (count, index of '(', index of the line with the closing ')').
    """
    m = re.search(r"\n\s*(\d+)\s*\n\s*\(", text)
    if not m:
        raise SystemExit("malformed polyMesh file: no count/list header found")
    start = text.index("(", m.end() - 1)
    end = text.index("\n)", start)
    return int(m.group(1)), start, end


def parse_points(path: Path) -> list[tuple[float, float, float]]:
    text = path.read_text(encoding="utf-8")
    n, start, end = _read_count_list(text)
    points = []
    for line in text[start + 1 : end].splitlines():
        line = line.strip().strip("()")
        if line:
            points.append(tuple(float(v) for v in line.split()))
    if len(points) != n:
        raise SystemExit(f"{path}: expected {n} points, parsed {len(points)}")
    return points


def parse_faces(path: Path) -> list[list[int]]:
    text = path.read_text(encoding="utf-8")
    n, start, end = _read_count_list(text)
    faces = []
    for line in text[start + 1 : end].splitlines():
        line = line.strip()
        if line:
            # '4(12 13 63 62)'
            faces.append([int(v) for v in line[line.index("(") + 1 : line.rindex(")")].split()])
    if len(faces) != n:
        raise SystemExit(f"{path}: expected {n} faces, parsed {len(faces)}")
    return faces


def parse_patch_range(path: Path, patch: str) -> tuple[int, int]:
    """Return (startFace, nFaces) of the named patch from polyMesh/boundary."""
    text = path.read_text(encoding="utf-8")
    m = re.search(
        patch + r"\s*\{[^{}]*?nFaces\s+(\d+)\s*;[^{}]*?startFace\s+(\d+)\s*;",
        text,
        re.DOTALL,
    )
    if not m:
        # nFaces/startFace order is fixed in v2312 output, but accept the
        # reverse order defensively.
        m = re.search(
            patch + r"\s*\{[^{}]*?startFace\s+(\d+)\s*;[^{}]*?nFaces\s+(\d+)\s*;",
            text,
            re.DOTALL,
        )
        if not m:
            raise SystemExit(f"patch '{patch}' not found in {path}")
        return int(m.group(2)), int(m.group(1))
    return int(m.group(2)), int(m.group(1))


def face_centres_x(case_dir: Path, patch: str) -> list[float]:
    """Face-centre x coordinates of the patch faces, in patch face order."""
    mesh_dir = case_dir / "constant" / "polyMesh"
    points = parse_points(mesh_dir / "points")
    faces = parse_faces(mesh_dir / "faces")
    start_face, n_faces = parse_patch_range(mesh_dir / "boundary", patch)
    centres = []
    for fid in range(start_face, start_face + n_faces):
        face = faces[fid]
        centres.append(sum(points[v][0] for v in face) / len(face))
    return centres


def main() -> None:
    case_dir = Path(sys.argv[1]) if len(sys.argv) > 1 else Path.cwd()
    time_dir = latest_time_dir(case_dir)
    taus = parse_patch_vectors(time_dir / "wallShearStress", PATCH)
    xs = face_centres_x(case_dir, PATCH)
    if len(xs) != len(taus):
        raise SystemExit(
            f"patch face count mismatch: mesh {len(xs)} vs field {len(taus)}"
        )

    # Cf(x) sorted by x; several faces may share one x (spanwise) — average.
    cf_at_x: dict[float, list[float]] = {}
    for x, tau in zip(xs, taus):
        cf_at_x.setdefault(round(x, 9), []).append(abs(tau[0]) / DYN_PRESSURE)
    xs_sorted = sorted(cf_at_x)
    cf_sorted = [sum(cf_at_x[x]) / len(cf_at_x[x]) for x in xs_sorted]

    qoi: dict[str, float] = {}
    for name, x0 in STATIONS.items():
        if x0 < xs_sorted[0] or x0 > xs_sorted[-1]:
            raise SystemExit(f"station x={x0} outside plate extent {xs_sorted[0]}..{xs_sorted[-1]}")
        for i in range(len(xs_sorted) - 1):
            if xs_sorted[i] <= x0 <= xs_sorted[i + 1]:
                span = xs_sorted[i + 1] - xs_sorted[i]
                frac = 0.0 if span == 0.0 else (x0 - xs_sorted[i]) / span
                qoi[name] = cf_sorted[i] + frac * (cf_sorted[i + 1] - cf_sorted[i])
                break
    print(json.dumps(qoi))


if __name__ == "__main__":
    main()
