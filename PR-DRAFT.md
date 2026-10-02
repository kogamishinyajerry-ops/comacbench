# 原生固定梁工作台：修复准入逐项审计与逐轮公开输入边界

修复 review 5393976144 复现的错误放行：重复 broker 回执不再能顶替缺失调用；每条 Agent 可见响应都按当前公开状态验证；重复 JSON key、截断和非有限值不能获得准入。正常任务动作失败仍保留为任务失败，网关前拒绝和 broker 失败另行记录。

冻结公开输入合同 v2，并检查完整 sections、contexts、工具 schema、公开用户入口及最终 DSH 派发消息。每轮记录实际内容及摘要；旧 v1 记录缺少逐轮正文时为 unknown，不补写常量或改旧身份追认。报告首屏区分任务完成与成绩准入，冲突或未知不能显示通过。

PR 保持 Draft，叠在 PR #7 的 `review/change-workbench-product-scope-20261002` / `59f3dbe659b750964f5a81c99eb619352657c2ae`，不自动合并。四个物理引擎文件与场景、3% / 1e-5 / 1e-6 阈值未变；固定梁既有本机校准结论保留。

验证：

- 原 reviewer 7 项：修复前 2 pass / 5 fail；修复后 7 pass。原 JS 服务替身 `--require-safe` 失败现场保留。
- 原有 124 项专项加 24 项回归：148 tests，147 pass、1 native opt-in skip；另 4 项源码导出 pass。
- JS 服务替身五项控制、安装 DSH 服务的 11 类组装/派发变更控制、既有权限/预算专项通过。真实服务测试使用无网络 adapter 和任务 body 替身，不是模型成绩。
- 实际 DSH headless 无模型预检：发现入口换行不符后修复；最终在派发验证处 `PREFLIGHT_COMPLETE_NO_MODEL` 停止。失败与成功停止记录都保留，0 模型调用、0 行动、0 新求解。
- 两份 closeout 轨迹按原引擎与原入口复读；旧成功轨迹保持 complete=true / needs_review、17 行动、3 个归档 job。新增附录准入为 unknown / unknown / false，旧报告原样保留。没有重跑历史 27 个 job。

[详细修复与验收附录](docs/admission-audit-v2-2026-10-03.md) 包含已知限制和固定预算待授权方案。本轮没有再次运行付费模型。要取得 v2 的真实受试轨迹仍需另行授权一次同配置运行；不宣称独立新任务、模型比较、未见题或跨软件泛化。

证据 ZIP 包含新源码、差异、全部失败/控制/专项原始日志、新准入附录，以及上轮 `COMACBench-PR8-Closeout-Evidence-2026-10-02.zip` 原件。可信本地宿主边界不等于 OS 隔离或对抗管理员。Chrome file:// 打开被工具安全策略拒绝，实际 JSON/INP/DAT/日志链接点击仍 BLOCKED；Windows、完整仓库、wheel、内网部署及工程批准未验证。

首次 Windows CI 失败已定位并保留日志：修复合同 CRLF 传输身份与原始文本解码核对，新增两项专项；不以规范化后的文本摘要替代原始产物字节身份。
