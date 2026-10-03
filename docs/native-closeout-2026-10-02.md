# PR #8 收口实测记录

本轮按独立审阅 `5392352453` 收口。起点 `ee6872ea26c9cc3e7605481b8f422a0c6bc6ad1a`，仍在 `codex/native-calibration-local-20261002`，没有合并或切换默认分支。
受限复测最终源码 `8a46c97b812ff09213728747c61af59aa3d743be`；其后的提交只更新 CI 源码导出、导出专项与交付文档，受试入口和物理引擎不变。

## 实际结果

| 项目 | 结果 |
| --- | --- |
| 公开操作面 | 固定会话 workbench 工具；只投影当前输入、状态、依赖、结果和完整动作合同 |
| 禁止访问 | 同一 DSH 注册表九项探测均拒绝；内部 session、测试、参考、验收、相邻结果、命令/脚本/目录/网页读取不可执行 |
| 宿主边界专项 | 禁止实现执行次数 0；后加 allow 不能覆盖 guard；JSON 字符串拒绝、对象参数通过；启动 observe 可用 |
| Python 专项 | 124 项：123 passed、1 native opt-in skipped；不是全仓测试 |
| 历史复读 | 10 份 session、27 个归档 job；按各自 77dee318 / 997ef4ea / df96c27f 引擎复读与旧 report.json 完全一致，0 新求解、0 版本探测 |
| 新原生结果 | 修复后 Agent 产生 3 个新 job；独立 INP/DAT/日志解析通过，物理阈值未改 |
| 报告文件链接 | 6 份主要报告共 181 个链接的本地文件存在、JSON 可解析、产物摘要匹配；仅静态文件检查 |
| 实际浏览器操作 | BLOCKED：Chrome 工具策略拒绝 file://；未改协议、换浏览器或绕过 |

求解输入、原始解析、阈值、四模块 engine_identity 和场景文件与审阅起点逐字节一致。报告改动不要求重跑历史 27 个 job；新增 3 次求解全部来自新受试轨迹。

## 两次公开开发记录均保留

1. `restricted-trial-01`，源码 `dab5d306`：7 次工具调用、0 受理行动、0 求解、complete=false。未明确 object 类型的参数合同使模型把 JSON 序列化为字符串；网关拒绝全部请求。属于宿主接口失败，不作模型能力评分。
2. 用户明确回复“允许追加一次修复后复测”后，`restricted-trial-02` 使用同一既有配置 `DSH 0.2.0-rc.2 / zai-coding-cn / glm-4.7`、新 session、源码 `8a46c97b`。19 次模型工具调用、17 次受理行动、3 次原生求解；两次过早 submit 以 mandatory_changes_remaining 拒绝并消耗行动预算。最终 complete=true、claim=needs_review。

新轨迹按主机控制及记录得出 `protocol_conformance=conformant`、`reference_exposure=not_observed_in_recorded_run`、`score_admissible=true`。
这里的准入**仅指同题公开开发记录**，不是未见题、隐藏测试、无历史暴露或泛化成绩；`unseen_generalization_score_admissible=false`。身份来自运行时配置，不是模型服务端认证。
旧 Agent 的 48 工具 / 16 行动 / 3 求解记录原样保留；独立附录标记 `nonconformant / observed / false`，以原工具轨迹第 11、13、66、67 行为证据，不采用其自述。

基线 limit / service 分别求解；载荷变更后仅重算 limit；限值变更后零新增 solve。
service 位移 -0.3811745 mm、反力约 +100.00001 N；初始 limit -0.4574094 mm、约 +120.00003 N；变更后 limit -0.5336443 mm、约 +140.00003 N。
0.45 mm 新限值下 limit 不满足，因此 needs_review 是正确结论，不是求解失败。

环境预算保持 32 行动、6 求解、每次 120 秒；宿主另限 96 工具调用（包含一次入口探测）、64 prompt assembly、30 分钟。没有读凭据、安装、换模型或扩大额度；没有批跑择优。
三次宿主预检都在模型调用前主动终止，退出 1 / PREFLIGHT_COMPLETE_NO_MODEL，0 模型任务、0 求解；不能计为受试成绩。

## 仍未通过的项目

本机为 macOS 26.5.2 (25F84)，Chrome 154.0.8037.95。reference 的实际 file:// 打开被浏览器工具安全策略拒绝；随后不再尝试相同策略下的 stale、false-ready、Agent 导航或下载。四份 file:// 地址及逐项 BLOCKED 均在 browser-acceptance.json。
本轮没有取得人工打开/点击确认，静态链接存在不等于真实浏览器打开或下载成功。
Windows 原生执行/超时、Windows 浏览器、wheel、离线部署、完整仓库全量测试、独立新实例和工程批准均未验证。

证据目录：`/Users/Zhuanz/Downloads/COMACBench-Closeout-2026-10-02`。
交付 ZIP：`/Users/Zhuanz/Downloads/COMACBench-PR8-Closeout-Evidence-2026-10-02.zip`。
包含两次受试轨迹、修复前后源码、权限探测、原始专项日志、全部相关求解产物、历史原引擎复读、旧记录独立审阅附录、浏览器受阻及授权记录。原 ZIP 与旧现场保持不变。

## CI 导出修复

首次推送的 Workbench 四个矩阵 job 因源码导出遗漏 scripts/dsh_public_boundary.mjs 而失败；原始 CI 日志已保留。补入 scripts 子树及必需文件检查，扩展既有导出专项验证 wrapper 存在，继续排除 Windows 受阻的研究资产。此修复不改运行时、物理逻辑或模型试验；无需新增原生/模型运行。最终线上结论见证据包 ci-final.json。
