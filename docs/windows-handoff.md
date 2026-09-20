# Windows 交接指南（2026-09-11）

> 目的：在 Windows 机器上继续 benchmark 开发。原 Mac 开发机（本仓库出生地）无 StarCCM+/Fluent 等商业仿真栈，测试环境有限；Windows 机装好商业栈后可解锁 registry 中的 commercial_cfd / commercial_fea 线。当前项目全景与差距见 [report/2026-09-11-dev-status-and-beta-readiness.md](../report/2026-09-11-dev-status-and-beta-readiness.md)。

## 1. 克隆与安装

```powershell
git clone https://github.com/kogamishinyajerry-ops/comacbench.git
cd comacbench
git checkout codex/trusted-resume-and-formula   # 9 月工作分支（main 停在 08-31 前）
python -m venv .venv
.venv\Scripts\activate
pip install -e .
python -m comacbench validate packs\aviation-core-v1    # 冒烟：应输出 blocker 0
python -m unittest discover -s tests                    # 全量测试（需 LibreOffice 的 ssb 项可先跳过）
```

Python ≥3.10（Mac 侧 3.12 实测）。git 需要 LFS 支持（`git lfs install`）——虽然 GitHub 远端未上传 LFS 对象（见 §3），但 clone 时 LFS 会尝试拉取并失败，可忽略或 `GIT_LFS_SKIP_SMUDGE=1` 克隆。

## 2. 能力 × 环境矩阵

| 能力 | 需要 | Windows 获取 |
| --- | --- | --- |
| 核心包 validate/calibrate + core-v1 | Python + pip 依赖 | 无额外 |
| structures-v2（CalculiX 求解） | `ccx` 可执行 | CalculiX 官方 Windows 版（ccx 二进制入 PATH 或设 `CCX_BIN`） |
| cfd-step-v1（OpenFOAM 10） | Docker + 锁定镜像 `sha256:d6ff1f9a2e7bc3c9177f373bebbdeb542fd8b49144afc24d5e3a3cd9bfae253d`（`openfoam/openfoam10-paraview510`） | Docker Desktop；镜像若已删需从 Docker Hub 拉回并核对 sha |
| ssb / engtable（表格判分） | LibreOffice `soffice` | 安装 LibreOffice；判分代码以 `soffice` 命令调用，PATH 中需可见 |
| gtm 系列 | MATLAB | 商业许可 |
| 商业 CFD/FEA 线（nasa_tmr / crm_dpw_hlpw / simjeb） | Fluent / StarCCM+ / ANSYS MAPDL | **这就是换机的原因**——装好后这些 registry 条目从 proposed/blocked 转 staged 的路径见 `env-matrix.md` 与各 `data/*/PROVENANCE.md` |
| 研究 harness 各基准专属栈 | `.venv`（pycycle）/`.venv-aviary`/`.venv-cad` | 按各 PROVENANCE 重建，Linux/macOS 的钉子栈版本在 Windows 可能有差异，如实记录 |

## 3. LFS 数据镜像说明（重要）

GitHub 远端**没有**上传 6.1GB LFS 对象（超免费配额，已选"跳过 LFS 保留全历史"策略）：

- 受影响：`data/` 下大文件（mechvqa 图片、superwing/hilift npy、parquet、h5 等）在远端是指针文件，clone 后不可用；
- 不受影响：全部代码、任务 YAML、registry、packs、报告文本与图表（report 下 PNG 已转普通 git）、results 明细；
- 需要某个数据镜像时：按对应 `data/<族>/<基准>/PROVENANCE.md` 从上游重新镜像 + sha256 核验（项目本来的纪律）；
- Mac 本机 `.git/lfs` 仍是完整归档（含已从工作区删除的 scicode h5 等）；跨机搬运可用移动盘拷整个仓库目录。

## 4. Windows 兼容性现状

- ✅ 已修：`fcntl` 文件锁 → `msvcrt.locking` 垫片（`comacbench/__main__.py`、`runners/run_state.py`，2026-09-11）；路径处理均为 `pathlib`；
- ⚠️ 未验证：`soffice`/`ccx`/Docker 子进程调用的 Windows 路径与 shell 差异；`shlex.join` 用于展示命令的转义差异；信号处理（`signal`）语义差异。首次跑 `tests/` 时会暴露，按"如实记录 + 修最小面"处理；
- POSIX shell 脚本（若有）不在核心链路上。

## 5. 交接后的开发优先级（摘自 2026-09-11 评估报告 §4.3/§5）

1. 判分可信遗留：ssb 大表"未变格多→近满分"权重问题、`ssb_22_47` 排序歧义（隔离中）、CFD 10% 容差校准（GCI 0.884% 未过 0.5% 研究门）；
2. **商业求解器线解锁**（换机核心动机）：nasa_tmr / crm / simjeb 的 adapter + 判分复算层——参照 `cfdb` 的 evidence 两阶段协议（判分侧不跑求解器、冻结 QoI 脚本对证据包降算）设计 Fluent/StarCCM+ 批处理版本；
3. 15 分钟工程师首次接入实测（受控内测版唯一真门）；
4. CFD Re=200/300 从研究证据转正（需正例+负例+校准+工程审查）。

## 6. 仓库纪律提醒

- 禁止 fork runner：任务差异走任务 YAML；
- 判分先 gate 后子分；负例必须命中 `expected_issue`；
- 不追改历史分数：新规则=新身份=新目录；
- 提交信息中文长行风格（见 git log）；每轮工作 report/ 落盘证据。
