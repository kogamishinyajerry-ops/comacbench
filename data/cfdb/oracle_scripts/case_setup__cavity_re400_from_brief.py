# oracle: cavity_re400_from_brief 两阶段（evidence 工具通道）——参考算例 validation/lid_driven_cavity_re400（参数与 brief 一致）
# 阶段 ASSEMBLE（.cfdb_assemble 存在）: 从 case/ 运行产物提取原始分布 -> submission/
# 阶段 RUN: 逐字复制参考算例为 case/{notes}
import json
from pathlib import Path

BENCH = Path("/Users/Zhuanz/projects/jerry-personal/JerryDSH-COMACBench")
if Path(".cfdb_assemble").exists():
    sub = Path("submission")
    (sub / "evidence" / "samples").mkdir(parents=True, exist_ok=True)
    probe_files = sorted(Path("case/postProcessing/probes").glob("*/U"))
    assert probe_files, "no probes output"
    lines = probe_files[-1].read_text().splitlines()
    coords = []
    for ln in lines:
        if ln.startswith("# Probe"):
            c = ln.strip("# Probe ()").split()
            coords.append(float(c[-2]))  # y of probe
    data = [ln for ln in lines if ln.strip() and not ln.startswith("#")]
    assert data and coords, "probes empty"
    vals = [float(v) for v in data[-1].replace("(", " ").replace(")", " ").split()][1:]
    assert len(vals) == 3 * len(coords), "probe/vector count mismatch"
    rows = [(yc, vals[3 * i], vals[3 * i + 1]) for i, yc in enumerate(coords)]
    with open(sub / "evidence" / "samples" / "centerline.csv", "w") as f:
        f.write("y,u,v\n")
        for y, u, vv in rows:
            f.write(f"{y:.8f},{u:.8g},{vv:.8g}\n")
    sl = Path("log.solve")
    bm = Path("log.block_mesh")
    (sub / "evidence" / "solver.log").write_text(
        sl.read_text(errors="ignore") if sl.exists() else "(solver log not found)\n", encoding="utf-8")
    (sub / "evidence" / "mesh_report.txt").write_text(
        bm.read_text(errors="ignore") if bm.exists() else "(blockMesh log not found)\n", encoding="utf-8")
    (sub / "manifest.json").write_text(json.dumps({
        "solver": "OpenFOAM v2312 (docker opencfd/openfoam-default:2312)",
        "timing": {"wall_time_sec": 0.0},
        "notes": 'lid-driven cavity Re=400 icoFoam; centerline probes final time',
    }, indent=2), encoding="utf-8")
    print(f"submission/ written")
    raise SystemExit(0)

import shutil
shutil.copytree(BENCH / "data/cfdb/validation/lid_driven_cavity_re400", "case", dirs_exist_ok=True)

print("case/ written from reference case")
