# FoamBench-Basic 数据镜像溯源（PROVENANCE）

> assets_revision: `foambasic@3b46d30+kaggle_v1+gt_runs_2026-08-19`
> 镜像日期: 2026-08-19 · 镜像执行: M3 会话（dev 终端）

## 镜像内容

| 文件/目录 | 来源 | 说明 |
| --- | --- | --- |
| `FoamBench_basic.json` | Kaggle `nithinsekhar/foambench`（sha256 `163702eb…08683722`） | 110 任务 = 11 算例族 × 10 变体；每任务 usr_requirement + 完整 GT 算例文件 |
| `LICENSE.BSD-3` | GitHub `NREL-Theseus/cfdllmbench` @ `3b46d30` | BSD-3-Clause |
| `upstream_*.py.reference` / `upstream_README.md.reference` | 同仓库 `FoamBench/` | 官方判分脚本与文档（只读参考） |
| `gt_cases/` | 本 harness 从 JSON 解包 | 110 任务 × GT 文件（1590 文件），源只读 |
| `gt_runs/` + `gt_runs_status.json` | 本 harness docker 预计算 | GT 参考场（末时刻），逐例状态 |
| `oracle_scripts/` | gen_tasks 生成 | GT 文件逐字写出器（判分器自检） |
| `run_gt_batch.py` | 本 harness | GT 批量预计算脚本（幂等） |

## 许可证据链（先许可证后镜像，2026-08-19 核验）

与 cfdquery/cfdcode 同源同链：仓库 LICENSE=BSD-3-Clause + 论文 arXiv:2509.20374
"CFDLLMBench is released under the terms of the BSD 3-Clause License"（覆盖 FoamBench
数据与 GT）。Kaggle 页 license 徽标 "Unknown"（上传者未选），不改变本体许可。镜像放行。

## 执行环境事实（与 env-matrix.md §0 的出入，如实记录）

- env-matrix 记载 dev 终端「装有 OpenFOAM + FoamAgent」；实测（2026-08-19）：
  **无本机 OpenFOAM、无 FoamAgent 包**；OpenFOAM 以 docker 镜像存在：
  - `openfoam/openfoam10-paraview510`（amd64，qemu 模拟；**v10 = FoamBench 上游指定版本**，
    方言匹配 GT 算例；实测 Cavity 6.5s/例）；
  - `opencfd/openfoam-default:2312`（arm64 原生但 ESI 方言：pisoFoam 需
    `constant/transportProperties`，GT 用 v10 的 `momentumTransport` → 不兼容）。
- **认知修正**：FoamBench 中 "Foam-Agent" 是被测算法框架（algorithm/ 槽位），非 harness
  依赖；本 harness 被测对象=生成算例文件的模型，OpenFOAM 只在判分侧运行。
- harness 采用：`runners/solvers/openfoam.py`（docker v10，amd64 模拟）。求解器无关原则
  不变：grader 只认 case 产物 + log End 判据 + NMSE 场比对；intranet 移植加 fluent.py。

## GT 预计算（docker v10，2026-08-19）

- 逐例：拷贝 gt_cases → docker Allrun → 官方判据（log.*Foam 倒数第二行 == "End"）；
- 结果：见 `gt_runs_status.json`（本文件头部修订时全部跑完；失败任务在任务生成器中
  如实排除并在 M3-summary 报告数量与原因）。

## 判分口径（官方语义 → simulation_agent 映射）

| 官方 | 本 harness |
| --- | --- |
| Execution（log End） | gate（simulation_failed / timeout） |
| NMSE（pyvista 末时刻场 [U,p,rho,T]，插值对齐，场均值） | physics（阈值 <0.1→1.0 / <0.3→0.5 / else 0，官方 score_calculation 映射） |
| Tree/ROUGE 结构相似度 | 不纳入（adapters/README.md §3 判分以物理结果为准；结构以 gate 的文件契约守） |
| — | requirements = 算例结构契约文件存在率（system 四件套+constant+0+Allrun） |

## 重取方式

```bash
curl -sL "https://www.kaggle.com/api/v1/datasets/download/nithinsekhar/foambench" -o foambench.zip
unzip foambench.zip   # -> FoamBench_basic.json / FoamBench_advanced.json
shasum -a 256 FoamBench_basic.json   # 应 == 163702eb…08683722
# GT 重算：python3 run_gt_batch.py（docker openfoam/openfoam10-paraview510 须在本地）
```
