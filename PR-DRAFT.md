# 原生 CalculiX 工作包：受限 Agent 入口与成绩准入

固定 C3D20 梁的两工况基线、载荷选择性重算和限值变化重验已完成本机校准。此次追加解决独立审阅 5392352453 指出的工具越界与报告准入缺口：受试 Agent 只能通过绑定一个 session 的工作台工具操作，报告首屏和 JSON 明确给出合规、参考暴露、成绩准入及原因；未知不默认合规。

PR 保持 Draft，叠在 `review/change-workbench-product-scope-20261002`；不自动合并。

## 变更

- 分开公开操作合同与维护者材料。固定宿主工具采用 typed object schema、当前信息投影、精确动作字段和文件白名单；不提供内部 session、未来阶段或参考答案。
- DSH 串行创建钩子安装工具 allowlist，全局执行 guard 拒绝文件、命令、脚本、网页与委派入口；禁用自动读取上下文。实际启动时核对当前模型、完整 prompt、工具 schema、禁止访问和可用 observe。
- 从主机控制记录、模型工具请求/结果与环境行动推导 `protocol_conformance`、`reference_exposure`、`score_admissible`。Agent 自述不能建立合规。旧证据不修改，以独立审阅附录补充结论。
- 报告增加原始产物直接链接，区分本机固定梁证据、冻结场景旧说明、其他平台部署与工程批准。
- 修复首次受限试验暴露的弱类型参数问题，新增字符串拒绝与真实入口预检；失败记录完整保留。

边界为可信 DSH 宿主中的工具能力限制，不是 OS 隔离、对抗管理员防篡改或模型服务端身份认证。物理引擎四文件与场景相对 `ee6872ea` 完全不变，3% / 1e-5 / 1e-6 阈值未改。

## 实际验证

- 最终受试源码 `8a46c97b812ff09213728747c61af59aa3d743be`；macOS 26.5.2、Python 3.12.13、既有 CalculiX 2.23。后续提交仅更新 CI 源码导出、导出专项和交付文档；受试运行时代码一致。
- 修复首次 CI 导出遗漏 wrapper 的问题：补入 scripts 子树、必需文件检查与导出断言；失败日志保留。
- 124 项工作台专项：123 passed、1 native opt-in skipped。DSH 权限专项通过，禁止工具实现执行次数为零，后加 allow policy 无法覆盖 guard。
- 10 份历史会话按原引擎复读通过，与原报告完全一致；27 个归档 job，0 新求解、0 版本探测。reference 15/3 complete=true/needs_review；stale 与 false-ready 继续被拒绝。
- 唯一初次复测失败：7 工具调用、0 行动、0 求解；JSON 字符串被网关拒绝，不能作模型能力成绩。
- 经用户明确追加一次授权，修复后同一既有 DSH/glm-4.7 配置：19 工具调用、17 行动（2 次过早提交被拒）、3 真实求解，complete=true、claim=needs_review。原始 INP/DAT/日志独立解析通过。基线 2 次、载荷变更 1 次、限值变更 0 次求解。
- 新记录主机审计通过：conformant / not_observed_in_recorded_run / score_admissible=true，仅准入同题公开开发记录；不是未见题、隐藏测试、无历史暴露或泛化成绩。旧 Agent 记录仍为 nonconformant / observed / false。
- 6 份主要报告、181 个本地文件链接的静态完整性通过。浏览器真实 file:// 操作仍 BLOCKED（Chrome 154.0.8037.95 工具策略拒绝），没有绕过或冒充人工验收。

## 证据与限制

完整记录见 [本轮收口](docs/native-closeout-2026-10-02.md)、[边界与审计](docs/restricted-public-trial.md)。
本机证据包 `COMACBench-PR8-Closeout-Evidence-2026-10-02.zip` 包含源码与差异、权限拦截、全部失败、两次工具轨迹、原始求解文件、原引擎复读、报告与浏览器 BLOCKED 记录；原始大体积证据未上传 GitHub。

Mac 人工 file:// 点击仍待确认；Windows 原生/浏览器、完整仓库测试、wheel、离线部署和工程批准均未验证。只支持可信本地、固定梁、线性静力的公开开发校准，不提供真实型号或内部数据，不改变既有分数，不把参考程序当模型。
