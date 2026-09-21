# comacbench Windows 交接落地报告

日期：2026-09-20 ｜ 执行环境：Windows 11 + Git Bash + Python 3.11.8 ｜ 仓库：D:\comacbench

## 0. 一句话结论

按《Windows 交接指南》完成全链路落地：仓库（`codex/trusted-resume-and-formula`，head `f767602`）就位、`.venv` 建成、冒烟 validate blocker 0、全量测试 **142 例 0 failures**（8 errors 均为 Windows symlink 特权限制、17 skipped 为环境未装项）；**换机核心动机已兑现——StarCCM+ 19.02.009-R8 在位，CalculiX ccx 2.23 已部署并解锁 structures-v2 线（structural 测试 10/10 全绿）**。共修 5 处 Windows 兼容 bug（最小面），未触碰任何判分语义。

## 1. 环境栈 × 能力矩阵（实测）

| 能力 | 状态 | 说明 |
| --- | --- | --- |
| 核心包 validate/calibrate + core-v1 | ✅ | Python 3.11.8 venv，pip install -e . 成功 |
| structures-v2（CalculiX 求解） | ✅ **已解锁** | ccx 2.23 官方 Windows 版装至 `C:\ccx\calculix_2.23_4win\`，`CCX_BIN` 已入用户环境变量；版本与 `data/calculix/fea_basic/PROVENANCE.md` 声明一致（2.23） |
| StarCCM+（商业 CFD 线） | ✅ 在位 | 19.02.009-R8，`C:\Program Files\Siemens\19.02.009-R8\STAR-CCM+19.02.009-R8\star\bin\starccm+.bat` |
| cfd-step-v1（OpenFOAM 10 Docker） | ⚠️ 待启动 | Docker 28.3.2 已装，daemon 未启动；镜像需按 sha256:d6ff1f9a 拉回核对 |
| ssb / engtable（表格判分） | ❌ 未装 | 需 LibreOffice soffice（17 skipped 的一部分） |
| gtm 系列（MATLAB） | ❌ 未装 | 未在本机发现 MATLAB |
| ANSYS Fluent（商业线） | ❌ 未装 | 仅有 ANSYS Germany GmbH 目录（非产品安装） |

## 2. 获取仓库的曲折（如实记录）

1. **github.com 主站 443 被 SNI 阻断**（DNS 正常、api/codeload 子域可达），git clone 反复 early EOF；
2. **credential.helper 坏路径**：`~/.gitconfig` 指向不存在的 `vendor/PortableGit/.../git-credential-manager.exe`（Windows 凭据库里有有效 PAT）→ 改为 `wincred` 后凭据可读；
3. 最终通道：**API（分支/sha 查询）+ codeload tarball（111.5MB，gzip 校验通过）**，解压至 D:\comacbench 后 `git init` + fetch 补历史（fetch 仍在后台爬，网络间歇）；
4. **分支头 f767602 = Mac 侧 2026-09-20 15:39 推送的交接收口 commit**（README 重写、pip install -e、msvcrt 垫片、docs/windows-handoff.md）——9-11 报告的"B 线 11 天未提交"红色警报已解除；
5. 已开 `core.longpaths=true`；首次 checkout 失败根因是 data/ 下 100 个 OpenFOAM 冒号文件名（`strainRateViscosityModel:nu`，Windows 保留字符，且属 LFS 指针不可用区，影响可忽略）。

## 3. Windows 兼容性修复（最小面 5 处 + 依赖补齐）

| # | 文件 | 问题 | 修复 |
| --- | --- | --- | --- |
| 1 | runners/solvers/backward_step.py:38 | `str(path.relative_to())` 产生反斜杠，audit_inputs 对全部原生输入误报 precomputed_output | `.as_posix()` |
| 2 | comacbench/agent.py:114 | `os.killpg` Windows 不存在（timeout 杀进程崩溃） | nt 分支 `proc.kill()` |
| 3 | studies/_win_compat.py（新）+ 4 个 studies 脚本 | `import fcntl` Windows 无此模块 | msvcrt.locking 垫片（对齐主包 __main__.py 既有模式） |
| 4 | tests/test_cfd_evidence_admission.py:94 | 硬编码 `.venv/bin/python`（POSIX 路径） | `sys.executable` |
| 5 | tests/test_cfd_fourth_grid.py / test_cfd_re300.py | 路径比较用 `str()` 反斜杠不等 | `.as_posix()` |

依赖补齐：`openpyxl`（formula_contract 测试）、`pyvista`+`contourpy`（foam_nmse/studies 引入）——均测试链路所需，pyproject 依赖之外。

**未动**（如实记录）：report/ 下冻结证据副本中的 `.venv/bin/python` 字样；runners/arm_router.py、gen_tasks_pycycle.py 的同款硬编码（研究 harness，未在测试链路上）。

## 4. 测试终态

```
Ran 142 tests in 39.4s
FAILED (errors=8, skipped=17)   ← 0 failures
```

- **8 errors**：全部 `WinError 1314`（非管理员无 symlink 创建特权）。涉及 adapter_resume×4、hidden_replay、cfd_primary_delivery、cfd_fourth_grid、cfd_re300_large_initial_field。测试基建的环境限制，非产品缺陷；开 Windows 开发者模式或以管理员跑测试即可消除。
- **17 skipped**：LibreOffice/ssb 等环境未装项（交接指南预告过）。
- 校准过程中曾出现的 4 failures（路径分隔符 2 处、ccx 缺失 1、pyvista 缺失致 harness_replay score 0.0）已全部闭环。

## 5. 与 9-11 评估报告的差距对照（交接后开发优先级）

| 优先级 | 事项 | 本次状态 |
| --- | --- | --- |
| 判分遗留 | ssb 大表权重 / ssb_22_47 / CFD 10% 容差 | 未动（需 LibreOffice 后复现） |
| 商业线解锁 | nasa_tmr / crm / simjeb adapter | **StarCCM+ 已在位**，可启动 Fluent/StarCCM+ 批处理版 evidence 两阶段协议设计 |
| 内测门 | 15 分钟工程师首次接入实测 | 未做（需先完成安装故事 bootstrap） |
| 安装故事 | bootstrap 脚本（venv+依赖+CCX/Docker sha 探测） | 本次实操已验证全链路步骤，可作为 bootstrap 脚本的输入 |
| CFD Re200/300 转正 | 正例+负例+校准+工程审查 | studies 测试已在 Windows 全绿（fcntl 垫片后），研究线可继续 |

## 6. 已知限制与下一步（更新：git 历史已对齐）

1. ~~git 历史未对齐~~ **已闭环**：后台 fetch 完成（网络间歇致 6 小时），`git reset f767602` mixed 对齐成功（sparse-checkout 排除 gt_runs 冒号区 + `core.protectNTFS=false`），真实提交链 f767602a→7169680e→1faac525 在库；**对齐后回归测试结果不变（142 例 0 failures）**；5 处 Windows 修复以未提交改动保留。
2. **LFS 大文件**：data/ 下大文件远端为指针，需按各 PROVENANCE.md 从上游重镜像 + sha256 核验。
3. **冒号文件名**：`data/cfdllm/foam_basic/gt_runs/`（100 个 `strainRateViscosityModel:nu`）已由 sparse-checkout 永久排除；git status 中 report workspace/data、tasks/.foam_tail 等 symlink 条目显示 D 属预期（Windows 无法创建 symlink）。
4. **symlink 特权**：建议开 Windows 开发者模式（设置→隐私和安全性→开发者选项），消除 8 个测试 error。
5. **Docker daemon**：启动 Docker Desktop 后按 env-matrix 核对镜像 sha256，解锁 cfd-step-v1。
6. 提交纪律提醒：本次 5 处修复建议按仓库风格提交（中文长行），report/ 落盘本文件作为证据。
