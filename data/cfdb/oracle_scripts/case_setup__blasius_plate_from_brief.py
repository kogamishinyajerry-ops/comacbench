# oracle: blasius_plate_from_brief 两阶段样例（evidence 工具通道端到端验证）
# 阶段 RUN: 复制 verification/flat_plate_blasius_of 参考算例（与 brief 同参数：
#   U=1, nu=1e-5, 站位 0.2/0.5/0.8/1.0）并注入壁面采样 functionObject
#   （wallShearStress writeFields + surfaces per-face 采样——这是模型侧应当自己
#   完成的配置，oracle 演示正确姿势）。
# 阶段 ASSEMBLE: 从 case/ 运行产物提取 Cf(x)=|tau_x|/(0.5·U²)（运动粘度制，U=1 →
#   Cf=2|wss_x|），组装 submission/ 证据包（逐文件合同见 visible/task.md）。
import json
import re
from pathlib import Path

BENCH = "/Users/Zhuanz/projects/jerry-personal/JerryDSH-COMACBench"
U_INF = 1.0

if not Path(".cfdb_assemble").exists():
    # ---------- 阶段 RUN ----------
    import shutil
    src = Path(BENCH) / "data/cfdb/verification/flat_plate_blasius_of"
    shutil.copytree(src, "case", dirs_exist_ok=True)
    # 注入壁面采样（per-face wallShearStress）——模型侧应按任务书自行配置
    ctl = Path("case/system/controlDict")
    txt = ctl.read_text()
    inject = '''
    wssPlate
    {
        type            wallShearStress;
        patches         (plate);
        writeFields     yes;
    }
    cfSample
    {
        type            surfaces;
        writeControl    writeTime;
        surfaceFormat   raw;
        fields          (wallShearStress);
        surfaces        (
            plate { type patch; patches (plate); }
        );
    }
'''
    txt = txt.replace("functions\n{", "functions\n{" + inject, 1)
    ctl.write_text(txt)
    print("case/ written with wall sampling FOs")
else:
    # ---------- 阶段 ASSEMBLE ----------
    raw_files = sorted(Path("case/postProcessing/cfSample").glob("*/wallShearStress_plate.raw"))
    assert raw_files, "no cfSample output (surfaces FO missing or solver did not run)"
    raw = raw_files[-1]  # 最晚写出时刻
    pts = []
    for ln in raw.read_text().splitlines():
        ln = ln.strip()
        if not ln or ln.startswith("#"):
            continue
        c = ln.split()
        x, wss_x = float(c[0]), float(c[3])
        if x < 0.02:  # 跳过前缘奇异区
            continue
        cf = abs(wss_x) / (0.5 * U_INF * U_INF)  # 运动粘度制 rho=1 → Cf=2|tau_x|
        pts.append((x, cf))
    pts.sort()
    assert pts and pts[0][0] <= 0.2 and pts[-1][0] >= 1.0, "x coverage must bracket 0.2..1.0"

    log_solve = Path("log.solve")
    log_mesh = Path("log.block_mesh")
    sub = Path("submission")
    (sub / "evidence" / "samples").mkdir(parents=True, exist_ok=True)
    mesh_cells = 0
    m = re.search(r"cells:\s+(\d+)", log_mesh.read_text(errors="ignore")) if log_mesh.exists() else None
    if m:
        mesh_cells = int(m.group(1))
    manifest = {
        "solver": "simpleFoam (OpenFOAM v2312, docker opencfd/openfoam-default:2312)",
        "mesh_cells": mesh_cells,
        "timing": {"wall_time_sec": 0.0},
        "notes": "laminar simpleFoam, structured hex; Cf extracted from per-face "
                 "wallShearStress sampled on plate patch",
    }
    (sub / "manifest.json").write_text(json.dumps(manifest, indent=2), encoding="utf-8")
    (sub / "evidence" / "solver.log").write_text(
        log_solve.read_text(errors="ignore"), encoding="utf-8")
    (sub / "evidence" / "mesh_report.txt").write_text(
        log_mesh.read_text(errors="ignore"), encoding="utf-8")
    with open(sub / "evidence" / "samples" / "cf_distribution.csv", "w") as f:
        f.write("x,cf\n")
        for x, cf in pts:
            f.write(f"{x:.6f},{cf:.8g}\n")
    print(f"submission/ written: {len(pts)} cf samples, x [{pts[0][0]:.3f}, {pts[-1][0]:.3f}]")
