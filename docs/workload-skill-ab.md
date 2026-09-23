# 工程 Skill A/B：先看新增退步，再看净提升

本阶段交付：逐任务配对诊断与一份现有 workload 的实验配方。没有增加求解器、改动判分规则，也没有声称已取得真实模型成绩。

## 为什么总通过率不够

合成示例：A、B 都做对 3/4 项，净变化为 0；B 修好了一个单位处理问题，同时引入了一个拒绝清单错误。只看“0 个百分点”无法发现这次回退。

新报告保留原有整体通过率差，追加每一组相同 `case × seed × suite × task_id` 的五类变化：新增通过、新增退步、保持通过、仍未全过、待核验。它比较**是否通过全部要求**，没有另造分数。0.2 到 0.8 仍属于“仍未全过”，两个原始分数都可查看。

新增退步优先展示；展开对照可看到 A/B 分数与原始 failure_mode/gate_failures。没有诊断时明示“未记录具体诊断”，不编造单位、物理或工具错误原因。这些诊断是原记录，不是自动根因分析。

原始记录 SHA、run SHA 和归档内的相对文件位置保留在 `campaign.json` 的 `comparisons[].paired_outcomes.tasks`。HTML 每组最多显示 100 条，JSON 保留全部计划配对；不能把 HTML 的显示上限当成分母变化。

## 缺项、混档与准入边界

单个运行缺失、损坏、身份漂移或运行器崩溃时，其配对为待核验，不将它解释为模型零分或新增退步。组内其他已经核验的差异可以用于定位，但整组的通过率差仍为空，报告提示只能看局部。

归档扫描失败或发现未登记的额外运行时，整个对照的分类暂停，全部配对记为待核验。任务自身合法的 timeout 则仍按原协议作为已完成的失败，不能与运行器 crash 混为一类。

`publishable=false`、`isolated_transfer_verified=false`、`engineering_artifacts_reverified=false` 保持不变。不因为没有观察到退步，就自动推荐替换旧 Agent。有限种子不证明独立统计重复；两套配置的关联差异也不自动证明因果。

## 用现有四个 workload 任务开始

使用 `examples/campaigns/workload-skill-ab.plan.json`。它复用已有公共合成包 `aviation-workload-starter-v1` 1.1.0：

| 现有 task_id | 观察重点 |
| --- | --- |
| workload_baseline_01 | 正常工况到受约束输入文件与清单 |
| workload_missing_unit_02 | 单位缺失时的处理 |
| workload_conflict_dup_03 | 重复与冲突记录的处理 |
| workload_stale_output_04 | 旧版本输出的识别与对账 |

四项都按公开开发材料处理，不把它们标为隐藏迁移。两套配置、四项任务、三个种子，共 **24 次计划计分任务执行**，不含前置校准及 Agent 身份锚点运行；仍然只有四项任务，没有新增 24 个场景。

准备两个现有协议的真实 Agent 配置 `my-agent-base.json` 和 `my-agent-skill.json`。两者使用相同模型、Harness、允许工具、预算及超时，只改变待研究的 Skill。将 Skill 和提示词相关文件实际纳入 `revision_files`／对应身份登记；不要把参考程序改名成 user_agent 充当模型。

凭据仅通过现有环境变量提供，不写入配置、实验计划或提交仓库。对内网材料使用内网获准模型；本配方不替你选择外部数据传输目的地。

在已验收的源码依赖环境、仓库根目录运行（不是安装说明）：

```bash
python -m comacbench validate packs/aviation-workload-starter-v1
python -m comacbench calibrate packs/aviation-workload-starter-v1 --out ./ab-anchors/calibration
python -m comacbench run packs/aviation-workload-starter-v1 --agent ./my-agent-base.json --seed 0 --out ./ab-anchors/baseline
python -m comacbench run packs/aviation-workload-starter-v1 --agent ./my-agent-skill.json --seed 0 --out ./ab-anchors/with-skill
python -m comacbench.campaign freeze examples/campaigns/workload-skill-ab.plan.json --anchors ./ab-anchors --out ./workload-ab.lock.json
```

校准应通过，真实 Agent 锚点需要是合法完整运行但可以包含任务失败。冻结使用已经暴露的预检记录，因此这是公开回归，不是盲测预注册。

正式评分目录单独生成。交错执行 A/B，保留全部失败，不挑最佳重试：

```bash
python -m comacbench run packs/aviation-workload-starter-v1 --agent ./my-agent-base.json --seed 0 --out ./ab-runs/baseline/workload/seed-0
python -m comacbench run packs/aviation-workload-starter-v1 --agent ./my-agent-skill.json --seed 0 --out ./ab-runs/with-skill/workload/seed-0
python -m comacbench run packs/aviation-workload-starter-v1 --agent ./my-agent-base.json --seed 1 --out ./ab-runs/baseline/workload/seed-1
python -m comacbench run packs/aviation-workload-starter-v1 --agent ./my-agent-skill.json --seed 1 --out ./ab-runs/with-skill/workload/seed-1
python -m comacbench run packs/aviation-workload-starter-v1 --agent ./my-agent-base.json --seed 2 --out ./ab-runs/baseline/workload/seed-2
python -m comacbench run packs/aviation-workload-starter-v1 --agent ./my-agent-skill.json --seed 2 --out ./ab-runs/with-skill/workload/seed-2
python -m comacbench.campaign report ./workload-ab.lock.json --runs ./ab-runs --out ./ab-report
```

打开 `ab-report/report.html`，先看待核验项，再看新增退步，最后看新增通过与净变化。人工介入、实际资源消耗和费用仍需另行记录；本 PR 没有新增预算强制执行或调度器。

## 兼容性

继续接受 lock.v2，不需要因这次报告增强更换锁协议。完整、同引擎的历史 v2 归档可以直接重新出报告；不重跑模型，也不改写旧锁或旧分数。

新代码会被既有 engine_identity() 计入，所以新产生的实验需新输出目录与一致的新引擎锚点。不能把旧、新引擎运行拼成一个实验。旧 v1 锁仍按已有规则拒绝，迁移见 `campaign-v2-acceptance-2026-09-22.md`。

## 本阶段验收目标

先证明报告可以暴露“净提升为零但有新增退步”的情况，再由目标机器完成上面的真实模型配对。后续值得推进的是独立维护者控制的新实例及干净机器上的离线交付验收；不要用更多公开重复任务替代这两件事。
