#!/usr/bin/env python
"""构建 COMACBench 内网离线交付包（Windows x64 / 无外网 / 中文 Windows）。

    python tools/build_offline_package.py --out D:/comacbench-offline
    python tools/build_offline_package.py --out ... --skip-wheelhouse

设计要点
--------
* **payload 用 `git archive <commit>` 导出**，不是复制工作区——天然排除未跟踪文件、
  `.git`、`__pycache__`、sparse-checkout 残留。
* **必须禁用 LFS 过滤器**：本仓 26925 个受 LFS 跟踪的路径在本地与远端都取不到实体
  （本地 `.git/lfs/objects` 无对象，远端 404），`git archive` 默认会因 smudge 失败
  而中止（exit 128）。禁用过滤器后这些路径会以 130 B 指针形式出现，再由裁剪规则
  整体排除，并把清单写进 `03_LFS_UNAVAILABLE.md`——不静默省略。
* **裁剪规则**只删两类：交付方用不到的历史产物（`results/`、`reports/`、
  `.pnpm-store/`、`report/` 中除被测试引用的那一个子树以外的部分），以及取不到实体的
  LFS 路径。其余一律原样交付。
* 构建脚本本身入库，使 v1.1 / v2 可用同一条命令复现。
"""
from __future__ import annotations

import argparse
import hashlib
import json
import os
import posixpath
import shutil
import subprocess
import sys
import tarfile
import zipfile
from pathlib import Path

REPO = Path(__file__).resolve().parents[1]

# 整棵排除的顶层目录：交付方用不到的历史/缓存产物（tests/ 不引用它们）
PRUNE_TOP = ("results", "reports", ".pnpm-store")
# report/ 只保留这一个子树——tests/test_structural_contract.py:42 引用了它
REPORT_KEEP = "report/2026-09-06-aviation-plugin-v1"

# 脚本一律纯 ASCII（cmd.exe 代码页 936 下非 ASCII 会被当命令名）。
# 统一先 chcp 65001 + PYTHONUTF8=1：中文 Windows 上 Python 默认按 cp936 解码文本，
# 而本仓的数据是 UTF-8，不强制会报 'gbk' codec can't decode。
BAT_VERIFY = """@echo off
REM COMACBench offline package - integrity check (ASCII only, CRLF, no BOM)
setlocal
chcp 65001 >nul
set PYTHONUTF8=1
where powershell >nul 2>nul
if errorlevel 1 goto NOPWSH
powershell -NoProfile -ExecutionPolicy Bypass -File "%~dp0verify.ps1"
set RC=%ERRORLEVEL%
echo.
echo RESULT: %RC%
pause
exit /b %RC%
:NOPWSH
echo [FAIL] powershell.exe not found. Use verify.ps1 directly.
pause
exit /b 1
"""

BAT_INSTALL = """@echo off
REM COMACBench offline package - install and acceptance (ASCII only, CRLF, no BOM)
setlocal
chcp 65001 >nul
set PYTHONUTF8=1
set PYTHONIOENCODING=utf-8
where powershell >nul 2>nul
if errorlevel 1 goto NOPWSH
powershell -NoProfile -ExecutionPolicy Bypass -File "%~dp0install.ps1"
set RC=%ERRORLEVEL%
echo.
echo RESULT: %RC%
pause
exit /b %RC%
:NOPWSH
echo [FAIL] powershell.exe not found. Use install.ps1 directly.
pause
exit /b 1
"""

# 日常使用入口：必须在 payload/ 里跑，否则 runners/ 不在 sys.path 上。
BAT_RUN = """@echo off
REM COMACBench offline package - run the CLI from the payload root (ASCII only, CRLF)
REM Usage: run-comacbench.bat validate packs/aviation-workload-starter-v1
setlocal
chcp 65001 >nul
set PYTHONUTF8=1
set PYTHONIOENCODING=utf-8
set "PKG=%~dp0"
set "PY=%PKG%.venv\\Scripts\\python.exe"
if not exist "%PY%" goto NOVENV
cd /d "%PKG%payload"
"%PY%" -m comacbench %*
set RC=%ERRORLEVEL%
exit /b %RC%
:NOVENV
echo [FAIL] venv not found. Run install.bat first.
exit /b 1
"""

VERIFY_PS1 = r"""# COMACBench offline package - integrity check.
# ASCII only. Verifies SHA256SUMS.txt; that proves transport integrity ONLY.
$ErrorActionPreference = 'Stop'
$root = Split-Path -Parent $MyInvocation.MyCommand.Path
Set-Location $root
$fail = 0
$checked = 0

Write-Host '== COMACBench offline package: integrity check =='
Write-Host ("package root : " + $root)

if (-not (Test-Path 'SHA256SUMS.txt')) {
    Write-Host '[FAIL] SHA256SUMS.txt not found'
    exit 1
}

foreach ($line in (Get-Content 'SHA256SUMS.txt' -Encoding UTF8)) {
    if ([string]::IsNullOrWhiteSpace($line)) { continue }
    $parts = $line -split '  ', 2
    if ($parts.Count -ne 2) { continue }
    $want = $parts[0].Trim()
    $rel  = $parts[1].Trim()
    $path = Join-Path $root $rel
    if (-not (Test-Path -LiteralPath $path)) {
        Write-Host ("[FAIL] missing : " + $rel)
        $fail++
        continue
    }
    $got = (Get-FileHash -LiteralPath $path -Algorithm SHA256).Hash.ToLower()
    if ($got -ne $want.ToLower()) {
        Write-Host ("[FAIL] digest  : " + $rel)
        $fail++
    } else {
        $checked++
    }
}

Write-Host ("files verified : " + $checked)
if ($fail -eq 0) {
    Write-Host 'RESULT: ALL CHECKS PASSED'
    Write-Host 'NOTE: integrity only - this does NOT prove the package content is correct.'
    exit 0
}
Write-Host ("RESULT: FAILED (" + $fail + " file(s))")
exit 1
"""

INSTALL_PS1 = r"""# COMACBench offline package - install into a package-local venv and run acceptance.
# ASCII only. Never touches the system Python; always uses --no-index.
$ErrorActionPreference = 'Continue'
$root = Split-Path -Parent $MyInvocation.MyCommand.Path
Set-Location $root
$fail = 0

function Check($name, $ok, $detail) {
    if ($ok) { Write-Host ("[ OK ] " + $name + " : " + $detail) }
    else     { Write-Host ("[FAIL] " + $name + " : " + $detail); $script:fail++ }
}

Write-Host '== COMACBench offline package: install + acceptance =='
Write-Host ("package root : " + $root)

# Force UTF-8 for every interpreter this script starts. On Chinese Windows Python
# otherwise decodes text as cp936 while the repository data is UTF-8, which fails
# with "'gbk' codec can't decode byte ...". Set before any python invocation.
$env:PYTHONUTF8 = '1'
$env:PYTHONIOENCODING = 'utf-8'

# ---- 1. interpreter: must be CPython 3.11 x64 (wheels are cp311 win_amd64) ----
# Resolve to an explicit python.exe path first, then always call that path.
# Never slice an args array by count - "$a[1..($a.Count-1)]" degenerates to
# "1..0" (i.e. indexes 1,0) when the array has a single element.
$pyExe = $null
$seen = 'none'
foreach ($cand in @('py', 'python', 'python3')) {
    if (-not (Get-Command $cand -ErrorAction SilentlyContinue)) { continue }
    $probe = @()
    if ($cand -eq 'py') { $probe = @('-3.11') }
    $ver = & $cand @probe -c "import sys,platform;print('%d.%d|%s' % (sys.version_info[0], sys.version_info[1], platform.architecture()[0]))" 2>$null
    if ($LASTEXITCODE -ne 0 -or -not $ver) { continue }
    $seen = $ver
    $bits = "$ver".Split('|')
    if ($bits[0] -eq '3.11' -and $bits[1] -eq '64bit') {
        $resolved = & $cand @probe -c "import sys;print(sys.executable)" 2>$null
        $pyExe = "$resolved".Trim()
        break
    }
}
if (-not $pyExe) {
    Write-Host ("[FAIL] python : need CPython 3.11 64-bit; found " + $seen)
    Write-Host '       install CPython 3.11 x64, or run this via the "py -3.11" launcher'
    Write-Host 'RESULT: FAILED (interpreter)'
    exit 1
}
Check 'python' $true ("3.11 x64 -> " + $pyExe)

# ---- 2. layout ----
Check 'payload' (Test-Path 'payload/pyproject.toml') 'payload/pyproject.toml'
Check 'wheelhouse' (Test-Path 'wheelhouse') 'wheelhouse/'
Check 'lock file' (Test-Path 'wheelhouse/requirements-lock.txt') 'requirements-lock.txt'

# ---- 3. venv inside the package (never the system python) ----
$venv = Join-Path $root '.venv'
$vpy = Join-Path $venv 'Scripts\python.exe'
if (-not (Test-Path $vpy)) {
    Write-Host '       creating venv ...'
    & $pyExe -m venv $venv
}
Check 'venv' (Test-Path $vpy) $vpy
if (-not (Test-Path $vpy)) {
    Write-Host 'RESULT: FAILED (venv)'
    exit 1
}

# ---- 4. offline dependency install (--no-index guarantees no network) ----
$log = Join-Path $root 'install-deps.log'
if (Test-Path $log) { Remove-Item $log -Force }
Write-Host '       pip install --no-index (wheelhouse) ...'
& $vpy -m pip install --no-index --find-links wheelhouse --upgrade pip *>> $log
$rcPip = $LASTEXITCODE
& $vpy -m pip install --no-index --find-links wheelhouse -r wheelhouse/requirements-lock.txt *>> $log
$rcDeps = $LASTEXITCODE
if ($rcPip -ne 0 -or $rcDeps -ne 0) {
    Write-Host '[FAIL] deps : see install-deps.log'
    Get-Content $log -Tail 25
    Write-Host 'RESULT: FAILED (deps)'
    exit 1
}
Check 'deps' $true 'installed from wheelhouse'

# ---- 5. install comacbench itself from the payload snapshot ----
# Install the build backend first: a venv ships setuptools on 3.11, but 3.12+
# dropped it from ensurepip, and the payload is a source tree that needs one.
& $vpy -m pip install --no-index --find-links wheelhouse setuptools wheel *>> $log
if ($LASTEXITCODE -ne 0) {
    Write-Host '[FAIL] build backend : see install-deps.log'
    Get-Content $log -Tail 25
    Write-Host 'RESULT: FAILED (build backend)'
    exit 1
}
Write-Host '       pip install --no-index ./payload (comacbench) ...'
# Must be './payload': a bare 'payload' is read by pip as a package NAME to
# resolve from the index ("No matching distribution found for payload"),
# never as a local path.
& $vpy -m pip install --no-index --no-build-isolation --find-links wheelhouse './payload' *>> $log
if ($LASTEXITCODE -ne 0) {
    Write-Host '[FAIL] package : see install-deps.log'
    Get-Content $log -Tail 25
    Write-Host 'RESULT: FAILED (package)'
    exit 1
}
Check 'package' $true 'comacbench installed from payload'

# ---- 6. acceptance: real entry points, real pack ----
$acc = Join-Path $root 'acceptance'
if (Test-Path $acc) { Remove-Item $acc -Recurse -Force }
New-Item -ItemType Directory -Force -Path $acc | Out-Null
$packDir = Join-Path $root 'payload'
$pack = 'packs/aviation-workload-starter-v1'

# The CLI must run with the payload root on sys.path: `runners/` is a repo-root
# package that is NOT part of the installed `comacbench` distribution, so running
# from an arbitrary directory fails with "No module named 'runners'".
Push-Location $packDir
Write-Host '       acceptance 1/2: comacbench validate ...'
& $vpy -m comacbench validate $pack --out (Join-Path $acc 'validate') *> (Join-Path $acc 'validate.log')
$rcVal = $LASTEXITCODE
$vlog = Get-Content (Join-Path $acc 'validate.log') -Raw -Encoding UTF8
Check 'validate' ($rcVal -eq 0) ("exit=" + $rcVal + " runnable=" + ($vlog -match '"runnable":\s*true'))

Write-Host '       acceptance 2/2: release chain (pytest) ...'
# Offline package cannot ship Chromium (~200 MB, and browser binaries cannot be
# installed without network). The chain therefore runs with an explicitly declared
# lower report-render requirement. This is NOT a skip: the chain still requires
# probes/test_report_full.py to exit 0 and its static TDZ layer to PASS. The
# downgrade is recorded here, in MANIFEST.json and in 02_EVIDENCE.md.
$env:COMAC_REPORT_RENDER = 'static'
& $vpy -m pytest -q --no-header -p no:cacheprovider (Join-Path $packDir 'tests/test_release_chain.py') *> (Join-Path $acc 'release-chain.log')
$rcChain = $LASTEXITCODE
Check 'release chain' ($rcChain -eq 0) ("exit=" + $rcChain + " ten-phase end-to-end")
Pop-Location
Write-Host '[WARN] report render layer : static'
Write-Host '       browser layer (Playwright + Chromium) is NOT bundled with this offline'
Write-Host '       package; the release chain ran with COMAC_REPORT_RENDER=static.'
Write-Host '       The static TDZ layer still passed. See 02_EVIDENCE.md.'

Write-Host ''
if ($fail -eq 0) {
    Write-Host 'RESULT: ALL CHECKS PASSED'
    Write-Host ('venv    : ' + $vpy)
    Write-Host ('logs    : ' + $acc)
    Write-Host 'NOTE: acceptance ran validate + the release chain on the aviation pack only.'
    Write-Host 'NOTE: CFD suites cannot run - their LFS data is not part of this package.'
    exit 0
}
Write-Host ("RESULT: FAILED (" + $fail + " check(s))")
exit 1
"""

READ_ME = """# 01 · 先读我（COMACBench 内网离线交付包）

> 这是一个**离线资产包**：拷进内网、双击就能装、装完自证。目标机器**不需要外网**。

## 三步流程

| 步 | 做什么 | 命令 |
|---|---|---|
| 1 | 拷进内网并解压 | 用 **7-Zip** 或 `Expand-Archive` 解压到**纯英文路径**（如 `D:\\COMACBench`），**不要**放在含中文或空格的目录 |
| 2 | 校验完整性 | 双击 `verify.bat`（或 `powershell -ExecutionPolicy Bypass -File verify.ps1`） |
| 3 | 安装并验收 | 双击 `install.bat`（或 `powershell -ExecutionPolicy Bypass -File install.ps1`） |

只看最后一行：`RESULT: ALL CHECKS PASSED` 即通过；否则按下面的排错表处理。

## 环境要求

| 项 | 要求 | 说明 |
|---|---|---|
| 操作系统 | Windows x64 | wheel 为 `cp311 / win_amd64` |
| Python | **CPython 3.11 x64** | 版本或位数不符会在第 1 项检查就明确报错，不会莫名失败 |
| 网络 | **不需要** | 安装走 `pip --no-index`，只用包内 `wheelhouse/` |
| 磁盘 | 约 2 GB 可用 | payload + wheelhouse + 包内 venv |
| 权限 | 普通用户即可 | venv 建在**包目录内**，不碰系统 Python |

### 必须设置的两个环境变量（重要）

```
PYTHONUTF8=1
PYTHONIOENCODING=utf-8
```

中文 Windows 上 Python 默认按 **cp936** 解码文本，而本仓的数据是 **UTF-8**。不设置会报：

```
UnicodeDecodeError: 'gbk' codec can't decode byte 0x80 in position ...
```

`install.bat` / `run-comacbench.bat` 已自动设置这两个变量（并 `chcp 65001`）。
**如果你是手工敲 `python -m comacbench ...`，请自己带上**：

```bat
set PYTHONUTF8=1
set PYTHONIOENCODING=utf-8
```

### 必须在 payload 根目录运行（重要）

`runners/` 是仓库根目录下的独立包，**不在** `comacbench` 这个 pip 发行版里。
所以 `comacbench validate` 必须让 **payload 根目录**在 `sys.path` 上，否则会报
`ModuleNotFoundError: No module named 'runners'`。

`run-comacbench.bat` 已经替你做了 `cd payload`。手工运行时：

```bat
cd <包目录>\\payload
<包目录>\\.venv\\Scripts\\python.exe -m comacbench validate packs/aviation-workload-starter-v1
```

## 日常使用

```bat
REM 预检任意题包
run-comacbench.bat validate packs\\aviation-workload-starter-v1

REM 校准（参考实现 + 错误负例自检）
run-comacbench.bat calibrate packs\\aviation-workload-starter-v1 --out D:\\calib

REM 跑发行级链路
cd payload
..\\.venv\\Scripts\\python.exe -m pytest -q tests/test_release_chain.py
```

## 目录结构

实际交付载体是**单个 zip**，解压后得到下面这棵树：

```
COMACBench-assets-v<版本>.zip          <- 交付这个文件（附 .sha256 旁文件）
└── COMACBench-assets-v<版本>/
    ├── 01_READ_ME_FIRST.md     本文件
    ├── 02_EVIDENCE.md          证据分级与边界（**必须看"不证明什么"那一节**）
    ├── 03_LFS_UNAVAILABLE.md   未随包交付的 LFS 路径清单与原因
    ├── MANIFEST.json           commit / content_tree / 内容清单 / 验收基线
    ├── SHA256SUMS.txt          全包校验（不含自身）
    ├── verify.ps1 / verify.bat
    ├── install.ps1 / install.bat
    ├── run-comacbench.bat      日常入口（自动设 UTF-8 并在 payload 根目录运行）
    ├── payload/                源码快照（git archive 导出后按规则裁剪）
    ├── git/comacbench.bundle   完整历史（可离线 clone / diff 审计）
    └── wheelhouse/             *.whl + requirements-lock.txt
```

zip 的 SHA-256 记录在同级 `COMACBench-assets-v<版本>.zip.sha256`（`sha256sum -c` 格式）。

## 解压注意事项

| 方式 | 结论 |
|---|---|
| **7-Zip**（首选） | 推荐。右键 → 解压到 `D:\COMACBench`。 |
| `Expand-Archive`（PowerShell 5.1） | **不推荐**：实测在本包上只解出 9437/11381 个文件就失败退出（该 cmdlet 对万级条目/大文件有已知限制），且不报错到底。 |
| Python `zipfile`（保底） | 若上面两者都不行：`python -c "import zipfile;zipfile.ZipFile(r'路径\\包.zip').extractall(r'D:\\')"` |

- 解压到**纯 ASCII 路径**，例如 `D:\COMACBench`。含中文或空格的路径会让部分工具链出问题。
- 包内条目名**全部为 ASCII**，因此不存在 zip 中文名编码问题。
- 解压后**先跑 `verify.bat`**，再做别的。注意 **`verify` 会逐文件算 SHA-256，实测约 3 分钟**（含 223 MB 的 git bundle），属正常。

## 排错表

| 现象 | 原因 | 处理 |
|---|---|---|
| `verify.bat` 窗口一闪而过 | 脚本被当命令执行失败 | 改用 `powershell -NoProfile -ExecutionPolicy Bypass -File verify.ps1` |
| `无法加载文件 ... 未对文件进行数字签名` | 执行策略限制 | 在命令里加 `-ExecutionPolicy Bypass`（脚本已通过 .bat 自动加） |
| `[FAIL] python : need CPython 3.11 64-bit` | 装的是 3.12 / 32 位 / 只装了 Microsoft Store 版 | 装官方 CPython 3.11 x64，或用 `py -3.11` 启动器 |
| `UnicodeDecodeError: 'gbk' codec can't decode byte ...` | 没设 UTF-8 环境变量 | 设 `PYTHONUTF8=1` + `PYTHONIOENCODING=utf-8`，并用 `run-comacbench.bat` |
| `ModuleNotFoundError: No module named 'runners'` | 不在 payload 根目录运行 | `cd payload` 后再跑；或直接用 `run-comacbench.bat` |
| `pip install` 报找不到包 | 试图联网 / wheelhouse 不完整 | 确认命令里有 `--no-index --find-links wheelhouse`；重新 `verify.bat` 核对 wheelhouse |
| 解压后中文文件名乱码 | 用旧版解压工具 | 用 **7-Zip**，或 `Expand-Archive`（会自动按 UTF-8 标记位解码） |
| `UnicodeDecodeError: 'gbk' codec` | requirements 文件被改成了非 ASCII | 不要编辑 `wheelhouse/requirements-lock.txt`，保持纯 ASCII |
| `validate` 通过但 CFD 相关测试失败 | **预期行为** | 这批任务的 LFS 数据未随包交付，见 `03_LFS_UNAVAILABLE.md` |

## 边界提醒（重要）

- 校验通过 **≠** 内容正确 **≠** 可投产。三层是分开的，见 `02_EVIDENCE.md`。
- 本包**不含**任何需要 LFS 的二进制数据实体（内网与上游都取不到），CFD 相关算例无法运行。
- 本包**不含** `results/`、`reports/`、`.pnpm-store/` 等历史产物，也不含 `report/` 中除
  被测试引用的那一个子树以外的部分。
"""

EVIDENCE = """# 02 · 证据分级与边界

> 交付诚信的核心是**说清证明了什么、以及没证明什么**。下面每一项都单列。

## 三层证据（各自独立，不可互相替代）

| 层 | 手段 | 依赖 | 证明什么 | **不证明什么** |
|---|---|---|---|---|
| 完整性 | `SHA256SUMS.txt` + `verify.ps1` | 只要有 PowerShell | 包在传输/拷贝过程中**未被改动** | 不证明内容正确、不证明能装、不证明能跑 |
| 可安装性 | `wheelhouse/*.whl` + `pip --no-index` | 只要有 Python 3.11 x64 | 无外网也能把依赖**装齐** | 不证明装出来的东西行为正确 |
| 行为正确性 | 装完后跑真实入口（`comacbench validate` + 发行级链路） | Python + 装好的依赖 | 交付的快照在目标机上**真的能跑**，且题包预检通过 | 不证明 CFD 算例可跑（数据未随包）、不证明判分口径与工程真值一致 |

**只做第 1 层是最常见的假交付**：哈希全对而内容跑不起来。本包的 `install.ps1` 强制跑到第 3 层。

## 本包交付内容的实测数字

| 项 | 值 | 来源 |
|---|---|---|
| 源提交 | 见 `MANIFEST.json` 的 `commit` | `git rev-parse HEAD` |
| 源内容树 | 见 `MANIFEST.json` 的 `content_tree` | `git rev-parse HEAD^{tree}` |
| 上游仓库文件总数 | 51621 | `git ls-tree -r HEAD` |
| 本包 payload 文件数 | 见 `MANIFEST.json` 的 `payload_files` | 构建时实测 |
| 未随包交付的 LFS 路径 | 26925 | `git lfs ls-files`，见 `03_LFS_UNAVAILABLE.md` |
| 装机验收基线 | `comacbench validate` → `runnable = true`；发行级十环链路 → pass | `install.ps1` 输出 |

## 打包过程中发现并修复的上游缺陷（交付方须知）

把包真正装到"另一个位置"跑，暴露了两类只在目标环境才现形的问题。两者都已在源提交里修掉：

| # | 缺陷 | 触发条件 | 修复 |
|---|---|---|---|
| 1 | `comacbench/pack.py` 无条件 `from runners.solvers.backward_step import ...` | `comacbench` 被 pip 装进 site-packages 后，`runners/` 不在包内 → 任何题的预检都 `ModuleNotFoundError` | 改为只在 `exec_kind == 'cfd_step'` 时导入；导入失败发**具名 blocker** `cfd_runner_unavailable`，不再让整个预检崩掉 |
| 2 | `comacbench/__main__.py` 等处 `Path.read_text()` 未指定编码 | 中文 Windows 上 Python 按 cp936 解码，而数据是 UTF-8 → `'gbk' codec can't decode byte 0x80`；实测 `calibrate` 直接失败 | `comacbench/` 全部站点 + 验收路径上的 `runners/` 站点补 `encoding="utf-8"`；`install.bat` / `run-comacbench.bat` 强制 `PYTHONUTF8=1` |
| 3 | `runners/design_artifact.py` 用了多行 f-string | 该语法需 Python 3.12+（PEP 701），而 `pyproject.toml` 声明 `requires-python >=3.10` → 在 3.11 上整个模块 `SyntaxError`，无法导入 | 改写为等价的单行 f-string；`python 3.11` 全仓扫描 1430 个 `.py`，语法不兼容文件数 **0** |

**仍存在的同类风险（未修，已记录）**：`runners/gen_tasks_*.py`（离线任务生成器，不在运行/验收路径上）
还有约 30 处未显式指定编码的文本 I/O。它们在本包的验收流程中不会被触发，
但如果内网要用这些生成器，请同样带上 `PYTHONUTF8=1`。

## 明确"不证明什么"（逐条）

1. **不证明 LFS 数据存在。** 上游仓库 26925 个受 LFS 跟踪的路径，其**实体内容在本地
   （`.git/lfs/objects` 为空）与远端（HTTP 404）** 都取不到。本包不含这些内容，
   也不含它们的 130 字节指针。**依赖这批数据的 CFD 相关算例与测试无法运行，这是
  数据可得性问题，不是本包缺陷。**
2. **不证明判分口径正确。** `comacbench validate` 是静态检查；题包另有 review 级条目
   `expert_review_required`（本版本对**任何**题包都无条件发出），工程专家审查**未做**。
3. **不证明全测试套件通过。** 装机验收只跑 `validate` 与航空工作包的发行级链路。
   完整 `pytest tests/` 在源环境下的实测结果是 `5 failed, 256 passed, 17 skipped`，
   其中 5 项失败全部是 `OSError: [WinError 1314]`（Windows 符号链接特权缺口），
   与本次交付内容无关；本包未在内网复现该套件。
4. **不证明报告能被真实浏览器渲染。** 本包**不含** Playwright 与 Chromium
   （浏览器二进制无法离线安装，且约 200 MB 与 benchmark 使用无关）。
   发行级链路的报告渲染层以 `COMAC_REPORT_RENDER=static` 运行：
   要求 `probes/test_report_full.py` 整体退出 0 且**静态层 TDZ PASS**，
   浏览器层为 `NOT_RUN`。**这是已声明的降级，不是跳过**——降级事实同时记录在本文件、
   `MANIFEST.json` 的 `acceptance_baseline.report_render_layer` 与 `install.ps1` 输出中。
   若内网有 Chromium，设 `COMAC_REPORT_RENDER=browser` 可要求完整浏览器层。
5. **不证明 `publishable`。** 该字段在本版本 `comacbench/pack.py` 中是**硬编码 `False`**，
   不参与计算（`plugin/dsh-comac-benchmark/test-packs.mjs` 亦将其断言锁死）。
   本版本的实际发布门是 `runnable`（blocker 数为 0）。
6. **不证明二进制与源码严格同源。** payload 由 `git archive <commit>` 导出并在导出后
   做了**规则化裁剪**（见 `01_READ_ME_FIRST.md` 末节与 `MANIFEST.json` 的 `prune_rules`）。
   裁剪规则与结果文件清单都在包里，可自行复核。

## 复现本包

```bash
# 在源仓库
python tools/build_offline_package.py --out <输出目录>
```

同一条命令可从同一 commit 重建出等价包（`wheelhouse` 内容取决于构建时的 PyPI 状态，
故 `MANIFEST.json` 同时记录每个 wheel 的文件名与摘要）。
"""


def run(args, **kw):
    return subprocess.run(args, cwd=REPO, capture_output=True, text=True, **kw)


def git(*args):
    r = run(["git", *args])
    if r.returncode != 0:
        raise SystemExit(f"git {' '.join(args)} 失败: {r.stderr.strip()}")
    return r.stdout


def sha256_file(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as fh:
        for chunk in iter(lambda: fh.read(1 << 20), b""):
            h.update(chunk)
    return h.hexdigest()


def lfs_paths() -> set:
    r = run(["git", "lfs", "ls-files"])
    if r.returncode != 0:
        raise SystemExit("git lfs ls-files 失败；无法确定 LFS 路径集")
    out = set()
    for line in r.stdout.splitlines():
        parts = line.split(None, 2)
        if len(parts) == 3:
            out.add(parts[2])
    return out


def dependency_closure(roots) -> dict:
    """对根包做已安装版本的依赖遍历，锁"已验证组合"而不是"最新解"。"""
    from importlib.metadata import version, requires, PackageNotFoundError
    from packaging.requirements import Requirement
    from packaging.utils import canonicalize_name

    seen, todo = {}, list(roots)
    while todo:
        name = canonicalize_name(todo.pop())
        if name in seen:
            continue
        try:
            ver = version(name)
        except PackageNotFoundError:
            continue
        seen[name] = ver
        for raw in (requires(name) or []):
            req = Requirement(raw)
            if req.marker is not None and not req.marker.evaluate():
                continue
            dep = canonicalize_name(req.name)
            if dep not in seen:
                todo.append(dep)
    return seen


def write_ascii(path: Path, text: str) -> None:
    """纯 ASCII + CRLF + 无 BOM。"""
    assert text.isascii(), f"{path.name} 含非 ASCII 字符"
    with path.open("w", encoding="ascii", newline="\r\n") as fh:
        fh.write(text)


def build_payload(dest: Path, exclude_lfs: set) -> tuple:
    """`git archive` 流式过滤写盘：一次遍历，无中间解包目录。

    符号链接单独处理：Windows 无权限创建 symlink 时 git 会把它检出成"内容是目标路径字符串"
    的普通文件，那种东西交付出去只会误导。这里**解引用**：目标若落在本包内就写出真实内容，
    否则跳过并记账（`symlinks_dereferenced` / `symlinks_skipped`）。
    """
    cmd = ["git", "-c", "filter.lfs.smudge=", "-c", "filter.lfs.clean=",
           "-c", "filter.lfs.process=", "-c", "filter.lfs.required=false",
           "archive", "--format=tar", "HEAD"]
    env = dict(os.environ, GIT_LFS_SKIP_SMUDGE="1")
    proc = subprocess.Popen(cmd, cwd=REPO, stdout=subprocess.PIPE, env=env)
    written, skipped = set(), {"lfs": 0, "prune": 0}
    links = []  # (link_name, target_raw)

    def keep(name: str) -> bool:
        if name in exclude_lfs:
            skipped["lfs"] += 1
            return False
        top = name.split("/", 1)[0]
        if top in PRUNE_TOP:
            skipped["prune"] += 1
            return False
        if name == "report" or name.startswith("report/"):
            if not (name == REPORT_KEEP or name.startswith(REPORT_KEEP + "/")):
                skipped["prune"] += 1
                return False
        return True

    with tarfile.open(fileobj=proc.stdout, mode="r|") as tar:
        for member in tar:
            # 只剥 `./` 前缀。不能用 lstrip("./")——那会剥掉任意前导 `.` 和 `/`，
            # 把 `.gitattributes` / `.gitignore` / `.pnpm-store` 剥成不带点的名字，
            # 既改坏文件名，也让按名字匹配的裁剪规则失效。
            name = member.name
            if name.startswith("./"):
                name = name[2:]
            if not name:
                continue
            if member.isdir():
                continue
            if not keep(name):
                continue
            if member.issym() or member.islnk():
                links.append((name, member.linkname))
                continue
            target = dest / name
            target.parent.mkdir(parents=True, exist_ok=True)
            src = tar.extractfile(member)
            if src is None:
                continue
            with target.open("wb") as fh:
                shutil.copyfileobj(src, fh)
            written.add(name)
    proc.stdout.close()
    rc = proc.wait()
    if rc != 0:
        raise SystemExit(f"git archive 失败（exit {rc}）")

    deref, dropped = [], []
    for name, raw in links:
        resolved = posixpath.normpath(
            posixpath.join(posixpath.dirname(name), raw or ""))
        if resolved not in written:
            dropped.append(f"{name} -> {raw}")
            continue
        blob = run(["git", "cat-file", "-p", f"HEAD:{resolved}"])
        if blob.returncode != 0:
            dropped.append(f"{name} -> {raw}")
            continue
        target = dest / name
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_bytes(blob.stdout.encode("utf-8", "surrogateescape"))
        written.add(name)
        deref.append(f"{name} -> {resolved}")
    skipped["sym_deref"] = deref
    skipped["sym_dropped"] = dropped
    return written, skipped


def main() -> int:
    ap = argparse.ArgumentParser(description="构建 COMACBench 内网离线交付包")
    ap.add_argument("--out", required=True, help="输出父目录")
    ap.add_argument("--skip-wheelhouse", action="store_true")
    ap.add_argument("--skip-bundle", action="store_true")
    args = ap.parse_args()

    version = run([sys.executable, "-c",
                   "import re,pathlib;print(re.search(r'^version = \"([^\"]+)\"',"
                   "pathlib.Path('pyproject.toml').read_text(encoding='utf-8'),re.M).group(1))"]
                  ).stdout.strip()
    commit = git("rev-parse", "HEAD").strip()
    tree = git("rev-parse", "HEAD^{tree}").strip()
    pkg = Path(args.out).resolve() / f"COMACBench-assets-v{version}"
    if pkg.exists():
        shutil.rmtree(pkg)
    pkg.mkdir(parents=True)
    print(f"包目录 : {pkg}")
    print(f"commit : {commit}")

    # ---- payload ----
    exclude = lfs_paths()
    print(f"LFS 跟踪路径: {len(exclude)}（整体排除，写入 03_LFS_UNAVAILABLE.md）")
    written, skipped = build_payload(pkg / "payload", exclude)
    print(f"payload: {len(written)} 文件；跳过 LFS {skipped['lfs']} / 裁剪 {skipped['prune']}"
          f" / 符号链接解引用 {len(skipped['sym_deref'])} / 丢弃 {len(skipped['sym_dropped'])}")

    # 守卫：payload 顶层条目必须都是 HEAD 里真实存在的名字。防的是"名字被改"这类
    # 静默损坏（例如用 lstrip 剥前缀把 `.gitattributes` 写成 `gitattributes`）。
    head_top = set(git("ls-tree", "HEAD", "--name-only").split())
    payload_top = {p.name for p in (pkg / "payload").iterdir()}
    stray = sorted(payload_top - head_top)
    if stray:
        raise SystemExit(f"payload 顶层出现 HEAD 中不存在的名字：{stray}")

    # ---- git bundle ----
    if not args.skip_bundle:
        (pkg / "git").mkdir()
        r = subprocess.run(["git", "bundle", "create",
                            str(pkg / "git" / "comacbench.bundle"),
                            "--branches", "--tags"],
                           cwd=REPO, capture_output=True, text=True,
                           env=dict(os.environ, GIT_LFS_SKIP_SMUDGE="1"))
        if r.returncode != 0:
            raise SystemExit(f"git bundle 失败: {r.stderr.strip()}")
        print("bundle : ok")

    # ---- wheelhouse ----
    roots = ["comacbench", "pytest", "numpy", "scipy", "scikit-learn", "pyyaml"]
    closure = dependency_closure(roots)
    closure.pop("comacbench", None)          # 自身由 payload 源码安装
    lock = "\n".join(f"{k}=={closure[k]}" for k in sorted(closure)) + "\n"
    wh = pkg / "wheelhouse"
    wh.mkdir()
    assert lock.isascii(), "lock 文件必须纯 ASCII"
    (wh / "requirements-lock.txt").write_text(lock, encoding="ascii", newline="\n")
    print(f"依赖闭包: {len(closure)} 包")
    if not args.skip_wheelhouse:
        wheels = ["pip", "setuptools", "wheel"] + [f"{k}=={closure[k]}" for k in sorted(closure)]
        cmd = [sys.executable, "-m", "pip", "download", "--only-binary=:all:",
               "--platform", "win_amd64", "--python-version", "3.11",
               "--implementation", "cp", "--abi", "cp311",
               "--dest", str(wh), *wheels]
        r = subprocess.run(cmd, capture_output=True, text=True)
        if r.returncode != 0:
            print(r.stdout[-3000:], r.stderr[-3000:])
            raise SystemExit("pip download 失败")
        print(f"wheelhouse: {len(list(wh.glob('*.whl')))} wheels")

    # ---- scripts ----
    write_ascii(pkg / "verify.bat", BAT_VERIFY)
    write_ascii(pkg / "install.bat", BAT_INSTALL)
    write_ascii(pkg / "run-comacbench.bat", BAT_RUN)
    write_ascii(pkg / "verify.ps1", VERIFY_PS1)
    write_ascii(pkg / "install.ps1", INSTALL_PS1)
    print("脚本   : verify/install/run .ps1 + .bat（纯 ASCII / CRLF / 无 BOM）")

    # ---- docs ----
    (pkg / "01_READ_ME_FIRST.md").write_text(READ_ME, encoding="utf-8", newline="\n")
    (pkg / "02_EVIDENCE.md").write_text(EVIDENCE, encoding="utf-8", newline="\n")
    lfs_list = "\n".join(sorted(exclude))
    (pkg / "03_LFS_UNAVAILABLE.md").write_text(
        "# 03 · 未随包交付的 LFS 路径\n\n"
        "## 结论\n\n"
        f"上游仓库共 **{len(exclude)} 个** 受 Git LFS 跟踪的路径，其**实体内容在本地与远端都取不到**：\n\n"
        "| 检查 | 结果 |\n|---|---|\n"
        "| 本地 LFS 实体对象（`.git/lfs/objects`） | **0 个**（仅 1 个 96 KB 的无关对象） |\n"
        "| 远端 LFS 对象（smudge 拉取） | **HTTP 404 — Object does not exist on the server** |\n"
        "| `git lfs ls-files` 标记 | 26924 个 `-`（指针，无实体）/ 1 个 `*` |\n\n"
        "因此这些路径**未随包交付**（既不是真数据，也不是 130 字节指针文本——后者看着像数据、\n"
        "实际不可用，留在包里只会误导）。\n\n"
        "## 影响\n\n"
        "- 依赖这批数据的 **CFD / 求解器相关算例与测试无法运行**。\n"
        "- 这是**数据可得性问题，不是本交付包的缺陷**；上游需要在有 LFS 实体的一方重新同步后另行交付。\n"
        "- 航空工作包（`packs/aviation-workload-starter-v1`）不依赖 LFS，装机验收完整通过。\n\n"
        "## 路径清单\n\n"
        f"共 {len(exclude)} 条：\n\n```\n{lfs_list}\n```\n",
        encoding="utf-8")

    # ---- manifest + checksums ----
    payload_files = sum(1 for p in (pkg / "payload").rglob("*") if p.is_file())
    wheels = sorted(p.name for p in wh.glob("*.whl"))
    manifest = {
        "protocol": "comacbench.offline-package.v1",
        "package": pkg.name,
        "version": version,
        "commit": commit,
        "content_tree": tree,
        "branch": git("rev-parse", "--abbrev-ref", "HEAD").strip(),
        "built_from": str(REPO),
        "payload_files": payload_files,
        "lfs_excluded_paths": len(exclude),
        "prune_rules": {
            "excluded_toplevel": list(PRUNE_TOP),
            "excluded_report_except": REPORT_KEEP,
            "excluded_lfs_tracked": len(exclude),
            "symlinks_dereferenced": len(skipped["sym_deref"]),
            "symlinks_dropped": len(skipped["sym_dropped"]),
            "note": "符号链接解引用为真实内容（Windows 无权限建 symlink 时 git 会把链接检出成"
                    "内容是目标路径的普通文件，那种形态交付出去会误导）。",
        },
        "wheelhouse": wheels,
        "acceptance_baseline": {
            "comacbench_validate": "runnable = true",
            "release_chain": "tests/test_release_chain.py pass (ten phases)",
            "report_render_layer": "static",
            "report_render_note": "本包不含 Playwright + Chromium（浏览器二进制无法离线安装，"
                                  "且约 200 MB 与 benchmark 使用无关），故发行链以 "
                                  "COMAC_REPORT_RENDER=static 运行：仍要求 "
                                  "probes/test_report_full.py 整体退出 0、静态层 TDZ PASS，"
                                  "浏览器层为 NOT_RUN。这是**已声明的降级**，非跳过。",
            "note": "装机验收只覆盖 validate 与航空工作包发行级链路；CFD 套件因 LFS 数据缺失无法运行。",
        },
        "source_env_gate": {
            "command": "python -m pytest -q -p no:cacheprovider tests/",
            "result": "5 failed, 256 passed, 17 skipped",
            "known_failures": "5 x OSError [WinError 1314] (Windows 符号链接特权缺口)",
        },
    }
    (pkg / "MANIFEST.json").write_text(
        json.dumps(manifest, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")

    # SHA256SUMS 必须排除自身
    sums = []
    for p in sorted(pkg.rglob("*")):
        if not p.is_file() or p.name == "SHA256SUMS.txt":
            continue
        sums.append(f"{sha256_file(p)}  {p.relative_to(pkg).as_posix()}")
    (pkg / "SHA256SUMS.txt").write_text(
        "\n".join(sums) + "\n", encoding="utf-8", newline="\n")

    # 守卫：契约里承诺的结构件必须真的在包里。防的是"定义了却忘了写盘"这类漏项。
    required = ["01_READ_ME_FIRST.md", "02_EVIDENCE.md", "03_LFS_UNAVAILABLE.md",
                "MANIFEST.json", "SHA256SUMS.txt", "verify.ps1", "verify.bat",
                "install.ps1", "install.bat", "run-comacbench.bat",
                "payload/pyproject.toml",
                "payload/comacbench/__main__.py", "payload/tests/test_release_chain.py",
                "wheelhouse/requirements-lock.txt"]
    if not args.skip_bundle:
        required.append("git/comacbench.bundle")
    if not args.skip_wheelhouse:
        required.append("wheelhouse/pytest-8.4.2-py3-none-any.whl")
    missing = [r for r in required if not (pkg / r).exists()]
    if missing:
        raise SystemExit(f"构建结构不完整，缺少：{missing}")

    total = sum(p.stat().st_size for p in pkg.rglob("*") if p.is_file())
    print(f"校验项 : {len(sums)} 个文件")
    print(f"包体积 : {total / 1048576:.1f} MiB")

    # ---- zip：实际交付载体 ----
    # 11300+ 个散文件不便拷贝/校验，交付用单个 zip。zip 放在包目录**之外**（兄弟位置），
    # 否则会把自己也算进 SHA256SUMS 的覆盖范围。
    zip_path = pkg.parent / f"{pkg.name}.zip"
    if zip_path.exists():
        zip_path.unlink()
    with zipfile.ZipFile(zip_path, "w", zipfile.ZIP_DEFLATED, compresslevel=6) as zf:
        for p in sorted(pkg.rglob("*")):
            if p.is_file():
                zf.write(p, arcname=f"{pkg.name}/{p.relative_to(pkg).as_posix()}")
    zip_sha = sha256_file(zip_path)
    (pkg.parent / f"{zip_path.name}.sha256").write_text(
        f"{zip_sha}  {zip_path.name}\n", encoding="ascii")
    print(f"zip    : {zip_path.name} ({zip_path.stat().st_size / 1048576:.1f} MiB) sha256={zip_sha[:16]}")
    print("完成。")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
