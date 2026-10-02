# 工程变更工作包：交互、重验与交付

状态：公开合成工作包的可运行原型。此模块只评工况输入的准备、版本影响与交付一致性；不运行真实性能程序、CAD/CFD/FEA 求解器，不提供设计放行或隐藏迁移结论。

## 1. 先跑一次完整过程

使用完整源码工作区与 Python 3.11+。本模块只使用标准库，独立于现有 `comacbench run`；它不证明 wheel 已经包含仓库中的场景与示例文件。

```bash
python examples/workbench/reference_policy.py --out ./change-reference-01
python examples/workbench/reference_policy.py --negative stale --out ./change-stale-01
python examples/workbench/reference_policy.py --negative false-ready --out ./change-false-ready-01
```

打开各目录的 `report/report.html`。参考策略没有调用模型，不能计入模型成绩。两个负例也不是两个新增工程场景。

默认场景只有**一个工作包、三个阶段、五个交付节点**：

| 阶段 | 发生什么 | 应当怎样处理 |
| --- | --- | --- |
| baseline | 三组明示单位的合成工况 | 生成每个工况的规范化记录、运行清单、审查报告并检查 |
| conditions-b | cruise 改变；reserve 新资料缺高度单位；说明文字也更新 | 重验受影响记录；reserve 标记 `missing_unit`，不猜单位；保留 ground 的有效证据 |
| program-2 | 程序版本从 1.0 改为 2.0 | 只需更新运行清单与报告，三个规范化节点的证据均可保留 |

参考策略使用 25/48 次行动：11 次登记、11 次检查、2 次阶段推进、1 次提交。它证明的是此冻结公开场景的接口和校准行为；不是最优策略、模型预算结论或统计独立样本。

最终 `complete=true` 的含义是**工作包被正确处理**。这个场景仍有 `reserve` 需澄清，最终声明必须是 `needs_review`，不能写成全部可执行。报告同时突出显示这两件事。

## 2. 让已有 Agent 使用这个环境

COMACBench 不再另造一个 Agent 宿主。DSH 或其他可信本地 Agent 通过 CLI 调用此工具即可；本轮未验证某个具体 DSH/模型适配器。

```bash
python -m comacbench.workbench start examples/workbench/workload-change-v1.json \
  --out ./change-agent-01 --subject my-agent --revision frozen-config-01

python -m comacbench.workbench observe ./change-agent-01
python -m comacbench.workbench act ./change-agent-01 --action-file ./agent-action.json
python -m comacbench.workbench report ./change-agent-01 --out ./change-agent-report-01
```

PowerShell 中将带 `\` 换行的命令写成一行。`agent-action.json` 放在会话目录之外，不要向 `events/` 写入额外文件。

每次 `observe` 返回当前源数据、依赖图、每个节点的状态、依赖摘要、公开输出契约以及剩余行动数。Agent 决定操作顺序；结果检查不依赖它的自报成功。示例动作：

```json
{"op": "check", "target": "normalized_ground"}
```

登记产物使用 `put`：提供 `target`、JSON `payload` 和 `basis`。`basis` 必须按本次观察中的 `dependencies[target]` 填写，精确包含所有直接依赖及其摘要，不能用名称或修订标签代替。

| 行动 | 语义 |
| --- | --- |
| `put` | 保存提交的 JSON 内容及其来源摘要；保存成功不等于内容有效 |
| `check` | 从当前冻结源数据独立推导期望，核对内容；父节点也必须已通过当前版本检查 |
| `advance` | 当前工作包全部通过后，应用下一个预先声明的变更；返回失效与保留节点 |
| `submit` | 所有强制阶段完成后提交最终声明；声明必须与当前通过检查的审查报告一致 |

`advance` 只能应用场景预先声明的变更，不能自由篡改源资料。公开场景完全可见，所有参考规则也公开；这不是隔离测试。

## 3. 证据怎样失效

每个源节点以**规范化 JSON 内容摘要**标识。每份产物以 `payload + basis` 标识。当前摘要不匹配、依赖缺失或父节点未验证，都会使下游状态失效。仅把 `source_revision` 从 A 改成 B，不能使旧数值通过独立内容检查。

说明文字 `note` 不在技术依赖图内，单独修改它不会让全部证据失效。程序版本是运行清单与报告的依赖，不是工况单位换算的依赖。这是本轮“只重验必要部分”的可执行边界；没有声称自动理解任意工程图谱。

状态为 `missing / stale / unchecked / failed / verified`。改写一个已验证父节点会立即影响其后代。曾经检查通过的旧证据仍在原始事件中保留，不会被重新命名为当前证据。

## 4. 独立检查与负例

`workbench_review.py` 从源数据计算预期内容，不读取参考策略的答案，不信任 Agent 的状态字段，也不由 Agent 更改阈值。示例参考策略使用独立实现（Decimal 换算），测试中另有固定数值答案、错单位、重复／漏行、旧版本、布尔数值、虚报求解等探测。

本轮的单位换算规则与内容容差是**输入文件协议**，不是物理仿真或适航验收容差。拒收原因按公开规则判定：先判断零条／多条记录；单条记录按 altitude、mass_flow 顺序检查，每个量依次检查单位缺失、单位不支持、数值非法。不能通过解释文字中出现某个词获得通过。

参考正例通过不代表检查器绝对正确；专家审查仍是升级到工程试用的独立步骤。

## 5. 预算、恢复和复查

所有受理的合法 JSON 动作都消耗行动预算，包括未知操作、错误参数、检查失败、错误完成声明。预算贯穿所有阶段，不因恢复会话而重置。语法错误、过大请求、锁冲突和不可核验归档属于材料／基础设施错误，不伪装为模型能力失败。

`observe` 与 `report` 不消耗行动数。它们重新读原始事件并重放纯状态与内容检查，不执行 Agent 或求解器。未来接原生求解器时，应归档工具结果和原生产物，**不能在状态重放中重复启动求解器**。

事件文件按序新增，保存失败尝试和摘要链。读取时检查序号、链、结果重算、冻结场景和引擎版本。中断留下的半个文件、缺失的中间事件、额外事件文件与伪造 verdict 会阻断复查，不会被自动删掉。单写者锁不会被另一读写请求强行清除；若进程中断，先保存归档、确认无存活写者，再人工调查，不提供绕过验收的 `--force`。

这是**可信本地环境**，不是签名、沙箱或可信执行。操作者若能改写整份归档、重造摘要或删除尾部记录，本工具不能证明其完整历史。`subject` 身份是声明信息，不证明操作全部来自同一 Agent，也不自动发现会话外人工干预。预算只限制本工具受理的行动，不计量／限制 token、求解核时或外部工具。真实 A/B 前必须另行冻结模型、工具与经验包并记录这些资源。

CLI 退出码：`0` 为命令正常完成；`act` 的可记录拒绝返回 `1`；材料、身份、预算耗尽、锁或归档错误返回 `2`。`report` 正常生成可返回 `0`，即使任务未完成；读取其中的 `complete` 和逐项状态，不以进程退出码代替能力成绩。

## 6. 交付物与既有协议的关系

报告目录包含 `report.html`、`report.json` 以及 `artifacts/`。每个已提交节点导出一份独立 JSON 文件；`artifacts/manifest.json` 记录字节 SHA-256、来源摘要、当前状态与完成状态。缺失节点不会伪造文件；失败或陈旧产物也保留并明确标记。导出内容与会话原始归档分离，修改导出副本不会改写原始事件。

这些是 `comacbench.workbench.v1` / `comacbench.workbench.artifacts.v1` 记录，**不能**冒充 `comacbench.run.v1`、既有 `artifacts.v1` 或已被 Campaign 接收的成绩。现有 pack 的 TaskSpec、真值、容差、评分权重、Agent 协议与 Campaign 锁格式均不改。

新源码会改变既有 pack 全局 engine identity。升级后新实验使用新输出目录，不能对旧 pack 运行强行 resume。WorkBench 自身冻结状态引擎和独立检查器的摘要；检查逻辑改变后也要新建会话。

下一条工程开发线应为此协议接入一个已有原生求解后端和经过专家确认的工作包，再补充固定配置的真实 Agent 实验。独立隐藏实例、求解器预算与跨软件等价性需分别验收，不能从本轮合成数据自检推出。
