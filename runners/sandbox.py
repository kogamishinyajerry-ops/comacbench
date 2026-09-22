"""sandbox.py — code_exec 的执行沙箱（dev 终端实现，无容器）。

设计边界（如实声明，写入 M2 报告）：
- dev 终端无容器运行时；本沙箱 = **静态检查（AST）+ 隔离子进程执行**：
  * `python -E -s`（忽略环境变量 PYTHONPATH 等 + 禁 user-site）。
    2026-08-20：原为 `-I`——Python 3.11+ 起 `-I` 隐含 `-P`（脚本目录不进
    sys.path），vendored gold 的 `import turbojet_engine`（同目录伴随模块）
    随新 venv（3.12）失败；`-E -s` 恢复 ≤3.10 时代 `-I` 的实际语义，
    隔离强度声明不变（仍无环境变量/无 user-site/独立 cwd/墙钟超时）；
  * 独立临时工作目录（读写仅限该目录），墙钟超时硬杀；
  * 静态检查禁止 网络/子进程/系统调用 类导入与调用，命中即
    `sandbox_escape_attempt`（score=0 并单独告警，adapters/README.md code_exec 失败模式）。
- macOS 无 RLIMIT_AS；内存限额不可强制 => 以墙钟超时兜底，报告中如实标注
  「dev 层沙箱强度 = 静态审查 + 隔离解释器 + 超时，非 OS 级强制隔离」；
  intranet 层移植时应替换为容器执行（env-matrix.md §2 python_sandbox）。
- `open()` 不禁：任务契约要求模型代码写 .npy 产物（写限在其临时工作目录）。
"""

from __future__ import annotations

import ast
import atexit
import shutil
import subprocess
import sys
import tempfile
import time
from pathlib import Path
from typing import Any

# 活着的隔离子工作目录。`IsolatedRun` 此前既不支持显式关闭、也没有任何回收，
# 每次运行都在系统临时目录留下一个 bm_sandbox_* 目录（实测曾积压 759 个）。
# 现在：① `close()` / 上下文管理器做主动回收；② `cleanup_all()` 供各 adapter
# CLI 在退出前一次性收尾；③ `atexit` 兜底，崩溃路径也不会留残余。
_LIVE_DIRS: set[Path] = set()

# 静态黑名单：导入即违规（网络/进程/系统侵入）
BANNED_IMPORTS = {
    "socket", "socketserver", "ssl", "asyncio",  # asyncio: 主要为网络用途，禁
    "subprocess", "multiprocessing", "concurrent",  # 进程逃逸
    "urllib", "requests", "http", "http.client", "ftplib", "telnetlib",
    "smtplib", "webbrowser", "xmlrpc", "ctypes", "cffi",
    "importlib",  # 动态导入绕过静态检查
    "shutil",  # 文件系统批量操作（模型代码无需）
}
# importlib.metadata 等科学栈不会用；保留 os/sys/math 等基础（gold 代码用到 os.path）

# 属性调用黑名单（进程逃逸/权限提升）。os.chmod 属良性文件操作，2026-08-19 已移除——
# 曾误伤 foam_basic 33 例（M4 判分器缺陷，已修）。
BANNED_CALL_SUBSTRINGS = (
    "os.system", "os.popen", "os.exec", "os.fork", "os.spawn",
    "os.kill", "os.setuid", "os.chown",
)


def static_check(code: str, allow_shutil: bool = False) -> tuple[list[str], bool]:
    """AST 静态检查 -> (violations, syntax_ok)。violations 非空 => sandbox_escape_attempt。

    allow_shutil：表格加工类任务（SSB 型「复制 init 工作簿再改」是标准做法，
    openpyxl 加载-改-存会丢数据验证等格式）声明 allowed_tools 含
    filesystem-copy 时放行 shutil——默认 False 沿用既有纪律（shutil 本属
    「模型代码无需」假设，对该任务族不成立，2026-08-26 SSB 实测修正）。"""
    violations: list[str] = []
    try:
        tree = ast.parse(code)
    except SyntaxError as e:
        return [], False
    banned = set(BANNED_IMPORTS)
    if allow_shutil:
        banned.discard("shutil")
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            for alias in node.names:
                root = alias.name.split(".")[0]
                if alias.name in banned or root in banned:
                    violations.append(f"banned_import:{alias.name}")
        elif isinstance(node, ast.ImportFrom):
            root = (node.module or "").split(".")[0]
            if node.module in banned or root in banned:
                violations.append(f"banned_import_from:{node.module}")
        elif isinstance(node, ast.Call):
            func = node.func
            parts: list[str] = []
            while isinstance(func, ast.Attribute):
                parts.append(func.attr)
                func = func.value
            if isinstance(func, ast.Name):
                parts.append(func.id)
            call = ".".join(reversed(parts))
            for pat in BANNED_CALL_SUBSTRINGS:
                if pat.rstrip("(") in call:
                    violations.append(f"banned_call:{call}")
                    break
    return sorted(set(violations)), True


class IsolatedRun:
    """一次性隔离子进程工作目录。

    用完必须回收：`with IsolatedRun() as iso:` 或显式 `iso.close()`。
    未回收的目录由 `cleanup_all()` / `atexit` 兜底清除。
    """

    def __init__(self) -> None:
        self.dir = Path(tempfile.mkdtemp(prefix="bm_sandbox_"))
        _LIVE_DIRS.add(self.dir)

    def close(self) -> None:
        """回收本工作目录（幂等）。"""
        if self.dir in _LIVE_DIRS:
            _LIVE_DIRS.discard(self.dir)
        shutil.rmtree(self.dir, ignore_errors=True)

    def __enter__(self) -> "IsolatedRun":
        return self

    def __exit__(self, *exc) -> bool:
        self.close()
        return False

    def write(self, name: str, content: str) -> Path:
        p = self.dir / name
        p.write_text(content, encoding="utf-8")
        return p

    def run(self, script: Path, timeout_s: float) -> dict[str, Any]:
        t0 = time.time()
        try:
            r = subprocess.run(
                [sys.executable, "-E", "-s", str(script)],
                cwd=self.dir, capture_output=True, text=True, timeout=timeout_s,
                env={"PATH": "/usr/bin:/bin", "HOME": str(self.dir),
                     "MPLCONFIGDIR": str(self.dir)},
            )
            return {"exit": r.returncode, "stdout": r.stdout[-20000:],
                    "stderr": r.stderr[-20000:], "duration_s": round(time.time() - t0, 2),
                    "timeout": False}
        except subprocess.TimeoutExpired as e:
            return {"exit": -1, "stdout": (e.stdout or b"")[-20000:] if isinstance(e.stdout, bytes) else (e.stdout or "")[-20000:],
                    "stderr": f"[sandbox timeout after {timeout_s}s]",
                    "duration_s": round(time.time() - t0, 2), "timeout": True}


def live_sandboxes() -> list[Path]:
    """尚未回收的隔离子工作目录（诊断用）。"""
    return sorted(_LIVE_DIRS)


def cleanup_all() -> int:
    """回收全部未关闭的隔离子工作目录；返回实际移除的数量（幂等）。"""
    pending = sorted(_LIVE_DIRS)
    _LIVE_DIRS.clear()
    removed = 0
    for directory in pending:
        if directory.is_dir():
            shutil.rmtree(directory, ignore_errors=True)
            removed += 1
    return removed


atexit.register(cleanup_all)
