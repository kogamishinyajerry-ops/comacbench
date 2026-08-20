# 会话提示词 —— 民机 Benchmark Harness 开发 Kickoff（M1）

> 用法：整段复制到新会话（同一仓库根目录 `/Users/Zhuanz/projects/jerry-personal/JerryDSH`）作为开场消息。
> 本文件本身也是交接文档：为什么这样开发、边界在哪里，都在这里。

---

## 提示词正文（复制以下全部）

你在 `/Users/Zhuanz/projects/jerry-personal/JerryDSH` 仓库工作，接手"民机设计 Benchmark Harness"的开发执行。设计与规范已全部定稿，你的任务是**按里程碑落地代码与评测**，不重新设计。

### 1. 先读这五个文件（动手前的唯一事实源，读完再写代码）

1. `benchmarks/README.md` —— 路线图、v0.1 核心八件套、M1–M4 里程碑、使用规则
2. `benchmarks/env-matrix.md` —— 两层目标环境（dev/intranet）、env_class 判定、Python 导入清单
3. `benchmarks/registry/registry.yaml` —— 接入清单 SSOT：每项的 adapter/env_class/license_status/status
4. `benchmarks/adapters/README.md` —— 五类 adapter 契约、通用 result.json、失败模式
5. `benchmarks/scoring/README.md` —— ValidityGate 公式、九维报告、judge 边界、划分纪律
6. `benchmarks/contracts/task.example.yaml` —— 任务 YAML 契约（逐字段注释）
7. `benchmarks/registry/license-notes.md` —— 许可证门禁：非 confirmed-\* 一律不得镜像

### 2. 环境事实（两次决策，以第二次为准）

- **dev 层（当前活跃）**：本开发终端装有 **OpenFOAM + FoamAgent**，无 Fluent/StarCCM。当前一切开发与评测都在这里跑，pip 直连可用。
- **intranet 层（最终移植目标）**：内网只有商业栈（ANSYS 系、StarCCM+、CATIA、Amesim、FENSAP、MATLAB），无 OpenFOAM。移植时 CFD 端到端换 Fluent journal / StarCCM macro runner。
- **求解器无关原则（硬性）**：simulation_agent 的 grader 只认 `result.json` + 残差/守恒/目标量，不绑定求解器 CLI。OpenFOAM 与 Fluent/StarCCM 是同一 adapter 下可替换的执行后端——runner 里求解器调用必须单独成层（如 `runner/openfoam.py` / `runner/fluent.py`）。
- foam_basic 已因 dev 终端有 OpenFOAM 恢复进 v0.1 核心（env_class=openfoam_dev）；其报告须标注运行环境为 dev 终端。

### 3. 本次会话目标：M1 —— 打通统一评测链路

按 `benchmarks/README.md` 里程碑定义，M1 = cfdllm.cfdquery + aeroengqa.gold 达到 `integrated`。具体交付：

1. **目录骨架**（在 `benchmarks/` 下新建，不碰仓库其他目录）：
   - `benchmarks/runners/` —— 五类 adapter 的 runner（M1 只需 `qa_grounded.py`）
   - `benchmarks/tasks/cfdllm.cfdquery/` —— 任务 YAML + 题目数据引用
   - `benchmarks/data/cfdllm/` —— 镜像数据 + `PROVENANCE.md`（来源 URL、license、拉取日期）
   - `benchmarks/results/cfdllm.cfdquery/<date>/` —— 基线报告
2. **cfdquery 镜像**：从 https://github.com/NREL-Theseus/cfdllmbench 拉取 CFDQuery 90 题；license BSD-3-Clause 已 confirmed-repo，可镜像；registry status → `staged`。
3. **qa_grounded runner**：实现 `adapters/README.md` §1 的客观层判分（选择题精确匹配）；输出按通用 result.json 契约（task_id/registry_id/adapter/subscores/score/artifacts/logs）；每个任务由 YAML 驱动（字段以 contracts/task.example.yaml 为准，qa 类可精简但不得新增互斥字段）。
4. **基线评测**：先用内置固定答案冒烟判分管线（不调模型，验证 scoring 端到端）；模型接入由我另行提供 API 配置——没有它就把冒烟结果作为"管线基线"并停在这一步等我。
5. **aeroengqa 许可核验**：只做核验不做镜像——查 Zenodo 数据记录的实际 license，把结论写回 `license-notes.md` 与 registry 的 `license_status`（confirmed-dataset 才许镜像；否则停在核验报告）。
6. **收尾**：两项 registry status 更新（staged/integrated 如实），M1 小结写进 `benchmarks/results/M1-summary.md`。

### 4. 工程规则（违反即返工）

- 先许可证后镜像：任何数据落盘前，license-notes.md 里该项必须是 confirmed-\*。
- 任务必须套五类 adapter 之一，禁止 fork runner；差异只通过任务 YAML 表达。
- ValidityGate 检查器先于子分实现（M2/M3 会用到；M1 的 qa 类 gate=格式/字段完整性）。
- 一切评测可离线重跑：固定随机种子、锁 assets_revision、判分输入输出全部落盘。
- 不静默扩 scope：M1 只做第 3 节列的事；发现的新需求记进 `benchmarks/results/M1-summary.md` 的"待议"清单。
- 报告结构遵循 scoring/README.md：qa 类也要给出 拒答正确率/引用失败 等 gate 类分布，不是只给一个均分。

### 5. 验收方式

我按三样东西验收：registry 的 status 变化、`results/` 下的报告、以及**一条命令重跑**（你最后要给我 `python -m benchmarks.runners.qa_grounded --registry-id cfdllm.cfdquery` 这类可复制命令，且它真的能重跑出同样结果）。

### 6. 可用工具

- Bash/读写文件工具直接用；本机 Python 3 可用，pip 直连。
- civair-kb MCP 工具与本次任务无关，不要调用。
- 遇到规范冲突（两个文件说法不一致）：以 registry.yaml + env-matrix.md 为准，并在 M1-summary 里记录冲突点，不要自行仲裁后隐瞒。

现在从第 1 节开始读文件，然后给我一个不超过 15 行的 M1 执行计划（含目录树），我确认后你再动手。

## 提示词正文到此（复制到此为止）

---

## 附：交接备忘（给人看，不进提示词）

- foam_basic 恢复决策：2026-08-19 用户确认开发终端有 OpenFOAM + FoamAgent，无 Fluent/StarCCM；评测先在 dev 终端跑，内网商业栈是移植目标。已同步 registry.yaml / env-matrix.md / README.md。
- 下一个里程碑提示词：M1 验收后，把本文件第 3 节换成 M2（scicode + cfdcode，code_exec runner + Python 沙箱）即可复用同一模板。
- 科普视频（设计构想讲解）在 `Minimax Video Master/videos/benchmark-harness-explainer/renders/benchmark-harness-explainer_v1.mp4`，与新决策有一处出入：视频中 foam_basic 标为暂缓，属制作时点的旧状态，以本文件为准。
