# oracle: taylor_couette_from_brief 两阶段（evidence 工具通道）——参考算例 verification/taylor_couette（参数与 brief 一致）
# 阶段 ASSEMBLE（.cfdb_assemble 存在）: 从 case/ 运行产物提取原始分布 -> submission/
# 阶段 RUN: 逐字复制参考算例为 case/{notes}
import json
from pathlib import Path

BENCH = Path("/Users/Zhuanz/projects/jerry-personal/JerryDSH-COMACBench")
if Path(".cfdb_assemble").exists():
    sub = Path("submission")
    (sub / "evidence" / "samples").mkdir(parents=True, exist_ok=True)
    csv_files = sorted(Path("case/postProcessing/sampleDict").glob("*/radial_U.csv"))
    assert csv_files, "no sampleDict output"
    rows = []
    for ln in csv_files[-1].read_text().splitlines():
        ln = ln.strip()
        if not ln or ln.startswith("#"):
            continue
        c = ln.split(",")
        if len(c) >= 4:
            try:
                r0, uy = float(c[0]), float(c[2])   # distance col + U_1（theta=0 切向 = U_y）
            except ValueError:
                continue  # 跳过带引号的表头行
            rows.append((0.051 + r0, uy))       # line starts just outside inner cylinder
    assert rows, "empty sample"
    with open(sub / "evidence" / "samples" / "profile.csv", "w") as f:
        f.write("r,u_theta\n")
        for r, ut in rows:
            f.write(f"{r:.8f},{ut:.8g}\n")
    sl = Path("log.solve")
    bm = Path("log.block_mesh")
    (sub / "evidence" / "solver.log").write_text(
        sl.read_text(errors="ignore") if sl.exists() else "(solver log not found)\n", encoding="utf-8")
    (sub / "evidence" / "mesh_report.txt").write_text(
        bm.read_text(errors="ignore") if bm.exists() else "(blockMesh log not found)\n", encoding="utf-8")
    (sub / "manifest.json").write_text(json.dumps({
        "solver": "OpenFOAM v2312 (docker opencfd/openfoam-default:2312)",
        "timing": {"wall_time_sec": 0.0},
        "notes": 'circular Couette icoFoam to steady; radial profile via sampleDict postProcess',
    }, indent=2), encoding="utf-8")
    print(f"submission/ written")
    raise SystemExit(0)

import shutil
shutil.copytree(BENCH / "data/cfdb/verification/taylor_couette", "case", dirs_exist_ok=True)

print("case/ written from reference case")
