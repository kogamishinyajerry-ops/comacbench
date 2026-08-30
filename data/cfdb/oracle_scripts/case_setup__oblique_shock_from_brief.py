# oracle: oblique_shock_from_brief 两阶段（evidence 工具通道）——参考算例 verification/oblique_shock
import json
import math
from pathlib import Path
BENCH = Path("/Users/Zhuanz/projects/jerry-personal/JerryDSH-COMACBench")
GAMMA = 1.4
R_GAS = 287.058
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

    probe_dir = None
    for d in sorted(Path("case/postProcessing/probeLine").glob("*/"), reverse=True):
        if (d / "U").exists():
            probe_dir = d
            break
    assert probe_dir, "no probeLine output"
    u_lines = [ln for ln in (probe_dir / "U").read_text().splitlines()
               if ln.strip() and not ln.startswith("#")]
    p_lines = [ln for ln in (probe_dir / "p").read_text().splitlines()
               if ln.strip() and not ln.startswith("#")]
    t_lines = [ln for ln in (probe_dir / "T").read_text().splitlines()
               if ln.strip() and not ln.startswith("#")]
    assert u_lines and p_lines and t_lines
    ys = [round(0.001 + 0.005 * i, 3) for i in range(58)]
    def vecs(ln):
        return [float(v) for v in ln.replace("(", " ").replace(")", " ").split()][1:]
    uv = vecs(u_lines[-1]); tv = vecs(t_lines[-1])
    n = min(len(ys), len(uv) // 3, len(tv))
    rows = []
    for i in range(n):
        ux, uy, uz = uv[3*i], uv[3*i+1], uv[3*i+2]
        speed = math.sqrt(ux*ux + uy*uy + uz*uz)
        if tv[i] <= 0:
            continue  # 楔体固体内探针
        rows.append((ys[i], speed / math.sqrt(GAMMA * R_GAS * tv[i])))
    rows.sort()
    assert rows[0][0] <= 0.15 <= rows[-1][0], "probe y coverage"
    with open(sub / "evidence" / "samples" / "mach_profile.csv", "w") as f:
        f.write("y,mach\n")
        for y, m in rows:
            f.write(f"{y:.8f},{m:.8g}\n")
    write_manifest('oblique shock M1=2 wedge 10deg; post-shock Mach profile at x=0.6')
    print("submission/ written")
    raise SystemExit(0)

import shutil
shutil.copytree(BENCH / "data/cfdb/verification/oblique_shock", "case", dirs_exist_ok=True)

inject = (
    "\n"
    "    probeLine\n"
    "    {\n"
    "        type            probes;\n"
    "        libs            (sampling);\n"
    "        writeControl    timeStep;\n"
    "        writeInterval   100;\n"
    "        fields          (U p T);\n"
    "        probeLocations\n"
    "        (\n"
    + "".join(f"            (0.6 {0.001 + 0.005 * i:.3f} 0)\n" for i in range(58))
    + "        );\n"
    "    }\n"
)
ctl = Path("case/system/controlDict")
txt = ctl.read_text()
if "probeLine" not in txt:
    txt = txt.replace("functions\n{", "functions\n{" + inject, 1)
    ctl.write_text(txt)

print("case/ written from reference case")
