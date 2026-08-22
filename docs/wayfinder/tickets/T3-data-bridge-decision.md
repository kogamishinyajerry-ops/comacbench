# T3 · 数据桥选型决策

- Label: `wayfinder:grilling`（HITL） · Status: **closed**（2026-08-23 grilling 拍板） · Blocked by: —

## Question

基于 T1 的能力矩阵，拍板工作台页的数据桥。T1 已实证候选与粗评（[研究报告 §候选数据桥方案](../research/T1-dsh-data-bridge.md)）：

1. **研究推荐**：host 插件挂 `/comac/*` prefix 路由活读仓库吐 JSON + client plugin fetch——四标准全优，本机 dsh-comfyui 为先例；风险集中在 client bundle 打包格式（T9 验证中）
2. 备选：Typert Remote Service + 通用 rpc.call——走 Gateway trusted-host 围栏更安全，但自定义 namespace 组合未实证、与 dsh 内部包版本耦合
3. 降级：纯 host 插件，不做内嵌页（不满足载体决策，仅兜底记录）

选型标准排序：① 薄代理（不复制判分逻辑）② 活读时延可接受 ③ 内网可移植 ④ 实现面最小。

若 T9 证明打包不可行：在此票内同时裁决 fallback（Typert / 独立本地 app / 静态快照站），并回写地图 Decisions so far 的载体形态项。

## Resolution

**定案：方案 1 —— host 插件挂 `/comac/*` prefix JSON 路由活读仓库 + client plugin fetch。** 三项裁决：

1. **主桥**：方案 1（T9 已端到端实证，四标准全优）。Typert Remote 记录为"未来暴露到非 loopback 时的升级路径"，现在不做；不并行验证。
2. **暴露面纪律**：handler 内置 loopback 检查（远端地址非 loopback → 403），不依赖部署记性；全部端点只读 GET；`/comac` 前缀独占。token 鉴权不做（UI 自己是唯一客户端，发给自已意义有限）。
3. **快照写路径**：导出只走脚本/CLI 落约定目录，UI 纯读（检测到快照存在才展示"快照模式"入口）；host 半保持零写，与"纯只读"决策严格一致。UI 导出按钮不做。

**随决议生效的边界声明**：① 端点清单归 T6 数据契约章，本票只定通道形态；② 工作台 host 半必须与 comac_* agent 工具共享同一数据读取层——comac_results 的"独立重算"逻辑不得在 UI 侧复写（薄代理原则延伸）；③ 双面孔件以包名/node_modules 形态挂载（T9 定论）。

证据链：[T1 研究报告](../research/T1-dsh-data-bridge.md)（能力矩阵+候选粗评）、[T9 研究报告](../research/T9-client-bundle-packaging.md)（方案 1 端到端实证）。
