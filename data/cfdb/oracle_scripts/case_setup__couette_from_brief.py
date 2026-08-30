# oracle: couette_from_brief 两阶段（evidence 工具通道）——参考算例 verification/couette_shear（参数与 brief 一致）
# 阶段 ASSEMBLE（.cfdb_assemble 存在）: 从 case/ 运行产物提取原始分布 -> submission/
# 阶段 RUN: 逐字复制参考算例为 case/{notes}
import json
from pathlib import Path

BENCH = Path("/Users/Zhuanz/projects/jerry-personal/JerryDSH-COMACBench")
if Path(".cfdb_assemble").exists():
    sub = Path("submission")
    (sub / "evidence" / "samples").mkdir(parents=True, exist_ok=True)
    raw_files = sorted(Path("case/postProcessing/profileSample").glob("*/lineY_U.xy") or sorted(Path("case/postProcessing/profileSample").glob("*/lineY_U.raw")))
    assert raw_files, "no profileSample output"
    rows = []
    for ln in raw_files[-1].read_text().splitlines():
        ln = ln.strip()
        if not ln or ln.startswith("#"):
            continue
        c = ln.split()
        if len(c) >= 4:
            rows.append((float(c[0]), float(c[1])))
    assert rows, "empty sample"
    with open(sub / "evidence" / "samples" / "profile.csv", "w") as f:
        f.write("y,u\n")
        for y, u in rows:
            f.write(f"{y:.8f},{u:.8g}\n")
    sl = Path("log.solve")
    bm = Path("log.block_mesh")
    (sub / "evidence" / "solver.log").write_text(
        sl.read_text(errors="ignore") if sl.exists() else "(solver log not found)\n", encoding="utf-8")
    (sub / "evidence" / "mesh_report.txt").write_text(
        bm.read_text(errors="ignore") if bm.exists() else "(blockMesh log not found)\n", encoding="utf-8")
    (sub / "manifest.json").write_text(json.dumps({
        "solver": "OpenFOAM v2312 (docker opencfd/openfoam-default:2312)",
        "timing": {"wall_time_sec": 0.0},
        "notes": 'planar Couette transient icoFoam to steady; profile from profileSample set line',
    }, indent=2), encoding="utf-8")
    print(f"submission/ written")
    raise SystemExit(0)

import shutil
shutil.copytree(BENCH / "data/cfdb/verification/couette_shear", "case", dirs_exist_ok=True)

print("case/ written from reference case")
