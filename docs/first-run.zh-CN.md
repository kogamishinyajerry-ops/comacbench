# 第一次使用：看懂一次评测，再连接自己的 Agent

这份指南回答三个问题：我要测什么？怎样跑完一次？结果能支持什么判断？“15 分钟接入”是准备好环境后的可用性验证目标，不是已完成的用户实测结论。

## 先认清四种操作

| 操作 | 谁在做题／工作 | 成功证明什么 | 不能证明什么 |
| --- | --- | --- | --- |
| `validate` | 只读检查材料 | 题面、资产与契约没有检测到的静态阻断项 | 本机依赖齐全、答案正确 |
| `calibrate` | 已知参考实现与已知错误实现 | 检查器对这些正负例表现符合契约 | 模型或你的 Agent 具备该能力 |
| `run --agent ...reference.json` | 直接返回已知答案的接口样例 | 输入输出协议及后续检查链路可工作 | 模型成绩、工程迁移 |
| `run --agent ./my-agent.json` | 你配置的真实 Agent | 该版本 Agent 在这些任务和预算下的表现 | 未测任务、飞机设计放行 |

## 维护者先准备运行环境

使用完整源码工作区与项目要求的 Python 依赖。当前 wheel 打包声明只包含 `comacbench`，运行却还依赖 `runners` 等源码与资产；不要把一个 wheel 当成已验证的独立离线安装包。

Windows PowerShell 可直接指定已准备好的解释器，避免激活脚本与全局 Python 混淆：

```powershell
.\.venv\Scripts\python.exe -m comacbench validate packs/aviation-data-starter-v1
```

下文的 `python` 都指这个已准备好的环境。所有命令在仓库根目录执行。轻量包不启动 CalculiX、OpenFOAM 或 Docker，但仍依赖当前项目的 Python 包和运行器源码。不要上传真实型号数据到公开仓库。

## 一条完整的首次使用路径

```bash
python -m comacbench validate packs/aviation-data-starter-v1
python -m comacbench calibrate packs/aviation-data-starter-v1 --out ./starter-calibration-01
python -m comacbench run packs/aviation-data-starter-v1 --agent examples/agents/reference.json --out ./starter-interface-01
```

第一步应没有 blocker；第二步应得到两项正例结果、四项负例结果且 `calibration_passed=true`；第三步应得到两项任务结果。**这些是需要在目标环境确认的成功标准，不是本指南宣称已完成的实测。** 校准未通过时先停止，不把环境错误当成模型能力问题。

用浏览器打开 `starter-interface-01/report.html`。无需启动网站服务。首先确认任务数，再找一条单位换算检查和一条来源关系检查；最后找到该次运行的结果文件及未覆盖范围。参考接口程序直接读取预置答案，其满分仅为接口自检。

## 这两题测的是什么

`data_units_01`：实现 `normalize_records`，检查长度单位、保留前导零的标识符、重复记录、缺失来源、非法数值以及输入不被修改。

`ontology_trace_01`：实现 `build_graph`，检查给定对象的关系类型、来源合并、缺失对象和无证据关系。它不要求从自然语言或工程文档中抽取知识。

两题均为公开、合成、函数级任务；每题七条测试片段。报告中沿用的 `physics` 字段在这里表示业务断言正确性，不是物理仿真。它们不测试真实 CSV/Excel 处理、真实企业本体构建或工程审查批准。

## 再连接真实 Agent

参考 [航空评测协议](aviation-quickstart.md) 配置 `my-agent.json`，至少核对以下契约：

- 使用 `comacbench.agent.v1`；设置可辨认的 `name`、`revision` 和 argv 数组 `command`。
- `revision_files` 锁定 wrapper 源码及影响行为的文件；通过 `env` 声明环境变量名称，不写密钥值。
- 每次 stdin 读一个任务 JSON；stdout 只写一个响应 JSON，其 `task_id` 必须原样返回；调试日志去 stderr。

```bash
python -m comacbench run packs/aviation-data-starter-v1 --agent ./my-agent.json --out ./starter-agent-01
```

现在报告才是该 Agent 的任务结果。使用参考样例和真实 Agent 的不同目录，不覆盖、不混合。改变模型、提示词、工具配置或运行器后，应冻结新身份并使用新目录。

## 遇到问题时如何判断

| 现象 | 先做什么 |
| --- | --- |
| 找不到 `runners` 或其他模块 | 回到完整源码根目录；确认使用维护者准备的解释器和依赖 |
| validate 通过但 run 失败 | 静态材料检查不是环境检查；查看运行错误与日志，不直接归为 Agent 答错 |
| 校准失败 | 核对正例结果是否齐全，负例是否由正确原因失败；基础设施崩溃不能算负例通过 |
| reference 自检成功，真实 Agent 失败 | 先查协议、stdout 内容和身份，再查业务检查；不要调松断言来掩盖失败 |
| 输出目录已有内容或 identity mismatch | 用新 `--out`；只有同身份中断任务才使用 `--resume` |
| 模型拿到满分 | 仅解释为这两个公开函数任务通过，不能据此宣布工程生产可用 |

## 一次真实用户验收

请三位未参与开发的工程师，在环境已准备好的前提下独立完成首次使用；记录完成时间、求助次数、失败位置，并请其解释“校准满分与模型满分的区别”“这两题没有测什么”。随后让其找到一条失败检查及对应产物。任何一项解释不清，都应继续优化入口，而不是增加首页图表。
