# T3 · 数据桥选型决策

- Label: `wayfinder:grilling`（HITL） · Status: open · Blocked by: T9

## Question

基于 T1 的能力矩阵，拍板工作台页的数据桥。T1 已实证候选与粗评（[研究报告 §候选数据桥方案](../research/T1-dsh-data-bridge.md)）：

1. **研究推荐**：host 插件挂 `/comac/*` prefix 路由活读仓库吐 JSON + client plugin fetch——四标准全优，本机 dsh-comfyui 为先例；风险集中在 client bundle 打包格式（T9 验证中）
2. 备选：Typert Remote Service + 通用 rpc.call——走 Gateway trusted-host 围栏更安全，但自定义 namespace 组合未实证、与 dsh 内部包版本耦合
3. 降级：纯 host 插件，不做内嵌页（不满足载体决策，仅兜底记录）

选型标准排序：① 薄代理（不复制判分逻辑）② 活读时延可接受 ③ 内网可移植 ④ 实现面最小。

若 T9 证明打包不可行：在此票内同时裁决 fallback（Typert / 独立本地 app / 静态快照站），并回写地图 Decisions so far 的载体形态项。

## Resolution

（待解）
