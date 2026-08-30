# oracle: pipe_from_brief 两阶段（evidence 工具通道）——参考算例 verification/pipe_poiseuille
import json
import math
from pathlib import Path
BENCH = Path("/Users/Zhuanz/projects/jerry-personal/JerryDSH-COMACBench")
R = 0.005
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

    set_files = sorted(Path("case/postProcessing").glob("*/*/radialProfile_U.xy")) or \
                sorted(Path("case/postProcessing").glob("*/*/radialProfile*.xy"))
    assert set_files, "no radialProfile set output"
    rows = []
    for ln in set_files[-1].read_text().splitlines():
        ln = ln.strip()
        if not ln or ln.startswith("#"):
            continue
        c = ln.replace(",", " ").split()
        if len(c) >= 2:
            try:
                r, u = float(c[0]), float(c[1])
            except ValueError:
                continue
            rows.append((r, u))
    rows.sort()
    assert rows and abs(rows[-1][0] - R) < 1e-4, "profile must reach r=R"
    with open(sub / "evidence" / "samples" / "profile.csv", "w") as f:
        f.write("r,u\n")
        for r, u in rows:
            f.write(f"{r:.8f},{u:.8g}\n")
    write_manifest('laminar pipe Poiseuille Re_D=20; radial U profile at x=0.06')
    print("submission/ written")
    raise SystemExit(0)

import shutil
shutil.copytree(BENCH / "data/cfdb/verification/pipe_poiseuille", "case", dirs_exist_ok=True)

inject = (
    "\n"
    "    radialProfile\n"
    "    {\n"
    "        type            sets;\n"
    "        libs            (sampling);\n"
    "        writeControl    timeStep;\n"
    "        writeInterval   100;\n"
    "        interpolationScheme cellPoint;\n"
    "        setFormat       raw;\n"
    "        sets\n"
    "        (\n"
    "            line\n"
    "            {\n"
    "                type    uniform;\n"
    "                axis    y;\n"
    "                start   (0.06 0.00025 0);\n"
    "                end     (0.06 0.005 0);\n"
    "                nPoints 60;\n"
    "            }\n"
    "        );\n"
    "        fields          (U);\n"
    "    }\n"
)
ctl = Path("case/system/controlDict")
txt = ctl.read_text()
if "radialProfile" not in txt:
    txt = txt.replace("functions\n{", "functions\n{" + inject, 1)
    ctl.write_text(txt)

print("case/ written from reference case")
