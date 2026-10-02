# 公开工作台操作合同

这是已经公开的固定梁工作包。开始时调用 `workbench({"request":{"op":"observe"}})`。
完整合同与**当前**输入通过返回的 `observation.contract`、`sources`、`instruction` 提供；后续反馈同样只提供当前状态。
只使用这个工具；无法完成时保留失败并说明。

`request` 是 JSON 对象，`op` 是动作选择字段；每种动作只接受下列字段：

| op | 字段 | 语义 |
| --- | --- | --- |
| observe | op | 读取当前输入、依赖摘要、状态、已生成产物和预算余量 |
| solve | op, target | 为 solution 节点运行固定原生模型，得到待检查的结果 |
| check | op, target | 检查已有产物；缺失、陈旧或内容错误会拒绝 |
| put | op, target, basis, payload | 仅可写 review；basis 原样复制当前 dependencies.review |
| advance | op | 当前各产物验证后申请下一份工作包；没有后续工作包时返回 no_next_phase |
| submit | op, claim | 提交与已验证 review 相同的 claim；若还有必需变更则返回错误 |
| read_native | op, target, name | 读取当前 solution 节点已生成的 INP、DAT 或日志等允许文件 |

`target` 是当前 `statuses` 中的节点名，不是路径。工具由宿主绑定一个会话；不接受路径、session ID、命令、程序、任意 INP 或其他会话。
`read_native.name` 必须完整匹配 `contract.native_files` 中一个文件名；不允许目录、绝对路径、路径穿越或相邻结果。

`payload` 字段为 `cases`、`claim`、`requirement_revision`。`requirement_revision` 使用当前要求版本。
`cases` 每个工况一项，含 `point`、数值 `uy_mm`、数值 `rfy_n`、布尔 `meets_requirement`。
工况名由 `solution_` 后的部分得到；有符号位移与反力来自该节点原生 `payload.qoi`。
`meets_requirement` 为 `abs(uy_mm) <= 当前 sources.requirement.max_tip_mm`。
所有工况都满足时 claim 为 `requirements_met`，否则为 `needs_review`。

反馈为 `result={ok,code,...}`。网关格式或路径拒绝发生在环境受理前；被环境受理的行动即使失败也消耗行动预算。
`observe` 与 `read_native` 不消耗环境行动或求解预算，但仍记录为工具调用。预算上限与剩余额度由公开响应提供。
错误不会被当作成功；缺失/陈旧证据、错误内容、虚报结论、超预算与不可推进均保留反馈。

这份合同不提供维护者材料或参考策略。物理适用范围仅为该固定线性静力梁，不构成工程批准；同题公开开发记录不能证明未见题、隐藏测试或泛化能力。
