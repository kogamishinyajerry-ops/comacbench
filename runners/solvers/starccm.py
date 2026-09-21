"""starccm.py — commercial_cfd 线的 StarCCM+ 执行后端（Windows dev 终端实现）。

职责（与 solvers/calculix.py、openfoam.py 同构：求解器无关原则下，本模块只负责
「把 starccm+ 批处理跑起来 + 把执行状态带回来」，判分仍在 adapter/grader）：

  starccm_binary()        starccm+ 可执行定位（STARCCM_BIN > 安装探测 > PATH）
  run_starccm(workdir, macro, timeout_s, sim)
                         在 workdir 下 `starccm+ -batch macro.java [-sim file.sim]`
                         执行，墙钟超时硬杀，返回 {exit, timeout, duration_s,
                         stdout_tail}。非零退出 = macro/journal 错误或求解失败
                         （simulation_failed）。

架构依据：
- runners/solvers/__init__.py 接口契约：Solver 类（run_case/execution_ok），
  RunResult {ok, exit, stdout, stderr, duration_s, timeout, last_time}；
- env-matrix.md §3：StarCCM+ 批处理方式 = `starccm+ -batch macro.java`（Java macro）；
- registry：nasa_tmr.verification / crm_dpw_hlpw.coarse 的 env_class=commercial_cfd，
  「求解改用内网 Fluent/StarCCM，不依赖 OpenFOAM」。

环境（2026-09-21 实测）：
- STAR-CCM+ 19.02.009-R8（R8/2024），安装于
  C:\\Program Files\\Siemens\\19.02.009-R8\\STAR-CCM+19.02.009-R8\\star\\bin\\starccm+.bat
- 许可：CDLMD_LICENSE_FILE=1999@Jerry（本机 FLEXlm License Manager 注册，
  HKLM\\SOFTWARE\\FLEXlm License Manager）；批处理占用 power-on-demand/compute
  座席，调度窗口纪律见 env-matrix.md §3。
- 批处理语言：Java macro（录制回放），R8 的 macro API 已知削减（probe/
  getValue(coordinate)/DynamicQuerySelectorInput 反射不可用）——macro 内部只走
  稳定 API 面，复杂取值由导出场文件 + grader 侧 field_reader 完成。

超时纪律：Windows 无进程组 killpg，按 agent.py 同款分支 proc.kill()；
starccm+.bat 为包装脚本，kill 后残余 java 子进程由 -batch 会话自身回收。

判分边界：本层不解析任何物理量；QoI 抽取走 macro 导出的表/场文件，
由 adapter 侧（foam_nmse 同级）读取——遵循「grader 只认产物+判据+场结果」。
"""

from __future__ import annotations

import os
import re
import shutil
import subprocess
import time
from pathlib import Path
from typing import Any

# Windows 安装探测路径（19.02.009-R8 实测）；intranet 层版本锁定时以 STARCCM_BIN 覆写
_CANDIDATE_BINS = (
    r"C:\Program Files\Siemens\19.02.009-R8\STAR-CCM+19.02.009-R8\star\bin\starccm+.bat",
    r"D:\Siemens\19.02.009-R8\STAR-CCM+19.02.009-R8\star\bin\starccm+.bat",
)


def starccm_binary() -> str:
    cand = os.environ.get("STARCCM_BIN")
    if cand and Path(cand).exists():
        return cand
    for c in _CANDIDATE_BINS:
        if Path(c).exists():
            return c
    which = shutil.which("starccm+")
    if which:
        return which
    probed = "、".join(_CANDIDATE_BINS) or "（无安装探测路径）"
    raise RuntimeError(
        f"未找到 starccm+（尝试 STARCCM_BIN、{probed} 与 PATH）。"
        "设 STARCCM_BIN 指向 starccm+.bat（Siemens 安装 star/bin 下）。")


def run_starccm(workdir: str | Path, macro: str, timeout_s: float, *,
                sim: str | None = None, power_off: bool = True) -> dict[str, Any]:
    """starccm+ -batch macro.java 执行；超时硬杀。

    macro 不带 .java 后缀与 sim 不带 .sim 后缀均按 STAR-CCM+ CLI 惯例传全名或
    基名皆可（这里原样传递，调用方负责与文件名一致）。
    """
    binp = starccm_binary()
    cmd = [binp, "-batch", macro]
    if sim:
        cmd += ["-sim", sim]
    t0 = time.time()
    env = dict(os.environ)
    env.setdefault("JAVA_TOOL_OPTIONS", "-Dfile.encoding=UTF-8")
    proc = subprocess.Popen(
        cmd, cwd=str(workdir),
        stdout=subprocess.PIPE, stderr=subprocess.STDOUT, text=True,
        encoding="utf-8", errors="replace", env=env)
    try:
        out, _ = proc.communicate(timeout=timeout_s)
        return {"exit": proc.returncode, "timeout": False,
                "duration_s": round(time.time() - t0, 2),
                "stdout_tail": (out or "")[-2000:]}
    except subprocess.TimeoutExpired:
        if os.name == "nt":
            proc.kill()               # bat 包装层；java 子进程随 -batch 会话退出
        else:
            import signal as _signal
            try:
                os.killpg(os.getpgid(proc.pid), _signal.SIGKILL)
            except Exception:  # noqa: BLE001
                proc.kill()
        try:
            out, _ = proc.communicate(timeout=30)
        except subprocess.TimeoutExpired:
            out = ""
        return {"exit": -9, "timeout": True,
                "duration_s": round(time.time() - t0, 2),
                "stdout_tail": (out or "")[-2000:]}


class StarCCMSolver:
    """Solver 接口实现（runners/solvers/__init__.py 契约）。

    case_dir 约定：macro.java（入口 macro）+ 可选 case.sim（初始文件）；
    execution_ok 以 stdout 的 "Server disconnected" / 正常退出码综合判断
    （STAR-CCM+ -batch 完成态特征），求解收敛判据由 grader 侧定义，
    本方法只回答「批处理会话是否正常走完」。
    """

    name = "starccm-19.02.009-batch"

    def run_case(self, case_dir: Path, timeout_s: float) -> dict[str, Any]:
        macro = case_dir / "macro.java"
        if not macro.is_file():
            return {"ok": False, "exit": 2, "stdout": "", "stderr":
                    "macro.java missing in case dir", "duration_s": 0.0,
                    "timeout": False, "last_time": None}
        sim_arg = None
        sim_path = case_dir / "case.sim"
        if sim_path.is_file():
            sim_arg = str(sim_path)
        r = run_starccm(case_dir, "macro.java", timeout_s, sim=sim_arg)
        return {"ok": r["exit"] == 0 and not r["timeout"], "exit": r["exit"],
                "stdout": r["stdout_tail"], "stderr": "",
                "duration_s": r["duration_s"], "timeout": r["timeout"],
                "last_time": _last_export_dir(case_dir)}

    def execution_ok(self, case_dir: Path) -> bool:
        log = case_dir / "macro.solver.log"
        if log.is_file():
            try:
                text = log.read_text(errors="replace")
            except OSError:
                return False
            # -batch 正常收尾特征：Server disconnected 且无 Fatal JVM 错误
            return ("Server disconnected" in text
                    and "Fatal" not in text[-4000:])
        return False


def _last_export_dir(case_dir: Path) -> str | None:
    """macro 导出目录探测（export_<n> 约定），非判分依据，仅审计信息。"""
    cands = sorted(
        (d for d in case_dir.iterdir()
         if d.is_dir() and re.fullmatch(r"export(?:_\d+)?", d.name)),
        key=lambda d: d.stat().st_mtime)
    return cands[-1].name if cands else None
