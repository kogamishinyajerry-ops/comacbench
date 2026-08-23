# T5 · 图表库与视觉系统选型

- Label: `wayfinder:grilling`（HITL，可带研究子代理先行摸底） · Status: **closed**（2026-08-23 实测+grilling 拍板） · Blocked by: —

## Question

深色高密度工程台的实现栈：

1. 图表库：雷达图 + 热力图 + 分布图第一公民；必须中文标注清晰、可完全本地化打包（无运行时外部请求）、深色主题原生或易定制。候选摸底：ECharts / visx / D3 直用 / uPlot 等。
2. UI 框架与样式方案：与 T3 数据桥选型的耦合点（若桥决定了前端宿主，框架随之收敛）。
3. 设计令牌：密度基准（字号/行高/间距档位）、深色色板、状态色（gate pass/fail、status 流转五色）、中文/等宽数字字体栈（系统字体优先，为内网铺路）。

约束（已决）：深色高密度；雷达图/热力图第一公民；中文标注清晰度是硬指标；依赖可完全本地化。

## Resolution

三项裁决（全部基于 `.attic/t5-chart-lab/` 实测 + DSH 宿主事实，见 [研究报告](../research/T5-chart-visual-stack.md)）：

1. **图表库 = ECharts 按需**（echarts/core + Radar/Heatmap/Bar + CanvasRenderer）：实测 554KB / **184KB gzip**，bundle 本地磁盘加载不走网络、代价≈0；雷达/热力开箱质量 + 内置 dark 主题 + 中文生态成熟 + tooltip/图例免费。canvas 不吃 CSS 变量的缺口用启动时 `getComputedStyle` 读 `--dsw-static-*` 色阶构造 JS 主题补（~20 行，随宿主明暗切换重建）。visx（14.5KB、SVG 令牌原生）记为 fallback——若 ECharts 主题映射效果不合格再启用。
2. **视觉令牌 = 继承宿主 `--dsw-*` 体系**：static 色阶 → alias 语义层 + `--dsw-font-*` 字号梯度 + 中文字体栈 + `.light/.dark` 双主题全部现成；不自造调色板。对冲：规格书记"令牌名随 DSH 版本漂移"为已知风险（低频，升级时跑视觉冒烟）。
3. **样式 = 命名空间 CSS 字符串注入**：`<style>` 注入 `.comac-wb-` 前缀 CSS，内部直用 `var(--dsw-*)`；零依赖、契合 factory 单文件 bundle 契约（loader 只认 client.js，CSS 必须内联）、前缀隔离不污染宿主。

**随票生效的实现纪律**（实验室踩坑，进 T6）：tsdown 默认 externalize dependencies——必须显式 `alwaysBundle: /^(?!react($|\/))/`；`clean:false` 下构建失败会留陈旧产物，构建脚本必须 fail-loud（检查退出码）。
