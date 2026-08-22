# T8 · 内网 DSH 形态人工确认

- Label: `wayfinder:task`（HITL——只有人能答，agent 不得代答） · Status: open · Blocked by: —（阻塞 T6）

## Question

T2 研究证明：内网 JS 运行时在全仓库近零证据，唯一线索是 `env-matrix.md` L43 的"内网 DeepSeek Harness 代理运行时"。以下 7 问需由人（问验收人/IT，或凭本人了解）确认，答案写回本票 Resolution：

| # | 问题 | 影响 |
| --- | --- | --- |
| Q1 | 内网机器是否装有 node.js？版本？可否手工导入 node 单二进制发行包？ | DSH 及前端构建链在内网的存在前提 |
| **Q2** | **"内网 DSH 代理运行时"的确切形态？谁部署？含不含 web GUI 层？** | **若不含 web GUI，"DSH GUI 内嵌页"载体在内网落空——本图最大风险** |
| Q3 | 内网是否允许本机 Web 服务（loopback 监听）？端口/进程白名单？ | 任何本地服务形态的前提 |
| Q4 | 内网浏览器内核/版本？组策略（JS、DevTools、WebSocket、本地文件）？ | 前端兼容性底线（注：DSH GUI 自身传输 = HTTP-up/WebSocket-down——若内网已有 DSH web GUI 在跑，说明其传输层已通，Q4 对"页面能不能用"大半自解，只剩内核版本问题） |
| Q5 | 内网 DSH 的模型 provider 是什么（本地网关？）？ | 若数据桥走 agent 工具，决定内网侧桥可行性 |
| Q6 | npm 包有无与 wheel 同等的"手工批量导入"通道？内部 npm 镜像计划？ | 依赖本地化流程形态（T2 已建议绕过：自包含 dist 拷目录） |
| Q7 | 内网验收人对"拷目录就能跑"制品的接受度？ | 打包形态：绿色目录 vs 安装脚本 |

优先级：Q2 一票否决级；Q1/Q3/Q4 选型级；Q5–Q7 流程级。允许部分确认（答几条写几条）。

完整背景与证据：[T2 研究报告](../research/T2-intranet-runtime.md) §1.4。

## Resolution

（待人答）
