# oracle: taylor_green_from_brief 两阶段（evidence 工具通道）——参考算例 verification/taylor_green_vortex
import json
import math
from pathlib import Path
BENCH = Path("/Users/Zhuanz/projects/jerry-personal/JerryDSH-COMACBench")

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

    import re
    times = [p for p in case_dir.iterdir() if p.is_dir() and p.name.replace(".", "").isdigit()]
    assert times, "no time dirs"
    def parse_vector_field(path):
        text = path.read_text()
        m = re.search(r"internalField\s+nonuniform\s+List<vector>\s+(\d+)\s*\(", text)
        if not m:
            return []  # uniform 占位场跳过
        n = int(m.group(1))
        start = text.index("(", m.end() - 1)
        end = text.index("\n)", start)
        vals = [tuple(float(v) for v in ln.strip().strip("()").split())
                for ln in text[start+1:end].splitlines() if ln.strip()]
        assert len(vals) == n
        return vals
    ke_rows = []
    for td in sorted(times, key=lambda p: float(p.name)):
        if not (td / "U").exists():
            continue
        vals = parse_vector_field(td / "U")
        if not vals:
            continue
        ke = 0.5 * sum(u*u + v*v for u, v, _ in vals) / len(vals)
        ke_rows.append((float(td.name), ke))
    assert len(ke_rows) >= 2, "KE history needs >=2 written times"
    with open(sub / "evidence" / "samples" / "ke_history.csv", "w") as f:
        f.write("time,ke\n")
        for t, ke in ke_rows:
            f.write(f"{t:.6g},{ke:.8g}\n")
    lf = sorted((case_dir / "postProcessing").glob("sampleLine/*/line_p_U.xy"))
    assert lf, "no sampleLine xy output"
    lf = sorted(lf, key=lambda q: float(q.parent.name))[-1]
    lrows = []
    for ln in lf.read_text().splitlines():
        ln = ln.strip()
        if not ln or ln.startswith("#"):
            continue
        c = ln.split()
        if len(c) >= 4:
            try:
                lrows.append((float(c[0]), float(c[2]), float(c[3])))
            except ValueError:
                continue
    assert lrows, "line sample empty"
    with open(sub / "evidence" / "samples" / "line_end.csv", "w") as f:
        f.write("x,u,v\n")
        for x, u, v in lrows:
            f.write(f"{x:.8f},{u:.8g},{v:.8g}\n")
    write_manifest('Taylor-Green vortex icoFoam; KE history + end-time line sample')
    print("submission/ written")
    raise SystemExit(0)

import shutil
shutil.copytree(BENCH / "data/cfdb/verification/taylor_green_vortex", "case", dirs_exist_ok=True)

print("case/ written from reference case")
