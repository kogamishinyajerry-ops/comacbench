# PR #8 准入复核修复附录（2026-10-03）

针对 review 5393976144，起点为 `640a4b869f93862bdb783fb62a291006f5612498`。本轮仅修复准入审计、逐轮公开输入边界、报告冲突显示及相关测试。四个物理引擎文件、场景与 3% / 1e-5 / 1e-6 阈值均未改变。旧校准结论保留，没有重跑历史 27 个 job。

## 复现与修复

原始 reviewer 7 项回归：2 通过、5 断言失败。原始 `probe_prompt_hook.mjs --require-safe` 退出 1，服务替身允许后续正文替换及追加 section；原脚本、全部输出均归档。这不证明旧真实 DSH 已泄露资料。

新审计在建索引前检查每类 callId 唯一性；逐条连接模型请求/结果、宿主结果与 broker。模型结果必须在请求之后、broker 必须在宿主结果之前。无 broker 仅允许可识别的工具参数验证或 guard 拒绝；有 broker 的进程失败单独记录。环境受理的失败动作与成功动作一样逐项对齐 events，保留 `task_action_rejected`，不伪造回执。损坏的 JSON stdout 即使被包装成安全错误也不能获得准入。

每条实际响应按操作作正向验证：observe 与受理动作的 result/observation 必须等于当时公开状态的重放投影，包括嵌套字段；read_native 只允许当前 job 的白名单文件及原始文本，并核对归档身份。没有扫描“0.45”等数字或敏感关键词的规则。复读使用归档 payload，不启动进程或求解。JSON/JSONL 拒绝重复键、非有限值、错误结构、截断和过大记录；保留具体原因。

## 公开输入合同 v2

`comacbench/public_input_v2.json` 是冻结的自包含 system、用户入口和完整工具 schema 合同；其 SHA256 在宿主和审计代码中固定为 `d6b1d694ed9c92093b9b022b1dcc208b5bf046b2608cdbaee0319052008b9271`。该合同不含未来阶段、参考策略或预期行动数。工具 observe 返回完整操作字段、路径语义、当前输入和错误反馈。

当前安装 DSH 的 Cordis waterfall 按外层到内层执行；SystemPrompt 在 waterfall 后恢复 complete section 并清空已抑制 context。v2 同时检查 cooperative transform、最终 assemble 返回值，以及所有 llm/stream hook 之后的共同 adapterStream 入口（prepared 与普通调用均经过这里）。最终 sections/contexts/完整 schemas、实际消息及由实际内容计算的摘要被记录，独立 Python 审计与冻结合同核对。版本不匹配、缺逐轮正文、未记录工具反馈或入口改变均不追认。

宿主包装仅针对已核验安装包，锁定五个相关 DSH 模块的源码摘要；升级后须重新验证。它是可信本地宿主控制，不能对抗管理员、安装包或提供方。不是 OS 沙箱、签名认证或模型服务端输入证明。

`--preflight` 使用实际 headless 启动及 Agent loop。预检专用的 prepareCall 替身不访问模型提供方，在最终派发验证并记录实际输入后抛出 `PREFLIGHT_COMPLETE_NO_MODEL`；退出 1 是预期停止，不能算受试模型完成任务。其启动版本确认使用本机已有 CalculiX，未求解。

## 验收范围与旧记录

- Python 原有 124 项专项保留；加 reviewer 7 项和补充 19 项，共 150 项，149 通过、1 native opt-in 跳过。另 4 项 campaign 源码导出通过。
- JS 服务替身：五项提示词回调控制通过；仅是服务替身。
- 安装 DSH 服务：真实 SystemPrompt、Cordis、Tools 与 LlmRuntime；11 种正常/后续 section/context/schema/最终请求变更情形通过，非法路径到达终端 adapter 次数为 0。终端 adapter 与任务 body 为无网络测试替身；不能算模型运行或原生物理证据。另保留既有九项权限拒绝及工具预算专项。
- 实际 DSH headless：第一次发现公开用户入口多余换行，被拒绝并保留；修复输入字节后第二次在最终派发处按预期停止。跨平台修复后又在新目录验证最终插件。全部 0 模型调用、0 环境行动、0 原生 job。
- 旧 restricted-trial-01 与 02 在各自原源码、原 plugin/gateway 摘要下复读。第一次旧审计对字符串请求抛 AttributeError，保留失败；新附录明确 unknown。第二次仍为 19 工具调用、17 行动、3 个历史 job、complete=true / needs_review；旧审计曾给出 true，新附录为 unknown / unknown / false，原因是 v1 没有逐轮实际模型输入。没有改写旧报告或替换其 hash。
- 更早公开开发记录的已确认协议偏差与参考暴露仍有效，不将其提升为合规。
- 首屏保留准入字段，unknown 或冲突不得显示核对通过。任务完成与成绩准入独立。

## 未完成与后续固定方案

没有新真实 Agent 复测。旧 v1 轨迹缺少的实际逐轮输入无法补写；要取得 v2 真实受试证据仍需用户另行授权一次运行。方案保持既有 DSH / zai-coding-cn / glm-4.7，不挑模型、不批跑、不扩大额度：32 环境行动、6 次求解、每次 120 秒、96 工具调用、64 次组装/派发、30 分钟宿主上限，一次新 session，失败同样归档。该方案不是执行授权。

本机 Chrome 的 file:// 打开被工具安全策略拒绝，已停止。没有换 HTTP、alternate surface 或 set_content；报告 JSON/INP/DAT/日志的实际点击仍 BLOCKED。Windows 浏览器/原生、完整仓库、wheel、内网部署及工程批准未验证。

新交付 ZIP 内包含上轮 `COMACBench-PR8-Closeout-Evidence-2026-10-02.zip` 原件（SHA256 `7b6446e447d01c6676dbfb8806aa60b899b4bbfcc9611c2fec82c240ffeb7fe3`），以及本轮复现、无模型专项、失败现场、复读附录、源码和差异。旧 Native-Acceptance 包不是该原件的替代品。

## Windows CI 修复补充

首次推送 `366764872d5a917daf4b07a49538db5cd51f81b8` 的 Ubuntu 两项通过，Windows 两项失败，原始日志保留。Git 的 CRLF 源码导出改变了 JSON 合同的传输换行；Python read_native 文本读取则会规范化 CRLF，不能将返回字符串再编码后冒充原始 DAT 字节。合同 SHA256 现明确定义为 UTF-8/LF 内容摘要，只归一化 JSON 传输 CRLF，不改变字符串转义或正文。原生文本审计通过 session 参数读取当前归档文件，先按原字节核对 receipt，再用与网关相同的换行/UTF-8 replacement 规则比较返回值；缺原始 session 路径保持 unknown。新增 CRLF 合同变更负例和原始文本解码测试，未放宽物理阈值。

补充按冻结完整工具 schema 核对 broker 入口参数，拒绝将应在参数校验层终止的请求伪装成已进入 broker；网关自身的合法字段组合拒绝仍保留为 gateway response。

逐轮覆盖还按 DSH step_start、一次 startup assembly 和每次运行 assembly 对齐；每个运行 assembly 都必须有实际 model_input，不能删掉后续输入记录后只凭第一份干净正文准入。重试可对应同一 assembly 的多个输入记录。
