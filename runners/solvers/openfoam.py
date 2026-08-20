"""openfoam.py — OpenFOAM 求解器后端（dev 终端：docker openfoam/openfoam10-paraview510）。

事实与决策（2026-08-19 核验）：
- dev 终端无本机 OpenFOAM；可用 docker 镜像两枚：
  * openfoam/openfoam10-paraview510（amd64，qemu 模拟；**v10 = 上游 FoamBench 指定版本**）
  * opencfd/openfoam-default:2312（arm64 原生，但 ESI 方言与 GT 算例不兼容：
    pisoFoam 需 constant/transportProperties，GT 用 Foundation v10 的 momentumTransport）
- 取 v10（amd64 模拟，实测 Cavity 6.5s/例，可接受），保证与上游判据/方言一致。

替换指引（intranet）：新增 fluent.py 实现 Solver 接口（fluent -t<N> -g -i case.jou），
adapter 与任务 YAML 不感知后端差异。
"""

from __future__ import annotations

import subprocess
import time
from pathlib import Path
from typing import Any

IMAGE = "openfoam/openfoam10-paraview510"
DOCKER_ENV = "source /opt/openfoam10/etc/bashrc"


class OpenFOAMSolver:
    name = "openfoam10-docker"

    def run_case(self, case_dir: Path, timeout_s: float) -> dict[str, Any]:
        t0 = time.time()
        try:
            r = subprocess.run(
                ["docker", "run", "--rm", "--platform", "linux/amd64",
                 "-v", f"{case_dir.resolve()}:/case", "-w", "/case",
                 "--entrypoint", "bash", IMAGE,
                 "-c", f"{DOCKER_ENV}; ./Allrun"],
                capture_output=True, text=True, timeout=timeout_s)
            return {"ok": r.returncode == 0, "exit": r.returncode,
                    "stdout": r.stdout[-4000:], "stderr": r.stderr[-4000:],
                    "duration_s": round(time.time() - t0, 1), "timeout": False,
                    "last_time": _last_time_dir(case_dir)}
        except subprocess.TimeoutExpired:
            return {"ok": False, "exit": -1, "stdout": "", "stderr": "docker timeout",
                    "duration_s": round(time.time() - t0, 1), "timeout": True,
                    "last_time": None}

    def execution_ok(self, case_dir: Path) -> bool:
        """官方 execution_report.py 语义：任一 log.*Foam 倒数第二行 == 'End'。"""
        for p in Path(case_dir).rglob("log.*Foam"):
            try:
                lines = p.read_text(errors="ignore").splitlines()
            except OSError:
                continue
            if len(lines) > 1 and lines[-2].strip() == "End":
                return True
        return False


def _last_time_dir(case_dir: Path) -> str | None:
    cands = [d.name for d in Path(case_dir).iterdir()
             if d.is_dir() and _is_time(d.name)]
    return max(cands, key=float) if cands else None


def _is_time(name: str) -> bool:
    try:
        float(name)
        return True
    except ValueError:
        return False


def get_solver(name: str):
    if name == OpenFOAMSolver.name or name == "openfoam":
        return OpenFOAMSolver()
    raise ValueError(f"未知求解器后端: {name}（dev 仅 openfoam10-docker；intranet 增 fluent/starccm）")
