"""matlab.py — gtm_matlab 分支的执行后端（dev 终端实现）。

职责（与 solvers/openfoam.py 同构：求解器无关原则下，本模块只负责
「把模型代码跑起来」，判分仍在 adapter）：
  run_matlab(workdir, entry, timeout_s)
    在 workdir 下 `matlab -batch "<entry>"` 执行模型脚本（entry 不带 .m），
    墙钟超时硬杀（进程组），返回 {exit, timeout, duration_s, stdout_tail}。
  matlab_static_check(code)
    MATLAB 方言的轻量静态检查（adapters/README.md code_exec 的
    sandbox_escape_attempt 在 MATLAB 侧的对应物）：禁 shell 逃逸/网络类调用。
    语法错误不在此拦——由 -batch 执行的非零退出码归入 code_not_executable。

环境（2026-08-22 实测）：
  /Applications/MATLAB_R2026a.app/bin/matlab（R2026a Update 3，Sponsored
  License，Control System/Aerospace Toolbox 齐备）；batch 启动 ~28s/次。
  MATLAB_BIN 环境变量可覆写（内网层版本锁定时用），缺省按上述路径再退
  PATH 探测。matlabengine-for-python 不用——版本配对脆弱，-batch 子进程
  更稳且与沙箱「隔离子进程执行」语义一致。
"""

from __future__ import annotations

import os
import re
import shutil
import signal
import subprocess
import time
from pathlib import Path

_DEFAULT_MATLAB = "/Applications/MATLAB_R2026a.app/bin/matlab"


def matlab_binary() -> str:
    """MATLAB 可执行文件定位：MATLAB_BIN > 默认路径 > PATH。找不到抛错（fail-fast）。"""
    cand = os.environ.get("MATLAB_BIN") or _DEFAULT_MATLAB
    if Path(cand).exists():
        return cand
    which = shutil.which("matlab")
    if which:
        return which
    raise RuntimeError(
        f"未找到 MATLAB（尝试 {cand} 与 PATH）。设 MATLAB_BIN 指向 matlab 可执行文件。")


# MATLAB 侧逃逸面：shell 逃逸 / 进程 / 网络 / 文件系统越界写（模型代码只需算+写 cwd）
_MATLAB_BANNED_PATTERNS: tuple[tuple[str, str], ...] = (
    (r"(?<![\w.])system\s*\(", "system()"),
    (r"(?<![\w.])unix\s*\(", "unix()"),
    (r"(?<![\w.])dos\s*\(", "dos()"),
    (r"(?<![\w.])perl\s*\(", "perl()"),
    (r"(?<![\w.])web\s*\(", "web()"),
    (r"(?<![\w.])urlread\s*\(", "urlread()"),
    (r"(?<![\w.])websave\s*\(", "websave()"),
    (r"(?<![\w.])webread\s*\(", "webread()"),
    (r"(?<![\w.])ftp\s*\(", "ftp()"),
    (r"(?<![\w.])parpool\s*\(", "parpool()"),
    (r"^[^%\n]*![a-zA-Z]", "! shell escape"),   # 行首 ! 前缀 shell 逃逸（% 注释除外）
)


def _strip_matlab_comments(code: str) -> str:
    """剥 %-注释 + 字符串字面量内容（防注释/串内 API 名误报）。

    '…' 单引号串感知（'' 转义），串内容以空串替换（保留引号定界防左右拼接）；
    与判分纪律一致：正则级近似，求低误报而非完美词法——逃逸调用不会藏在
    串里（藏了也执行不了），剥串只影响检测面不影响安全性。
    """
    out_lines = []
    for line in code.splitlines():
        buf = []
        in_str = False
        i = 0
        while i < len(line):
            c = line[i]
            if in_str:
                if c == "'":
                    if i + 1 < len(line) and line[i + 1] == "'":   # '' 转义
                        i += 2; continue
                    in_str = False
                    buf.append("''")            # 闭引号（空串占位）
            else:
                if c == "%":
                    break                      # 注释起点，丢弃其后
                if c == "'":
                    in_str = True
                    buf.append("'")            # 开引号（空串占位）
                else:
                    buf.append(c)
            i += 1
        out_lines.append("".join(buf))
    return "\n".join(out_lines)


def matlab_static_check(code: str) -> list[str]:
    """返回违规列表（空=通过）。只做正则级检查（先剥注释防误报）——
    MATLAB 无 AST 可用，判分纪律与 python 侧一致：命中即
    sandbox_escape_attempt，单独告警。"""
    stripped = _strip_matlab_comments(code)
    violations: list[str] = []
    for pat, label in _MATLAB_BANNED_PATTERNS:
        if re.search(pat, stripped, re.M):
            violations.append(label)
    return violations


def run_matlab(workdir: str | Path, entry: str, timeout_s: float) -> dict:
    """matlab -batch 执行，超时杀进程组（MATLAB 启动器会派生子进程）。

    -batch 语义：非交互、无桌面、脚本报错时退出码非零、stdout/stderr 合流。
    cwd=workdir 使模型脚本相对读写（result.json 落在 workdir）。
    """
    binp = matlab_binary()
    t0 = time.time()
    try:
        p = subprocess.Popen(
            [binp, "-batch", entry], cwd=str(workdir),
            stdout=subprocess.PIPE, stderr=subprocess.STDOUT, text=True,
            start_new_session=True)          # 进程组杀（启动器→jvm 子进程）
        out, _ = p.communicate(timeout=timeout_s)
        return {"exit": p.returncode, "timeout": False,
                "duration_s": round(time.time() - t0, 2),
                "stdout_tail": (out or "")[-2000:]}
    except subprocess.TimeoutExpired:
        try:
            os.killpg(os.getpgid(p.pid), signal.SIGKILL)
        except Exception:  # noqa: BLE001 — 进程已退则无需杀
            pass
        p.communicate()
        return {"exit": -9, "timeout": True,
                "duration_s": round(time.time() - t0, 2), "stdout_tail": ""}
