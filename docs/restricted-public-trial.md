# 维护者：受限公开试验与成绩准入

受试可读合同是 `docs/public-workbench-contract.md` 与工具 `observe` 返回值。本文件、源码、测试、参考程序、完整 session 及相邻结果不进入受试工具面。

`scripts/run_restricted_trial.py` 使用现有 DSH headless 配置和现有 CalculiX 2.23；不读取或打印用户配置/凭据，不安装依赖，不设置或重新选择模型。
本轮入口断言既有 `zai-coding-cn/glm-4.7`；改变时停止，不回退其他模型。只有权限边界覆盖：新 headless 会话、空工作目录、关闭自动读取指令/技能及辅助标题模型。

DSH 的全局执行 guard 拒绝除 `workbench` 之外的所有工具；在 `agent/created` 串行钩子内应用 scope allowlist，固定 native presentation，拒绝脚本转发入口。
完整公开 system prompt 与 runtime-context suppression 防止自动上下文载入维护者材料；每次组装及最终派发都按冻结 v2 合同核对实际 sections、context、完整 schema 和用户入口，记录实际正文；详见 [v2 修复附录](admission-audit-v2-2026-10-03.md)。
固定 broker 子进程仅执行 `comacbench.workbench_public`，参数由宿主绑定；受试输入只能是数据。每次 observe/action 返回正向筛选的当前信息，屏蔽 phase 列表/数量和内部 manifest。
所有受理行动由原引擎记录，原生文件完整留存。原引擎的输入、阈值、解析和身份计算不改。

这是**可信宿主中的工具能力边界**，不是独立 OS 用户/容器，不防恶意宿主、维护者改档或模型服务端训练资料污染。Python 求解进程的原 sandboxed=false 仍保留；不能把工具限制说成操作系统隔离或独立模型认证。

启动在同一个受试 Agent 的工具注册表执行九项禁止访问探测，失败便阻止模型运行。独立 Node 专项还证明后加的 allow policy 不能覆盖 guard，以及禁止工具实现未被调用。
`--preflight` 建立空基础设施会话，使用预检专用 prepareCall 替身阻止提供方访问，穿过实际 headless Agent loop 至最终派发检查，随后以 `PREFLIGHT_COMPLETE_NO_MODEL` 终止；它不发送任务给模型、不启动求解，不计为受试尝试。保留其非零退出记录。

环境预算固定 32 行动、6 次求解、每次 120 秒；另固定 96 工具调用、64 次 prompt assembly 与 30 分钟宿主期限，不能因失败自动放宽。
只启动一次真实受试任务，失败也归档。模型/工具 NDJSON、主机所有工具结果、broker 请求与反馈、受理行动必须相互核对。参考程序不能充当受试模型。

`python -m comacbench.workbench_admission --session SESSION --audit AUDIT --out NEW_REPORT` 复读原始 session 后审计主机记录。
默认 `protocol_conformance=unknown`、`reference_exposure=unknown`、`score_admissible=false`；未知、缺失、截断、不匹配和未关闭的记录均不能获得准入。
只有来源绑定、每轮实际输入、工具调用/结果与环境行动逐项核对通过才准入同题公开开发记录；`unseen_generalization_score_admissible` 永远 false。
准入不是任务完成判断，也不改既有物理分数、阈值或结果。Agent 自述不是合规证据。

旧报告/会话不得改写；另生成审阅附录，指出实际读过的内部文件和参考材料。复读必须用与 session 匹配的四模块原引擎，不能改 engine_sha256 来迁就新版。
仅报告和访问控制发生变化时复读归档与运行受影响专项；只有原生输入、求解、物理解析或阈值变化才在新目录增加对应原生回归。

审计合同为 `comacbench.public-boundary.v2`；v1 缺少实际逐轮输入，不能追认。旧记录使用原源码验证身份，再生成独立 unknown 附录，不替换其 plugin/gateway 摘要。
