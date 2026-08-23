# COMACBench 工作台 UI 设计规格书 v1

- 状态：v1（wayfinder 地图 T6 产物）· **已实现并验收（2026-08-23，e2e 12/12 PASS + 守卫/数字抽核/主题跟随）** · 日期：2026-08-23
- 读者：实现者（agent 或人）、评审人
- 输入索引：决策与证据见 `docs/wayfinder/000-workbench-ui-map.md`（Decisions so far）及研究报 T1/T2/T5/T9（`docs/wayfinder/research/`）；本文只写**规格**，不复述论证过程
- 第一受众：评测运营（Jerry）；核心心智："结果说明什么"

---

## 1. 决策论证

### 1.1 问题：静态 markdown 报告的四个盲区

现状全部结果消费都走 `summary.md` / `comac_results` / `comac_report`。实测 19 基准 × 88 个 date×provider 组合、9728 个 result.json：

1. **交叉对比不可能**：想知道"glm 在哪些基准赢 minimax、输在哪"要人肉开 19 个目录对读；
2. **失败下钻断链**：gate 失败分布（全库实测 1047 起：missing_output 412 / code_not_executable 403 / simulation_failed 120 / non_physical_values 104 / …）只能在 summary 里看到计数，从"non_physical ×100"钻到具体是哪 100 题要开文件管理器；
3. **家底不透明**：38 项 registry 的 status/license/env 流转靠读 YAML；
4. **长跑无进度感**：小时级评测脱离起跑后只有日志文件可看。

交互式工作台恰好补这四个盲区——这是"要不要做"的肯定回答。

### 1.2 形态论证与被否决备选

| 备选 | 判决 | 理由 |
| --- | --- | --- |
| **DSH GUI 内嵌页（ViewMap 视图）** | ✅ 采纳 | 用户工作现场即 DSH；T1 实证可行（slot 机制 + webServer 路由），T9 端到端验证通过；零部署（装一次包，HMR 接管迭代） |
| 独立本地 Web app | ❌ | 多一个进程多一个端口；脱离工作现场；数据读取层要么复制要么起服务 |
| 纯静态站点生成器 | ❌ | 看不到在跑批；每次手动重建 |
| 纯 host 插件（无内嵌页，靠 agent 工具） | ❌ | 回到盲区本身；作为无 GUI 环境的降级保留（comac_* 工具永在） |
| Typert Remote 桥 | ❌（记档） | 自定义 namespace 组合未实证 + 与 dsh 内部包版本耦合；记为未来暴露非 loopback 时的升级路径 |

### 1.3 边界（非目标）

- **纯只读**：零写路径。起跑/重跑留 `comac_run` / CLI；UI 至多"复制重跑命令"（T3 决议）
- 快照**导出走脚本**，UI 只读快照文件（T3）
- v1 不做：报告阅读器（comac_report 已覆盖）、registry/license 完整看板、多用户、远程访问

---

## 2. 信息架构与页面规格

### 2.0 载体与导航

工作台 = `conversation.view` ViewMap 的**一个视图**（label「工作台」，对标 ui-trajectory）。视图内部自导航：

```
┌ 顶栏: [总览] [对比矩阵] [基准详情] [运行监控] ······ 数据模式指示(活读|快照<tag>)
│        面包屑出现在钻入时: 矩阵 › cfdllm.cfdquery › 2026-08-19/glm-4.6 › q005
└ 内容区（五页之一；单题下钻是矩阵/详情内的钻入面板，不占主导航位）
```

- **单题下钻**是第四"页"但以 drill-in 面板呈现（从矩阵/详情的任何 task 行点入，面包屑回溯）
- **数据模式指示**：活读（绿点 `results/ 实时`）或快照（琥珀点 `results/_snapshots/<tag>.json`）；快照模式下钻读当前盘并显示「时点差」警示条（T4）

### 2.1 总览页（轻量入口）

| 项 | 规格 |
| --- | --- |
| 数据 | `GET /comac/overview`（registry 计数 + 最近 10 runs + 最新快照名 + 里程碑进度） |
| 布局 | 上：家底计数条（status×N 的分段条：integrated 17 / staged / proposed / paused-env）；中：**九维度雷达图**（最新日期、可切 provider；维度=knowledge/coding/cad_geometry/cfd/structures/propulsion/flight_control/mdo_design/robustness_audit，映射自 registry 的基准分组）；下：最近运行表（registry_id/date/provider/gate 通过率/均分，点击进详情） |
| 交互 | 雷达切 provider（默认最新日期的全量 provider 并列）；最近运行行点击 → 基准详情页 |
| 状态 | 空（无 results）→ 引导文案「先跑 comac_run」；加载 → 骨架；错误 → 重试按钮 + 错误摘要 |

### 2.2 对比矩阵页（核心页）

| 项 | 规格 |
| --- | --- |
| 数据 | `GET /comac/matrix?date=<d>`（默认最新日期；行=基准，列=provider，格=该组合的聚合） |
| 布局 | 主体**热力图矩阵**（ECharts heatmap）：格值 = 均分（0–1），格上角小字 = gate 通过率；行按 registry tier/order 排序，冻结行头；缺数格显式画斜纹（不是留白） |
| 交互 | 行/列头点击排序；格 hover → tooltip（n_tasks、gate 分布、failure_mode top3）；格点击 → 该组合的基准详情页；列头 provider 点击 → 整列高亮对比；日期切换器（历史日期矩阵对比）；「复制重跑命令」入口在格 tooltip 内 |
| 状态 | 单日期无数据 / 组合缺失按斜纹处理；错误态同 2.1 |

### 2.3 基准详情页

| 项 | 规格 |
| --- | --- |
| 数据 | `GET /comac/bench/<registry_id>`（registry entry + 该基准全部 runs 聚合 + 可选 ?date&provider 定位） |
| 布局 | 头：registry 卡（status/tier/adapter/env_class/license_status/assets_revision/risks）；左：**历次运行轨迹**（date×provider 散点/折线，y=均分，点大小=n_tasks）；中：**gate 失败模式分布**（堆叠条形图，7 种 failure_mode 词表配色固定）；右：子分均值（physics/requirements/objective/robustness 四条，标注 applicability）；底：任务明细表（task_id/gate/failure_mode/score/子分/agent_s，支持按 gate 失败过滤） |
| 交互 | 轨迹点点击切 date×provider；失败模式条点击 → 过滤任务表；任务行点击 → 单题下钻 |
| 状态 | paused-env 基准 → 状态横幅（env_class 说明）；无 runs → registry 卡 + 空态引导 |

### 2.4 单题下钻（drill-in 面板）

| 项 | 规格 |
| --- | --- |
| 数据 | `GET /comac/task/<registry_id>/<date>/<provider>/<task_id>`（完整 result.json 信封） |
| 布局 | 左：**统一信封区**——gate 徽章（通过绿/失败红+failure_mode）、四子分条（带 applicability 注释）、score、timings（agent/setup/grade）、model_meta（provider/model/finish_reason/escalated）；右：**adapter 载荷渲染器**（按 adapter 分派）：qa_grounded→答案 vs 题面；code_exec→代码块（等宽字体+语法高亮配色走宿主 shiki 令牌）+ grade_details（cases_pass/steps）；simulation_agent→代码/算例文件树 + gate_failures 明细；field_prediction→prediction vs true 的 rel_err 表。底部：logs 折叠区 |
| 交互 | 面包屑回溯；「复制重跑命令（单题）」；快照模式警示条（读当前盘） |
| 状态 | result.json 缺失（快照时点后新增）→ 「时点差：此题在快照之后产生」占位 |

### 2.5 运行监控页（简版）

| 项 | 规格 |
| --- | --- |
| 数据 | `GET /comac/runstatus`（与 comac_run_status 同一读取层：进程存活 + result 计数增长 + 日志尾 20 行） |
| 布局 | 在跑批卡片列表（registry_id/provider/已落 result 数 ÷ n_tasks 估算进度/最近日志尾）；无在跑 → 显示最近完成 3 组 + 「起跑请回会话用 comac_run」提示 |
| 交互 | 5s 自动轮询（页可见时）；卡片点击 → 该 run 的基准详情；日志尾展开 |
| 状态 | 监控页**只有活读模式**（快照模式下禁用并说明） |

---

## 3. 数据契约

### 3.1 事实基础：统一 result 信封（五类 adapter 同构，实测）

```
task_id, registry_id, adapter,
validity_gate (0|1), gate_failures: string[], failure_mode: null|string,
subscores: {physics, requirements, objective, robustness},   // 各 0–1 或 null
subscore_applicability: {同四键: string 注释},
score: 0–1,
artifacts: {…adapter 载荷, model_meta, grade_details},      // 唯一 adapter 差异点
timings: {agent_s, setup_s, grade_s},
environment_digest, assets_revision, logs: string[]
```

failure_mode 词表（全库实测频次，配色固定）：missing_output(412) / code_not_executable(403) / simulation_failed(120) / non_physical_values(104) / sandbox_escape_attempt(6) / timeout(1) / invalid_geometry(1)。

### 3.2 端点表（全部 GET、loopback 守卫、`/comac` 前缀独占）

| 端点 | 响应 | 数据来源 |
| --- | --- | --- |
| `/comac/overview` | 家底计数 + 最近 runs + 里程碑 | registry.yaml + results/ 扫描 |
| `/comac/registry` | 全部 entries（id/status/tier/adapter/env_class/license_status/…） | registry.yaml |
| `/comac/matrix?date=` | 行×列×格聚合 | results/ 聚合 |
| `/comac/runs` | run 索引（88 组合：registry_id/date/provider/n_tasks/gate 率/均分/manifest 内联字段） | results/ 扫描 |
| `/comac/bench/<id>` | entry + 该基准 runs + 任务行 | registry + results/ |
| `/comac/task/<id>/<date>/<provider>/<task_id>` | 完整信封 | 单 result.json |
| `/comac/runstatus` | 在跑批列表 + 进度 + 日志尾 | 进程 + 日志（与 comac_run_status 共层） |
| `/comac/snapshots` · `/comac/snapshot/<tag>` | 快照清单 · 快照 JSON | results/_snapshots/ |

**实现纪律（T3）**：端点逻辑活在 `plugin/dsh-comac-benchmark/index.js`（与 comac_* 工具同一文件同一读取层，绝不复写聚合逻辑）；每个 handler 首行 loopback 检查（非 127.0.0.1 → 403）。

### 3.3 ViewJSON（活读聚合 = 快照正文，同一 schema，UI 无感渲染两种模式）

```jsonc
{
  "header": { "mode": "live|snapshot", "tag": "M4?", "generated_at_utc": "…",
              "git_commit": "…", "generator": "comac-snapshot/1.0" },
  "registry": [ { "id": "...", "status": "...", "tier": "...", "adapter": "...",
                  "env_class": "...", "license_status": "...", "order": 1 } ],   // 全部 38 项
  "runs": [ { "registry_id": "...", "date": "2026-08-19", "provider": "glm",
              "model": "glm-4.6", "seed": 0, "n_tasks": 90,
              "gate_pass": 90, "gate_fail": 0,
              "failure_modes": { "non_physical_values": 104 },
              "subscore_means": { "physics": 0.71, "requirements": 0.87 },
              "score_mean": 0.8667,
              // T4：内联可复现字段（拷自 run_manifest）
              "environment_digest": "sha256:…", "assets": {"path": "sha256"},
              "rerun_command": "…", "git_commit": "…" } ],
  "tasks": [ { "run": 0, "task_id": "cfdquery_q001", "gate": 1,
               "failure_mode": null, "score": 1.0,
               "subscores": { "physics": null, "requirements": 1.0 } } ]   // run=runs[] 下标；体积预算 ~1.5MB/9728 题
}
```

### 3.4 快照文件（T4 纪律落成）

- 落点 `results/_snapshots/<tag>.json`（tag=里程碑名或日期），内容 = ViewJSON（mode=snapshot），进 git
- 生成器：`node plugin/dsh-comac-benchmark/snapshot.mjs --tag <t>`（与路由共享读取层）；`--full` 额外产出自包含外发包（快照 + 全部 result.json + 独立 HTML 壳）到 `results/_snapshots/<tag>-full/`，**不进 git**（.gitignore 增条目）

---

## 4. 技术选型与实现方案

### 4.1 架构（两个包，一处逻辑）

```
dsh-comac-benchmark（现有 server 插件，改造）
 ├ comac_* agent 工具（不变）
 ├ inject: ["webServer"]（新增）
 └ /comac/* 路由（新增；同一文件内的读取层直接复用） + loopback 守卫 + snapshot.mjs

dsh-comac-workbench（新包，纯 client）
 ├ package.json: dsh.client{platform:web, inject:[runtime, ui-conversation]} + exports["./client"]
 ├ src/client.jsx（React 18.3.1 宿主提供）+ ECharts 按需 + .comac-wb- CSS 注入
 └ lib/index.js: 空 apply（纯 UI 先例：dsh-client-ui-goal）
```

### 4.2 打包配方（T9+T5 实测结论，全量可复刻自 `.attic/t9-hello-client/` 与 `.attic/t5-chart-lab/`）

- tsdown 0.22：`format:"cjs"` + banner/footer 拼_factory 包装 + `clean:false` + `minify:true`
- **`deps: { neverBundle: [/^react(\/.*)?$/], alwaysBundle: [/^(?!react($|\/))/] }`**（tsdown 默认 externalize dependencies——不写 alwaysBundle 会得到 2KB 假产物）
- 构建脚本**fail-loud**：检查 tsdown 退出码，非零即中止（clean:false 下陈旧产物会冒充新构建）
- 挂载：**包名形态**（`~/.dsh/profiles/web/node_modules/dsh-comac-workbench` 软链到仓库 plugin 目录）+ cordis.patch.yml insert；首次安装后重启 dsh web 一次，此后 HMR 接管（T9 实证 500ms 轮询链路）

### 4.3 视觉栈（T5 决议）

- **ECharts 按需**（echarts/core + Radar/Heatmap/Bar/Scatter + CanvasRenderer + Grid/Tooltip/Legend）：实测 554KB/184KB gzip，本地磁盘加载
- **令牌 = 宿主 `--dsw-*`**：文字/边框/背景直接 `var(--dsw-alias-*)`；图表色启动时 `getComputedStyle` 读 `--dsw-static-{blue,green,amber,red,neutral}-*` 色阶构造 ECharts 主题（~20 行），`MutationObserver` 监听 `.light/.dark` 切换重建
- **样式 = `.comac-wb-` 前缀 CSS 字符串注入**（单文件 bundle 契约：CSS 必须内联进 client.js）；字号走 `--dsw-font-{xxxs…xl}` 梯度（高密度默认 xs/s）
- 中文：宿主字体栈已含 PingFang SC 等，零成本；fallback：visx（14.5KB，SVG 原生令牌）若 ECharts 主题映射不合格

### 4.4 内网移植（T2 结论 + **T8 占位**）

已定（T2）：**dev 侧打自包含制品、内网拷目录**——client bundle 天然是自包含单文件；20 条本地化校验清单（A 依赖/B 写法/C 构建/D 验收）进验收流程；node-gyp 判定：运行时制品含原生模块=违规（ECharts/tsdown 均纯 JS，通过）。

**待 T8（人工确认 7 问，见 `tickets/T8-intranet-dsh-shape.md`）**：
- Q2（一票否决级）：内网 DSH 是否含 web GUI？含 → 本方案内网成立；不含 → 启用**方案 B**：`--full` 外发包的独立 HTML 壳（快照模式只读变体，无宿主依赖，浏览器直接打开）作为内网形态，内嵌页形态保留 dev
- Q1/Q3/Q4：决定内网 serve 方式与浏览器兼容底线
- Q5–Q7：流程级，不阻塞

### 4.5 本地化校验关键条（全表见 T2 报告 §问题3）

产物 `grep -rE "https?://"` 零外链；`@font-face` 只指包内文件；遥测 SDK 零依赖；`base:'./'` 相对路径；断网冒烟（D1）+ 全页零外连监听（D2）；制品 SHA256SUMS 归档。

---

## 5. 分期路线

### v1（本规格，预期 1–2 个实现 session）

范围：五页全量 + 活读/快照双模式 + ECharts + 宿主令牌 + snapshot.mjs。

**验收标准**（逐条可测）：
1. 工作台视图出现在 DSH GUI 会话头部，五页可达，console 零错误；
2. 矩阵页默认日期显示 19 行×provider 列，格值与 `summary.md` 手算一致（抽 3 组核对）；
3. 从矩阵格钻到单题（矩阵→详情→下钻全链路），qa/code/simulation/field 四类 adapter 载荷各渲染一题正确；
4. 非本机访问 `/comac/*` 得 403（用 curl 模拟非 loopback 地址头）；
5. `snapshot.mjs --tag test` 产出 <2MB JSON，UI 快照模式渲染 = 活读模式同数据；`--full` 包断网可开；
6. 明暗主题切换图表色跟随；中文字幕/轴标注清晰无豆腐块；
7. 深链可复制：矩阵/详情/下钻的面包屑状态可从 URL hash 恢复。

### v1.1（T8 回来后）

- 内网章定稿（方案 A 内嵌 / 方案 B 静态壳）；`--full` 外发包叙事化包装按评审反馈裁剪；`results/_snapshots/*-full/` 进 .gitignore。

### v2（fog 区毕业，按需切票）

- 运行监控进度语义升级（runner 落 progress.json，需动 runners/——单独票）；
- adapter 载荷渲染器精修（simulation_agent 文件树折叠、code_exec diff 视图）；
- provider 扩容交互（列 pin/diff/归一化）；
- 评审只读视图（--full 包的打开方式定稿）。

### 风险登记册

| 风险 | 等级 | 对冲 |
| --- | --- | --- |
| 内网无 DSH web GUI（T8-Q2） | 高（仅内网侧） | 方案 B 静态壳已设计，dev 侧不受影响 |
| ECharts 主题映射观感不合格 | 中 | visx fallback（T5 记档） |
| 宿主令牌名随 DSH 版本漂移 | 低 | 升级跑视觉冒烟（v1 验收 6 复用） |
| tsdown/rolldown 版本演进破坏 factory 格式 | 低 | 构建产物首行断言 `window.__ModuleLoader__.load(`（构建脚本内建） |
| 快照 tasks[] 随基准扩容超 5MB | 低 | 分片预案（T4 已评估，触发时切） |

---

## 附录：研究报告索引

| 报告 | 内容 |
| --- | --- |
| `research/T1-dsh-data-bridge.md` | slot 机制、四通道能力矩阵、候选桥粗评（含证据路径） |
| `research/T2-intranet-runtime.md` | 内网证据盘点、npm 本地化映射、20 条校验清单、T8 七问 |
| `research/T5-chart-visual-stack.md` | 宿主令牌体系、七候选实测矩阵、样式方案 |
| `research/T9-client-bundle-packaging.md` | factory 格式配方、挂载形态定论、HMR 实证、e2e 旁路 |
