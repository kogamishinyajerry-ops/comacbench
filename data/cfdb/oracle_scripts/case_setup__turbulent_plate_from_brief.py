# oracle: turbulent_plate_from_brief 两阶段（evidence 工具通道）——参考算例 validation/turbulent_flat_plate
import json
from pathlib import Path
BENCH = Path("/Users/Zhuanz/projects/jerry-personal/JerryDSH-COMACBench")
PATCH = "plate"
DYN_PRESSURE = 50.0
import re
def _read_count_list(text):
    m = re.search(r"\n\s*(\d+)\s*\n\s*\(", text)
    if not m:
        raise SystemExit("malformed polyMesh: no count/list header")
    start = text.index("(", m.end() - 1)
    end = text.index("\n)", start)
    return int(m.group(1)), start, end

def parse_points(path):
    text = path.read_text()
    n, start, end = _read_count_list(text)
    pts = [tuple(float(v) for v in ln.strip().strip("()").split())
           for ln in text[start+1:end].splitlines() if ln.strip()]
    assert len(pts) == n
    return pts

def parse_faces(path):
    text = path.read_text()
    n, start, end = _read_count_list(text)
    faces = [[int(v) for v in ln.strip()[ln.strip().index("(")+1:ln.strip().rindex(")")].split()]
             for ln in text[start+1:end].splitlines() if ln.strip()]
    assert len(faces) == n
    return faces

def patch_range(pm_dir, patch):
    text = (pm_dir / "boundary").read_text()
    m = re.search(patch + r"\s*\{[^{}]*?nFaces\s+(\d+)\s*;[^{}]*?startFace\s+(\d+)\s*;", text, re.DOTALL)
    if not m:
        m = re.search(patch + r"\s*\{[^{}]*?startFace\s+(\d+)\s*;[^{}]*?nFaces\s+(\d+)\s*;", text, re.DOTALL)
        return int(m.group(2)), int(m.group(1))
    return int(m.group(2)), int(m.group(1))

def face_centre_coords(case_dir, patch, axis):
    pm = case_dir / "constant" / "polyMesh"
    pts = parse_points(pm / "points")
    faces = parse_faces(pm / "faces")
    start, n = patch_range(pm, patch)
    return [sum(pts[i][axis] for i in f) / len(f) for f in faces[start:start+n]]

def parse_patch_vectors(field_path, patch):
    text = field_path.read_text()
    m = re.search(patch + r"\s*\{[^{}]*?value\s+nonuniform\s+List<vector>\s+(\d+)\s*\(", text, re.DOTALL)
    if not m:
        raise SystemExit(f"no vector list for patch {patch}")
    n = int(m.group(1))
    start = text.index("(", m.end() - 1)
    end = text.index("\n)", start)
    vals = [tuple(float(v) for v in ln.strip().strip("()").split())
            for ln in text[start+1:end].splitlines() if ln.strip()]
    assert len(vals) == n
    return vals

def parse_patch_scalars(field_path, patch):
    text = field_path.read_text()
    m = re.search(patch + r"\s*\{[^{}]*?value\s+nonuniform\s+List<scalar>\s+(\d+)\s*\(", text, re.DOTALL)
    if not m:
        raise SystemExit(f"no scalar list for patch {patch}")
    n = int(m.group(1))
    start = text.index("(", m.end() - 1)
    end = text.index("\n)", start)
    vals = [float(v) for v in text[start+1:end].split()]
    assert len(vals) == n
    return vals

def latest_time_dir(case_dir):
    times = [p for p in case_dir.iterdir() if p.is_dir() and p.name.replace(".", "").isdigit()]
    assert times, "no time dirs"
    return max(times, key=lambda p: float(p.name))

def write_manifest(notes):
    sl = Path("log.solve")
    bm = Path("log.block_mesh")
    (sub / "evidence" / "solver.log").write_text(
        sl.read_text(errors="ignore") if sl.exists() else "(no log)\n", encoding="utf-8")
    (sub / "evidence" / "mesh_report.txt").write_text(
        bm.read_text(errors="ignore") if bm.exists() else "(no log)\n", encoding="utf-8")
    (sub / "manifest.json").write_text(json.dumps({
        "solver": "OpenFOAM v2312 (docker opencfd/openfoam-default:2312)",
        "timing": {"wall_time_sec": 0.0}, "notes": notes,
    }, indent=2), encoding="utf-8")

if Path(".cfdb_assemble").exists():
    sub = Path("submission")
    (sub / "evidence" / "samples").mkdir(parents=True, exist_ok=True)
    case_dir = Path("case")

    latest = latest_time_dir(case_dir)
    tau = parse_patch_vectors(latest / "wallShearStress", PATCH)
    xs = face_centre_coords(case_dir, PATCH, 0)
    pts = sorted((x, abs(t[0]) / DYN_PRESSURE) for x, t in zip(xs, tau) if 0.1 <= x <= 1.9)
    assert pts and pts[0][0] <= 0.5 and pts[-1][0] >= 1.0, "station coverage"
    with open(sub / "evidence" / "samples" / "cf_distribution.csv", "w") as f:
        f.write("x,cf\n")
        for x, cf in pts:
            f.write(f"{x:.6f},{cf:.8g}\n")
    write_manifest('turbulent flat plate RANS; Cf from wallShearStress plate patch')
    print("submission/ written")
    raise SystemExit(0)

import shutil
shutil.copytree(BENCH / "data/cfdb/validation/turbulent_flat_plate", "case", dirs_exist_ok=True)

print("case/ written from reference case")
