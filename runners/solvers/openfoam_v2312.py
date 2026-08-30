"""openfoam_v2312.py — OpenFOAM ESI v2312 求解器后端（cfdb 域专用，dev 终端）。

事实与决策（2026-08-28 核验）：
- cfdb(GLM-CFD-Benchmark) 案例为 ESI v2312 方言（system/blockMeshDict、
  constant/transportProperties 等），与 foam_basic 的 Foundation v10 不兼容；
- 本机镜像 opencfd/openfoam-default:2312（arm64 原生，非 qemu）；
  环境需显式 `source /usr/lib/openfoam/openfoam2312/etc/bashrc`
  （Debian 布局；/opt/openfoam2312 是软链目标但 bashrc 在 /usr/lib 下）；
- 判分语义 = cfdb 上游 managed 模式：按案例 case.yaml 声明的 steps 真实执行
  （blockMesh/setFields/solve/postProcess…，命令模板含 {{ run_dir }}），
  全部 critical 步骤退出 0 视为执行成功；
- QoI 不在本模块：由 simulation_agent 的 cfdb_cfd_qoi 分支在宿主以
  `sys.executable -B <qoi_script> <case_dir>` 调用案例冻结的 compute_qoi.py
  （与 cfdb 上游"冻结判分材料在宿主执行"同一 trust posture）。

替换指引（intranet）：cfdb case_setup evidence 模式判分侧不跑求解器；
managed 模式可换商业求解器批处理（fluent.py 同构），adapter 不感知。
"""

from __future__ import annotations

import os
import subprocess
import time
from pathlib import Path
from typing import Any

IMAGE = "opencfd/openfoam-default:2312"
BASHRC = "/usr/lib/openfoam/openfoam2312/etc/bashrc"
MOUNT = "/work"
DEFAULT_STEP_TIMEOUT = 300.0


class OpenFOAMV2312:
    """按 cfdb 案例 steps 声明执行的求解器后端（solver_backend: openfoam-v2312-docker）。"""

    name = "openfoam-v2312-docker"

    def run_steps(self, work_dir: Path, steps: list[dict],
                  total_timeout_s: float) -> dict[str, Any]:
        """顺序执行 steps；返回 {ok, duration_s, steps:[{name,exit,duration,timeout}], tail}。

        steps 元素（来自案例 case.yaml，任务 YAML 冻结副本）：
          {name, command: "blockMesh -case {{ run_dir }}/case",
           timeout_sec, critical}
        """
        t0 = time.time()
        out_steps: list[dict[str, Any]] = []
        tail = ""
        ok = True
        for st in steps:
            # 上游双模板变量：run_dir=挂载根，case_dir=算例目录（naca0012_sa_tmr 用后者）
            cmd = (str(st["command"])
                   .replace("{{ run_dir }}", MOUNT)
                   .replace("{{ case_dir }}", f"{MOUNT}/case"))
            step_timeout = float(st.get("timeout_sec") or DEFAULT_STEP_TIMEOUT)
            budget = min(step_timeout, max(30.0, total_timeout_s - (time.time() - t0)))
            if budget < 30.0:
                out_steps.append({"name": st["name"], "exit": -1, "duration_s": 0.0,
                                  "timeout": True})
                ok = False
                break
            try:
                # --user 宿主 uid：OpenFOAM dynamicCode::checkSecurity 拒绝 root 编译
                # coded functionObject（taylor_green 2026-08-29 实测踩坑）；且产物归
                # 宿主用户，不产生 root 属主文件。
                r = subprocess.run(
                    ["docker", "run", "--rm",
                     "--user", f"{os.getuid()}:{os.getgid()}",
                     "-v", f"{work_dir.resolve()}:{MOUNT}", "-w", MOUNT,
                     "--entrypoint", "bash", IMAGE,
                     "-c", f"source {BASHRC} && {cmd} > log.{st['name']} 2>&1"],
                    capture_output=True, text=True, timeout=budget)
                exit_code, timed_out = r.returncode, False
            except subprocess.TimeoutExpired:
                exit_code, timed_out = -1, True
            duration = round(time.time() - t0, 1)
            # 命令以 -w /work 执行且重定向到 log.<name> → 日志在工作目录根（非 case/ 内）
            log_path = work_dir / f"log.{st['name']}"
            if log_path.exists():
                tail = "\n".join(log_path.read_text(errors="ignore").splitlines()[-5:])
            out_steps.append({"name": st["name"], "exit": exit_code,
                              "duration_s": duration, "timeout": timed_out})
            if timed_out or (exit_code != 0 and st.get("critical", True)):
                ok = False
                break
        return {"ok": ok, "duration_s": round(time.time() - t0, 1),
                "steps": out_steps, "tail": tail}

    def execution_ok(self, work_dir: Path, steps_result: dict[str, Any]) -> bool:
        """cfdb managed 语义：全部 critical 步骤退出 0（最终判据仍是冻结 QoI 脚本）。"""
        return bool(steps_result.get("ok"))
