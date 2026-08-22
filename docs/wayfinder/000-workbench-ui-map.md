# 地图：COMACBench 工作台 UI（wayfinder:map）

- Label: `wayfinder:map` · Tracker: local-markdown（仓库无 issue tracker；票据见 `tickets/`，研究成果见 `research/`）
- Created: 2026-08-22（charting session）

## Destination

一份《COMACBench 工作台 UI 设计规格书》：以评测运营（Jerry）为第一受众、核心心智"结果说明什么"（date×provider×benchmark 交叉对比 + gate 失败下钻）的 **DSH GUI 内嵌只读工作台**。规格书含"要不要做"的决策论证、信息架构+线框、数据契约、技术选型与打包（内网移植）方案、分期路线。动手实现不在这张图里。

## Notes

- 领域：民机设计 Benchmark Harness（38 基准 registry / 五类 adapter / results/<id>/<date>/<provider>/ 落盘结构 / M0–M4 里程碑）。
- 每 session 应consult的技能：`eng-grilling`（HITL 决策票）、`eng-domain-modeling`（词汇表 CONTEXT.md）、`eng-codebase-design`（数据契约 seam 设计时）。
-  standing preferences（全部来自已决项，见下）：
  - **纯只读**：UI 零写路径；起跑/重跑留在 comac_run / CLI，UI 至多给"复制重跑命令"。
  - **本地化硬规矩**：任何依赖必须可完全本地化打包，禁止运行时外部请求（字体/CDN/遥测）。
  - **薄代理延伸**：UI 数据层只读 result.json / registry.yaml / run_manifest，绝不复制判分逻辑。
  - **深色高密度工程台**：雷达图/热力图第一公民；中文标注清晰度是硬指标。
- 关键事实（charting 已查）：19 基准、~80 个 date×provider 组合——全量结果一个 JSON 快照装得下；已有静态雷达图先例 `report/2026-08-21-coverage-assessment/radar_*.png`；仓库零前端积累。
- 约定（local-markdown tracker）：票据状态 `open / claimed(<谁>) / closed`；阻塞用 `Blocked by:` 体例；前沿 = open 且 Blocked-by 全 closed 且未 claimed 的票据。**除 research 票外，每 session 最多解一票。**

## Decisions so far

- 终点形态 = 设计规格书（含"要不要做"论证）；实现另起工程。
- 第一受众 = 评测运营（Jerry）；"好看"服务于一眼定位问题；评审视图后续作为只读子集衍生。
- 核心心智 = "结果说明什么"：交叉对比 + 失败下钻优先于运行监控与家底总览。
- 载体形态 = DSH GUI 内嵌页（用户决策，推翻独立 app 备选；可行性挂于 [T1 · DSH 内嵌页的数据桥](tickets/T1-dsh-data-bridge.md)）。
- 数据供给 = 分层：活读为主（缓存秒级）+ 一键导出里程碑自包含快照（可归档进 git）。
- 交互权限 = 纯只读；动作留 agent 工具与 CLI（密钥注入与幂等 resume 语义不进 UI）。
- 内网约束 = dev 先行 + 依赖可完全本地化硬规矩；内网运行时事实挂 [T2 · 内网前端运行时事实](tickets/T2-intranet-runtime.md)。
- v1 页面 = 对比矩阵 / 基准详情 / 单题下钻 / 轻量总览首页 / 运行监控简版，共五页。
- 视觉方向 = 深色高密度工程台（Linear/Vercel 气质），雷达图/热力图第一公民，中文标注硬指标。
- 规格书交付物 = 决策论证 + IA/线框 + 数据契约 + 技术选型与打包 + 分期路线；可点击原型后置。
- [T2 · 内网前端运行时事实](tickets/T2-intranet-runtime.md)：内网 JS 运行时全仓库近零证据（唯一线索 env-matrix L43"内网 DSH 代理运行时"）；pip 纪律已映射 npm，**推荐形态 = dev 打自包含静态 dist、内网拷目录**；4 层 20 条本地化校验清单草案 → [研究报告](research/T2-intranet-runtime.md)。暴露风险：内网 DSH 是否含 web GUI 未确认 → 见 T8。
- [T1 · DSH 内嵌页的数据桥](tickets/T1-dsh-data-bridge.md)：**能内嵌**。页面 = client plugin 注册进 `conversation.view` ViewMap；前端不能调 agent 工具；**推荐桥 = host 插件挂 `/comac/*` prefix JSON 路由活读仓库**（本机 dsh-comfyui 有实证先例），Typert Remote 备选；风险集中于 client bundle 打包格式（→ T9）、裸路由无鉴权、新增插件须重启 → [研究报告](research/T1-dsh-data-bridge.md)。

## Tickets（前沿快照，权威状态以票据文件为准）

| 票 | 类型 | 状态 | Blocked by |
| --- | --- | --- | --- |
| ~~[T1 · DSH 内嵌页的数据桥](tickets/T1-dsh-data-bridge.md)~~ | research (AFK) | **closed**（能内嵌；推荐 prefix 路由桥） | — |
| ~~[T2 · 内网前端运行时事实](tickets/T2-intranet-runtime.md)~~ | research (AFK) | **closed**（Resolution 已记） | — |
| [T4 · 快照格式与归档纪律](tickets/T4-snapshot-format.md) | grilling (HITL) | open | — |
| [T5 · 图表库与视觉系统选型](tickets/T5-chart-visual-stack.md) | grilling (HITL) | open | — |
| [T8 · 内网 DSH 形态人工确认](tickets/T8-intranet-dsh-shape.md) | task (HITL，7 问清单) | open | — |
| [T9 · client bundle 打包格式验证](tickets/T9-client-bundle-packaging.md) | task (AFK，hello-world 实证) | open | — |
| [T3 · 数据桥选型决策](tickets/T3-data-bridge-decision.md) | grilling (HITL) | open | T9 |
| [T6 · 规格书 v1 撰写](tickets/T6-spec-writing.md) | task | open | T3, T4, T5, T8 |
| [T7 · 可点击高保真原型](tickets/T7-clickable-prototype.md) | prototype (HITL) | open | T6 |

## Not yet specified

- **运行监控的"进度"语义**：是数 result 文件、解析日志尾，还是让 runner 落 progress.json（要改 runners/，是个真决策）——等 T6 信息架构成形后再切。
- **单题下钻的跨 adapter 渲染差异**：qa_grounded / code_exec / simulation_agent / field_prediction 的 result.json 形状差异多大、要不要分 adapter 渲染器——数据契约阶段实地看过才知道怎么切。
- **provider 扩容后的对比交互**：当前 2 个真实 LLM provider + stub/oracle；横向扩容后矩阵交互（ pinning、diff、归一化）长什么样。
- **评审只读视图**：第二受众（COMAC 评审）的衍生形态——可能只是里程碑快照的叙事化导出，也可能什么也不用做。

## Out of scope

- 从 UI 触发评测动作（起跑/重跑/管理）：已决纯只读，动作永留 agent/CLI。
- 完整运维台、用户系统、多租户、远程访问：这不是运维产品。
- 报告阅读器、registry/license 完整看板：v1 之外（前者已有 comac_report 工具，后者价值真实但可后置——若未来需要，随目的地重画新图）。
