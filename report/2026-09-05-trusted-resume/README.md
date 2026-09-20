# B02＋B04 可信复跑修复；B03 独立表格契约修复

日期：2026-09-05。分支：`codex/trusted-resume-and-formula`。
基于 `25a81e7c38580274b532a8a62abab9954f75c633`；本次未提交、推送或改写历史评测结果。

## 修改范围

| 工作项 | 文件 | 实现 |
| --- | --- | --- |
| B02 | `runners/run_state.py`、`runners/common.py`、五类 runner 的 `main` | 统一身份校验、全量缓存预检、原子 JSON 发布、进程写锁、执行前 manifest |
| B04 | 同上，重点 `runners/qa_grounded.py` | 真实执行题数、选中 IDs、隐藏参数及实际解释器的可重放命令 |
| B03 | 仅 `runners/design_artifact.py::_run_formula_task` 判分逻辑 | 指定答案表、原输入工作表保留、非空答案区；转换改名兼容；错误 gold/转换结构归为 harness 故障 |
| 验收 | `tests/test_run_identity.py`、`test_adapter_resume.py`、`test_hidden_replay.py`、`test_interrupted_resume.py`、`test_harness_replay.py`、`test_formula_contract.py` | 真实 CLI、临时虚构数据、oracle/stub、loopback 假 provider、实际 LibreOffice |
| 协议 | `docs/specs/trusted-resume-v1.md` | 版本、兼容性和复跑边界 |

B03 保持单独函数修改和独立测试，不涉及其他 grader、任务 YAML、oracle 源码或评分权重。

## B02＋B04 行为与兼容性

- 在既有 `manifest.extra` 内新增 `resume_identity` v1 和 `selected_task_ids`；在 `result.artifacts` 内新增身份摘要。顶层结果字段、分数公式及 CLI 参数名不变。
- 身份覆盖 provider/实际模型、端点摘要（不存密钥）、seed、runner 环境摘要、任务与有效题面摘要、资产、声明的 gold/QoI 文件、oracle 伴随模块、Harness 参数。
- 在调用 provider 和重写 manifest 前检查全部缓存文件；不同身份、错误任务、残缺结果、旧协议或额外结果文件均非零退出，已有结果及 manifest 字节保持不变。
- 相同身份只执行缺失任务。manifest 在首题前原子落盘；任务结果通过同目录临时文件加 `fsync`/`os.replace` 发布。POSIX `flock` 排除同目录并发写入，进程死亡后锁自动释放。
- 已有 run 的目录必须显式使用 `--resume`。旧历史结果继续可读，但没有身份元数据的目录不能直接续写；应使用新 `--out` 开启新周期，不回填历史身份。
- `n_tasks` 使用最终执行集合，覆盖 hidden、limit、partial-oracle。命令携带实际 Python、实际模型、seed 及全部 Harness/隐藏选项，并正确引用含空格路径。命令默认带 `--resume`，更换 `--out` 可从头复跑。

## B03 的独立修复和转换回归

原实现遇到错误 `answer_sheet` 会退回第一张工作表，并固定给出 requirements=1。现在原始候选必须包含指定答案表及输入工作表，目标区域必须非空；缺表/缺文件/空区域为 gate=0、score=0。

首次严格检查使官方 oracle 从 25/25 降为 24/25。单独检查 `ssb_22_47` 后确认：原始输出与输入、gold 均含 `sheet1`，本机 LibreOffice 26.2.3.2 重算后将其改为 `sheet1 -1`。因此这不是 oracle 数据错误。

最终实现先校验原始工作簿的指定表和保留表。对转换产物仅允许表数不变、顺序不变、每个表名相同或增加 ` -N` 的可核验改名；映射记录在 `grade_details.recalc_sheet_mappings`。不符合该转换规则时归为 harness 故障，绝不退回任意第一张表。错误原始表名仍被拒绝。该官方题已进入独立回归测试。

## 验证命令与证据

```sh
.venv/bin/python -m unittest discover -s tests -p 'test_*.py' -v
git diff --check
.venv/bin/python -m runners.qa_grounded --tasks tasks/awext.clause_extract --out /tmp/comac-awext-new-cycle --provider oracle
.venv/bin/python -m runners.design_artifact --tasks tasks/spreadsheetbench.verified_subset --out /tmp/comac-ssb-new-cycle --provider oracle
```

后两条命令应选择尚未使用的输出目录，或在身份相同时加 `--resume`。

- `tests.log`：21 个测试全部通过，无跳过。覆盖四个非 QA adapter 子用例、QA 的身份拒绝、真实强杀恢复、并发锁、hidden 8 题两次重放、Harness/伴随模块变化、7 个表格用例。
- `verification.json`：命令、退出码、耗时、源码/测试 SHA256、语法检查、环境依赖。
- `qa-oracle.json`：公开 awext **12/12 满分**，逐题 gate/score 与完整 manifest。
- `spreadsheet-oracle.json`：官方表格 **25/25 满分、gate 全通过、无作废**，逐题 gate/score、完整 manifest 与 `ssb_22_47` 转换映射。

测试先复现身份漂移仍被接受、残缺缓存晚失败、伴随模块变更未识别、错表名得分等问题，再验证修复后的 CLI 行为。没有生产模型请求；loopback 假 provider 只用于验证中断时是否重复请求已完成任务。

本机原 `.venv` 缺少 code_exec 导入所需依赖，已补装 `scikit-learn==1.6.1`、`joblib==1.4.2`、`threadpoolctl==3.6.0`，没有升级已有包或修改仓库依赖文件。

## 风险与后续

- 身份检查用于本地一致性，不是防恶意伪造的签名，也没有增强 sandbox 隔离或认证全部外部求解器/依赖版本。
- B03 修复会改变违规表格的得分；模型评测必须进入新周期，不能覆盖旧成绩。LibreOffice 未知的结构转换会使任务作废，需独立诊断。
- 本次没有执行真实模型、完整 CFD/CAD 求解或内网安装验收；oracle 是判分器自检，不能当作模型能力结果。
- 原有 `data/scicode/physics/test_data.h5` 删除与 CFDB YAML 的 `oracle_source` 修改均保留，旧接手分析报告也保持不变。
- 推荐下一步按新身份协议开新目录，执行一个固定预算的真实模型小样本，再进入 B05 入口契约校验；SciCode 资产恢复继续按 B01 单独处理。
