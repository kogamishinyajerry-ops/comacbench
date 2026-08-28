# PROVENANCE — cfdb.*（GLM-CFD-Benchmark 镜像）

> 上游：github.com/kogamishinyajerry-ops/GLM-CFD-Benchmark（本地克隆
> `~/projects/cfd/runtimes/cfdb`，即用户所指"GLM_Benchmark 项目目录"）。
> 镜像 revision：**cfdb@b26799e**（2026-08-28 镜像时上游 HEAD，
> b26799ebc6d2d931a71a07c911fdb8f699b03fe5）。

## A. 镜像范围（逐字复制，无任何内容改写）

| 上游目录 | 镜像路径 | 案例数 | 内容 |
| --- | --- | --- | --- |
| cases/case_setup | data/cfdb/case_setup | 17 | solver-agnostic 工程任务书（visible/task.md + drawing.png）+ 冻结 QoI 脚本 + held_out 参考 |
| cases/verification | data/cfdb/verification | 10 | 解析/程序化参考的 V&V 案例（完整参考算例 + held_out/qoi.json） |
| cases/validation | data/cfdb/validation | 15 | 实验/跨代码参考的验证案例（NACA0012 系列、圆柱 Re40/100、空腔 Re400/1000 等） |

- 上游 LICENSE（MIT）随镜像存于 data/cfdb/LICENSE；MIT 允许复制与再分发，
  `mirror_allowed: true`，再分发时须保留上游版权声明。
- 上游 trust 机制要点（与本仓库纪律同构，未做语义改动）：判分材料（隐藏 checker /
  normalize 规则）与参考数据一样 sha256 锚定；LLM-as-judge 永不进入任何判分路径；
  held_out 对账防"手写 qoi.json 得分"。

## B. 任务转化（tasks/cfdb.*，42 任务）

- 生成器 `runners/gen_tasks_cfdb.py`（--check 可校验漂移）：case_setup 题面 =
  上游 visible/task.md 逐字拷贝；verification/validation 题面 = 由 case.yaml 元数据合成
  （描述/物理/工况/QoI 原文引用，不新增物理声明）。
- **registry 状态 = staged 而非 integrated**：simulation_agent 的 `cfdb_case_setup` /
  `cfdb_cfd_qoi` 两个 exec_kind 分支尚未实现（判分侧需 OpenFOAM v2312 docker 跑
  managed 模式、evidence 模式走冻结脚本宿主降算）。任务 YAML 已写明完整判分契约，
  实现分支后即可 oracle/staged 升级。这是如实的状态机使用，不是降级。
- evidence 模式价值：判分侧**不跑求解器**，与本项目内网策略（env-matrix.md：商业 CFD
  Fluent/StarCCM+ 批处理）天然兼容——agent 在内网用商业求解器自行求解并提交证据包。

## C. 与既有条目的关系

- 上游 case_setup/verification 的 17+10 案例与本仓库 cfdllm.foam_basic（FoamBench
  110+16）不重叠：cfdb 是"任务书→自建案例"与"经典 V&V 复现"，FoamBench 是"教程级
  案例改写"；两者互补构成 agent-CFD 仿真执行层。
- 上游 coding_tasks/agentic_tasks（文件操作/编码 checker 类）本次未镜像：与本仓库
  humaneval/mbpp/spreadsheetbench 定位重叠，价值密度低；需要时按同一模式扩镜像。
