"""calculix.py — ccx_fea 分支的执行后端（dev 终端实现）。

职责（与 solvers/matlab.py 同构：求解器无关原则下，本模块只负责
「把 ccx 跑起来 + 把 .dat 里的数读出来」，判分仍在 adapter）：
  ccx_binary()           ccx 可执行定位（CCX_BIN > /opt/homebrew/bin/ccx > PATH）
  run_ccx(workdir, job, timeout_s)
                         在 workdir 下 `ccx -i <job>` 执行（job 不带 .inp），
                         墙钟超时硬杀（进程组），返回 {exit, timeout, duration_s,
                         stdout_tail}。非零退出 = INP 错误/不收敛（simulation_failed）。
  parse_dat(dat_path, extract)
                         按任务 YAML grader.extract 规格抽值：
                           max_abs_udof {set, dof}: 位移块 (vx,vy,vz) for set X，
                               取 dof 列绝对值最大项（带符号）
                           sum_rf {set, dof}:       反力块 forces for set X，dof 列求和
                           eigen_freq {mode}:       *FREQUENCY 表 REAL PART (CYCLES/TIME)
                           buckle_factor {mode}:    *BUCKLE 表 BUCKLING FACTOR

环境（2026-08-24 实测）：/opt/homebrew/bin/ccx（brew calculix-ccx，2.23，
GPL-2.0）。单位约定 mm-N-MPa-tonne（密度 7.85e-9 tonne/mm³，频率即 Hz）。
烟测互证：悬臂梁 C3D20 静力尖端挠度 vs 解析 3.810→3.812（0.06%）、
模态弱轴/强轴 419.9/833.0 vs EB 417.7/835.4、屈曲 5425/21515 vs 欧拉
5397/21590——判分物理层可信。

解析纪律：.dat 块标题（"displacements (vx,vy,vz) for set X and time ..."）
为 ccx 固定格式；只按任务声明的 set 名取块，模型改集合名 = 取不到值
（missing_output，合法失败信号——遵守输出契约是任务的一部分）。
"""

from __future__ import annotations

import os
import re
import shutil
import signal
import subprocess
import time
from pathlib import Path
from typing import Any

_DEFAULT_CCX = "/opt/homebrew/bin/ccx"


def ccx_binary() -> str:
    cand = os.environ.get("CCX_BIN") or _DEFAULT_CCX
    if Path(cand).exists():
        return cand
    which = shutil.which("ccx")
    if which:
        return which
    raise RuntimeError(
        f"未找到 ccx（尝试 {cand} 与 PATH）。设 CCX_BIN 指向 ccx 可执行文件"
        "（brew install calculix-ccx）。")


def run_ccx(workdir: str | Path, job: str, timeout_s: float, *, capture_log: bool = False) -> dict:
    """ccx -i <job> 执行，超时杀进程组。stdout/stderr 合流尾部带回。"""
    binp = ccx_binary()
    t0 = time.time()
    try:
        p = subprocess.Popen(
            [binp, "-i", job], cwd=str(workdir),
            stdout=subprocess.PIPE, stderr=subprocess.STDOUT, text=True,
            start_new_session=True)
        out, _ = p.communicate(timeout=timeout_s)
        if capture_log:
            (Path(workdir) / f"{job}.solver.log").write_text(out or "", encoding="utf-8")
        return {"exit": p.returncode, "timeout": False,
                "duration_s": round(time.time() - t0, 2),
                "stdout_tail": (out or "")[-2000:]}
    except subprocess.TimeoutExpired:
        try:
            os.killpg(os.getpgid(p.pid), signal.SIGKILL)
        except Exception:  # noqa: BLE001 — 进程已退则无需杀
            pass
        out, _ = p.communicate()
        if capture_log:
            (Path(workdir) / f"{job}.solver.log").write_text(out or "", encoding="utf-8")
        return {"exit": -9, "timeout": True,
                "duration_s": round(time.time() - t0, 2), "stdout_tail": ""}


# ---------------------------------------------------------------- .dat 解析

_DISP_RE = re.compile(r"displacements \(vx,vy,vz\) for set (\S+) and time", re.I)
_RF_RE = re.compile(r"forces \(fx,fy,fz\) for set (\S+)", re.I)
_NUM_ROW = re.compile(r"^\s*(\d+)\s+" + r"\s+".join(
    r"([-+]?\d*\.?\d+(?:[EeDd][-+]?\d+)?)" for _ in range(3)) + r"\s*$")


def _rows_after(dat_lines: list[str], start: int) -> list[tuple[int, list[float]]]:
    """从 start+1 行起读数值行（node/value 表）；跳过前导空行，读到非数值行止。"""
    rows: list[tuple[int, list[float]]] = []
    seen_data = False
    for ln in dat_lines[start + 1:]:
        if not seen_data and not ln.strip():
            continue                     # 块标题后的空行
        m = _NUM_ROW.match(ln)
        if not m:
            break                        # 首个非空行即非数值行 = 空块；数据后 = 块尾
        seen_data = True
        rows.append((int(m.group(1)),
                     [float(m.group(i)) for i in range(2, 5)]))
    return rows


def parse_dat(dat_path: str | Path, extract: dict[str, dict[str, Any]]) -> dict:
    """按 extract 规格抽值；解析不到的键不出现（判分按 missing 处理）。"""
    text = Path(dat_path).read_text(encoding="utf-8", errors="replace")
    lines = text.splitlines()
    out: dict[str, float] = {}

    # 预扫位移/反力块的 (set 名 → 行号)（同 set 多 time 步取最后一块）
    disp_at: dict[str, int] = {}
    rf_at: dict[str, int] = {}
    for i, ln in enumerate(lines):
        m = _DISP_RE.search(ln)
        if m:
            disp_at[m.group(1).upper()] = i
            continue
        m = _RF_RE.search(ln)
        if m:
            rf_at[m.group(1).upper()] = i

    for key, spec in extract.items():
        typ = spec.get("type")
        try:
            if typ == "max_abs_udof":
                i = disp_at.get(str(spec["set"]).upper())
                if i is None:
                    continue
                dof = int(spec["dof"]) - 1
                rows = _rows_after(lines, i)
                if not rows:
                    continue
                best = max(rows, key=lambda r: abs(r[1][dof]))
                out[key] = best[1][dof]
            elif typ == "sum_rf":
                i = rf_at.get(str(spec["set"]).upper())
                if i is None:
                    continue
                dof = int(spec["dof"]) - 1
                rows = _rows_after(lines, i)
                if not rows:
                    continue
                out[key] = sum(r[1][dof] for r in rows)
            elif typ == "eigen_freq":
                mode = int(spec["mode"])
                # MODE NO  EIGENVALUE  REAL PART(RAD/TIME)  REAL PART(CYCLES/TIME) ...
                for i, ln in enumerate(lines):
                    if "MODE NO" in ln and "EIGENVALUE" in ln:
                        for l2 in lines[i + 3:]:
                            parts = l2.split()
                            if len(parts) >= 5 and parts[0].isdigit():
                                if int(parts[0]) == mode:
                                    out[key] = float(parts[3])  # cycles/time (Hz)
                            elif parts and not parts[0].isdigit():
                                break
                        break
            elif typ == "buckle_factor":
                mode = int(spec["mode"])
                # 表头跨两行：MODE NO BUCKLING / FACTOR（标题行字母间有空格，不匹配）
                for i, ln in enumerate(lines):
                    if "MODE NO" in ln and "BUCKLING" in ln:
                        for l2 in lines[i + 2:]:
                            parts = l2.split()
                            if len(parts) >= 2 and parts[0].isdigit():
                                if int(parts[0]) == mode:
                                    out[key] = float(parts[1])
                            elif parts and not parts[0].isdigit():
                                break
                        break
            else:
                raise ValueError(f"未知 extract 类型: {typ}")
        except (KeyError, ValueError, IndexError):
            continue
    return out
