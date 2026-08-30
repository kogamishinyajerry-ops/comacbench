# oracle: heat_conduction_from_brief 两阶段（evidence 工具通道）——参考算例 verification/heat_conduction_1d（参数与 brief 一致）
# 阶段 ASSEMBLE（.cfdb_assemble 存在）: 从 case/ 运行产物提取原始分布 -> submission/
# 阶段 RUN: 逐字复制参考算例为 case/{notes}
import json
from pathlib import Path

BENCH = Path("/Users/Zhuanz/projects/jerry-personal/JerryDSH-COMACBench")
if Path(".cfdb_assemble").exists():
    sub = Path("submission")
    (sub / "evidence" / "samples").mkdir(parents=True, exist_ok=True)
    import re
    times = [p for p in Path("case").iterdir() if p.is_dir() and p.name.replace(".", "").isdigit()]
    assert times, "no time dirs"
    latest = max(times, key=lambda p: float(p.name))
    text = (latest / "T").read_text()
    m = re.search(r"internalField\s+nonuniform\s+List<scalar>\s+(\d+)\s*\(", text)
    n = int(m.group(1))
    start = text.index("(", m.end() - 1)
    end = text.index("\n)", start)
    T = [float(v) for v in text[start + 1:end].split()]
    assert len(T) == n, "T parse mismatch"
    with open(sub / "evidence" / "samples" / "profile.csv", "w") as f:
        f.write("x,temperature\n")
        for i, tv in enumerate(T):
            f.write(f"{(i + 0.5) * 0.01:.8f},{tv:.8g}\n")
    sl = Path("log.solve")
    bm = Path("log.block_mesh")
    (sub / "evidence" / "solver.log").write_text(
        sl.read_text(errors="ignore") if sl.exists() else "(solver log not found)\n", encoding="utf-8")
    (sub / "evidence" / "mesh_report.txt").write_text(
        bm.read_text(errors="ignore") if bm.exists() else "(blockMesh log not found)\n", encoding="utf-8")
    (sub / "manifest.json").write_text(json.dumps({
        "solver": "OpenFOAM v2312 (docker opencfd/openfoam-default:2312)",
        "timing": {"wall_time_sec": 0.0},
        "notes": '1D steady conduction laplacianFoam; T profile from final field',
    }, indent=2), encoding="utf-8")
    print(f"submission/ written")
    raise SystemExit(0)

import shutil
shutil.copytree(BENCH / "data/cfdb/verification/heat_conduction_1d", "case", dirs_exist_ok=True)

print("case/ written from reference case")
