# 从单个算例走向任务族实验：HydroGym 对 COMACBench 的参考价值

状态：**增量开发／公开回归工具，非发布批准，非隔离迁移认证。**

## 1. 借鉴什么，保留什么

HydroGym 将流动控制环境、求解器和控制策略分开组织，支持不同环境配置、重复实验与控制方法比较。官方来源：

- HydroGym 仓库：https://github.com/dynamicslab/hydrogym
- 官方 Quickstart：https://dynamicslab.github.io/hydrogym/docs/quickstart/
- 2025 L4DC 论文：https://proceedings.mlr.press/v283/lagemann25a.html

这里借鉴的是实验组织方法，没有复制 HydroGym 源码、环境资产或策略权重。COMACBench 继续评价工程 Agent 的任务交付；不把它改造成 RL 控制器排行榜，也不引入 Firedrake、MPI、JAX 或 HydroGym 依赖。

既有 `validate → calibrate → run → report` 保持不变。新模块只读已经生成的 `comacbench.run.v1` 记录，在其上提供固定实验矩阵和对照报告，不改 grader、参考真值、容差、权重或 Agent 协议。

| 要回答的问题 | 本次增加的机制 | 不能据此声称什么 |
| --- | --- | --- |
| 熟悉样例与变体是否被混为一谈？ | development / transfer / stress 分栏 | public transfer 不是未见过的隐藏测试 |
| 只展示成功运行了吗？ | 预先登记 subject × case × seed，缺项保留分母 | 不能阻止操作者在登记前筛选或删除外部实验 |
| 换了环境或改了检查器吗？ | 每个 case 固定 pack、engine、environment、task roster；subject 固定已登记的 Agent 身份 | 摘要不是签名或可信执行证明 |
| 报告里的 full_pass 可信吗？ | 回读原始 result JSON 与 run_manifest.json、检查摘要和 provider/seed 一致性，重算 gate=1 且 score=1 | 不重新计算流场，也不重跑业务检查器 |
| 与基线相比提高了吗？ | 对相同 case/seed 的有效完整记录作百分点差值 | 不提供通用总分、置信区间或“性能提升倍数” |

“任务族”由工程负责人定义。该工具不自动证明两个构型共享物理机制，也不把参数组合数解释为独立能力覆盖数。

## 2. 两个命令

```bash
python -m comacbench.campaign freeze PLAN.json --anchors ./anchors --out ./experiment.lock.json
python -m comacbench.campaign report ./experiment.lock.json --runs ./campaign-runs --out ./campaign-report
```

两个命令均不执行 Agent、贡献代码或求解器，不下载数据、不访问模型接口。模块只依赖标准库及既有 `comacbench.completion`。

`freeze` 使用**已经完成的预检记录**确定契约，避免手工填写一大串摘要。case 锚点须所有任务满分且达到对应执行类型的证据要求，可以来自参考实现或校准；subject 锚点必须来自真实 `user_agent` 配置，可以包含合法的任务失败。锚点不进入成绩分母。

因此这是公开开发／回归流程，**不是盲测预注册**：预检锚点本身可能已经使任务暴露。v1 只接受 `scope: public_regression`；改成 `isolated_holdout` 会被拒绝。

`report` 仅按冻结矩阵读取路径，不搜索“最佳结果”：

```text
campaign-runs/
  candidate/
    starter/
      seed-0/run.json
      seed-0/runs/<suite>/run_manifest.json
      seed-0/runs/<suite>/result_<task>.json
      seed-1/run.json
      seed-1/runs/<suite>/run_manifest.json
      seed-1/runs/<suite>/result_<task>.json
      seed-2/run.json
      seed-2/runs/<suite>/run_manifest.json
      seed-2/runs/<suite>/result_<task>.json
```

每个 `seed-N` 是原有 `comacbench run --out` 的完整输出目录。归档中的旧绝对 `result_file` 不用于读取；通过受检的 suite/task ID 定位本次复制目录内的原始结果。符号链接、路径越界、Windows 保留名和大小写路径冲突会被拒绝。

退出码：`0` 表示冻结成功，或计划记录全部可核验；合法任务失败不会改变为基础设施错误。`2` 表示格式、身份、完整性或输出路径问题。材料合法但运行缺失时，仍生成问题报告并返回 `2`。已有锁文件或报告目录不覆盖。

## 3. 从现有轻量包开始，不凭空增加迁移成绩

随附 `examples/campaigns/starter.plan.json` 只有一个开发 case 和三个种子：共计划 6 次任务执行，仍是原来的两个任务，没有增加独立工程场景。

在仓库已有可用源码环境中，先按首跑文档修复当前包的所有阻断。以下不是离线安装步骤，也不是承诺现有首发问题已经消失。

```bash
# 在本次新增代码已就位后，生成全新的锚点目录。
python -m comacbench run packs/aviation-data-starter-v1 --agent examples/agents/reference.json --seed 0 --out ./anchors/reference
python -m comacbench run packs/aviation-data-starter-v1 --agent ./my-agent.json --seed 0 --out ./anchors/candidate

python -m comacbench.campaign freeze examples/campaigns/starter.plan.json --anchors ./anchors --out ./experiment.lock.json

# 原有 CLI 负责执行；每个种子使用独立目录。
python -m comacbench run packs/aviation-data-starter-v1 --agent ./my-agent.json --seed 0 --out ./campaign-runs/candidate/starter/seed-0
python -m comacbench run packs/aviation-data-starter-v1 --agent ./my-agent.json --seed 1 --out ./campaign-runs/candidate/starter/seed-1
python -m comacbench run packs/aviation-data-starter-v1 --agent ./my-agent.json --seed 2 --out ./campaign-runs/candidate/starter/seed-2

python -m comacbench.campaign report ./experiment.lock.json --runs ./campaign-runs --out ./campaign-report
```

打开 `campaign-report/report.html`。首次试验只回答现有流程的重复运行情况，不显示虚构的迁移通过率。示例是 source-workspace 用法，不声称 wheel 已通过独立安装验收。

Agent 身份只覆盖既有协议实际登记的配置摘要、`revision_files`、`identity_env` 等。提示词、Skill、知识库版本应显式纳入这些登记项；未登记资源和人工干预不会被本工具自动发现。

增加基线时，先用基线 Agent 生成单独的 subject 锚点，在计划的 `subjects` 中登记其 ID 和锚点，在 `comparisons` 登记：

```json
{"baseline": "baseline", "candidate": "candidate"}
```

冻结后，基线也必须覆盖**相同** case × seed 矩阵。任何一侧有未核验项，对应任务族／分集不计算提升。不能用参考程序作为基线模型成绩，也不能通过改文件名给同一 Agent 身份重复记数。

## 4. case、family 与参数变体

一个 case 对应一个已经由既有运行器评过的 pack 契约。适合参数化研究的组织方法是：同一任务族有多个经过独立校准的 pack 变体，而每个变体的物理条件、资产和预算在其原有 TaskSpec 中表达，避免另造一套与 TaskSpec 脱节的参数真值。

示意，**不是本次已增加的可运行任务**：

```json
{
  "id": "pressure-unit-perturbation",
  "family": "apu-record-normalization",
  "split": "transfer",
  "scope_note": "公开同类变体：改变输入顺序与合法压力单位；仍属已约定规则域。",
  "anchor": "pressure-unit-perturbation/run.json"
}
```

同一 family 有 `transfer` 时，必须存在 `development`。`stress` 单独显示，不加进迁移通过率。完全相同的 pack 摘要和 task roster 不能作为两个 case 重复计数；换个 case 名字不能制造迁移集。

但是修改 README、题目 ID 或复制成不同包也能改变摘要。**语义去重、物理同类性、真正未参与开发，需要专家审查和独立发布流程，当前代码无法凭摘要证明。**

需要维护者确认每个 case 的 `scope_note` 和 family 边界。不要把同属“CFD”的所有任务归为一个可互相迁移的类别。

## 5. 报告的四条判读规则

### 固定分母

分母是计划任务执行数，不是“找到的成功结果数”。缺失、重复任务、损坏文件、环境错误进入未核验计数，不当作普通工程零分，也不从分母删除。当前实现会将完整性有问题的整个 run cell 标为未核验，避免部分损坏的运行看起来已经完整。

### 任务失败与管线故障分开

有效结果中 `gate=0, score=0` 可作为已完成的任务失败；沿用 `completion.result_issues` 定义的 `crash` / `env_mismatch` 等作废结果阻断该 cell。满分必须满足原始结果 `gate=1, score=1`，并达到执行类型对应的证据类别。摘要行上的 `full_pass` 与 `evidence_level` 不作为独立授权。

### 分组比较，不造一个万能总分

每个 subject × family × split 单独列：通过、任务未全过、待核验、计划、通过率。跨任务族不混加总分；不同成本和物理问题也不做“平均提升倍数”。有未登记的额外 `run.json`（例如未登记的 retry-best 目录）会阻断整个 campaign 的完整声明及对比通过率。

每个 seed 仍可能使用相同输入或相同确定性算法。次数增加不证明统计独立。本版不输出置信区间，也不审核实际 token、核时、求解步数、费用或限额执行。

### 报告自带结论边界

所有报告固定带有：

```json
{
  "publishable": false,
  "isolated_transfer_verified": false,
  "engineering_artifacts_reverified": false,
  "integrity_scope": "run_manifest_and_result_json_only"
}
```

这是**既有判分结果的完整性与可比性审计**。没有重新读取全部 CSV、网格、流场、求解日志并执行独立工程验收；不会用本 PR 掩盖先前发现的产物归档和恢复检查不足。

## 6. 兼容与迁移

新增文件不会修改现有命令或 run JSON 格式。但当前 `engine_identity()` 会遍历 `comacbench/` 与 `runners/` 下的 Python／HTML 源文件；新增 `campaign.py` 本身就会改变新运行的 engine 身份。

因此：**安装本次代码后，新实验、新锚点使用新输出目录。不要对旧运行强行 `--resume`，也不要修改旧 run.json 里的 engine 摘要来绕过保护。**旧证据保持原样；若仅审计同一旧引擎产生的历史记录，可以用这些旧记录建立单独公开回归锁。

该锁是无签名的本地可信记录。控制整个归档的操作者能重新生成摘要；它不提供对抗恶意管理员的安全性，也不代替隔离沙箱、签名、可信时间戳或权限管理。

## 7. 下一步，按这个顺序推进

**A. 收口首发证据问题。** 修复并实测原始产物字节归档、manifest、可信 resume 和包元数据／题面一致性。本 PR 不自动解决这些问题，也不提高现有包的发布等级。

**B. 一条真实的参数化任务族。** 优先选择现有确定性数据／交付物任务：APU 性能盘批处理的单位、行序、重复记录与拒绝清单，或固定范围内的仿真批处理结果汇总。规则、实例和独立判分应分离；每个公开变体须有参考正例和故障负例。然后再为合适的 CFD/结构问题添加真实求解变体，禁止用未经验证的缩放“推导真值”。

**C. 隔离迁移试验。** 由独立维护者保管新实例；冻结任务范围、Agent/Skill/工具版本、人工干预边界和调参预算，隔离答案与运行权限，再产生真正的 holdout 结果。新协议必须处理开发暴露、污染审计与审批，不是在 JSON 中加 `hidden: true`。

**D. HydroGym 外部环境。** 仅在内部任务证据链稳定后，考虑一个可离线、许可已审查、带数值基线的公开后端；单独运行，不放入基础安装依赖。真实工程任务不因引入公共 CFD 环境而减少。

## 8. 专项验证

```bash
python -m unittest discover -s tests -p test_campaign.py -v
```

测试使用明确标记的合成归档夹具，覆盖正常矩阵、合法任务失败、原始摘要、身份漂移、固定分母、重复 case、参考实现排除、恶意路径、JSON 边界、离线 HTML、CLI 退出码和不可覆盖行为。它们证明的是新审核器行为，不是模型成绩、真实 CFD 数值正确性、原有全量测试通过或内网发布通过。
