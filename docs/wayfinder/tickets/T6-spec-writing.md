# T6 · 规格书 v1 撰写

- Label: `wayfinder:task` · Status: **closed**（2026-08-23，规格书 v1 落盘） · Blocked by: —

## Question

汇齐 T2–T5 的决议，撰写《COMACBench 工作台 UI 设计规格书》v1，章节即地图 Decisions so far 的五项交付物：

1. 决策论证（要不要做、为什么内嵌 DSH、为什么只读——含被否决备选的记录）
2. 信息架构 + 五页线框级描述（对比矩阵 / 基准详情 / 单题下钻 / 轻总览 / 运行监控简版：每页什么数据、什么交互、什么空态/加载态/错误态）
3. 数据契约（result.json / registry.yaml / run_manifest → 视图 JSON 的映射 schema；快照格式按 T4）
4. 技术选型与打包方案（桥按 T3、栈按 T5、内网移植方案按 T2 + 本地化校验清单）
5. 分期路线（v1 → 后续，每期验收标准；含 fog 区四条目的归位处置）

落点建议：`docs/specs/workbench-ui-v1.md`（撰写时确认）。本票是目的地本身——完成即地图走通。

## Resolution

《COMACBench 工作台 UI 设计规格书》v1 落盘：**`docs/specs/workbench-ui-v1.md`**。

- 五章齐备：决策论证（含被否决备选全记录）/ 信息架构与五页线框（每页数据来源=端点、交互、空/载/错三态）/ 数据契约（统一 result 信封 + 实测 failure_mode 词表 + 9 端点表 + ViewJSON schema + 快照文件 schema）/ 技术选型与打包（两包一逻辑架构、tsdown 配方、ECharts+宿主令牌、内网章 T8 占位含方案 B）/ 分期路线（v1 验收 7 条可测标准 + v1.1 + v2 fog 归位 + 风险登记册）
- 全部决议（T1/T2/T3/T4/T5/T9）已内化为规格条款，每条可溯源到地图 Decisions so far
- 内网移植章以 T8 占位（Q2 一票否决级），方案 B（静态壳）已预设计——T8 回答不阻塞实现动工
- 撰写时补齐的实证：五类 adapter result 信封同构验证、全库 failure_mode 频次扫描、九维度→registry 映射、registry entry 全字段

地图目的地（设计规格书）已抵达。剩余票：T7 可点击原型（后置验证"直观好看"）、T8 内网人工确认（喂 v1.1）。
