# 开发现状深度研究与首测就绪度评估

日期：2026-09-11。基线：git `25a81e7c`（08-31）+ 工作树未提交改动（至 09-08 晚）。
方法：仓库全量盘点——50 个提交、registry 59 条、tasks/ 31 目录 2645 个任务 YAML、report/ 26 个报告目录、tests/ 24 个测试文件、comacbench/ + runners/ + plugin/ 源码、results/ 与 results/_snapshots/。本报告只读不写运行语义。

## 0. 一句话结论

项目已形成「两条主线、一套纪律」：**A 线（评测资产）**建成 31/52 integrated、~2700 任务、十一维雷达的民机设计模型评测系统；**B 线（工程产品）**在 9 月上旬完成航空工程评测插件 v1（comacbench 包 + 3 评测包 + JSON stdio agent 协议 + 证据准入），P0 验收全过、P1 约七成。**距离「受控内测版」（1-3 名工程师、结构 + 企业数据两包、CFD 作研究附录）约 1-2 周专注工作；距离「公开测试版」（含文件级数据线、贡献隔离、更多工况）约 4-8 周。** 当前最大风险不是功能，而是：① B 线 11 天工作全部未提交；② 判分可信关有已知遗留；③ 从未做过一次真实工程师接入实测。

## 1. 两条主线

| | A 线：评测资产（模型评测系统） | B 线：工程产品（工程师评测插件） |
| --- | --- | --- |
| 定位 | 评模型/评 harness（研究资产 + 判分内核蓄水池） | 评工程师自己的 agent（产品出口） |
| 形态 | registry 59 条 + 五类 adapter + gate/九维评分 + results 落盘 | comacbench CLI（validate/run/calibrate/admission）+ 3 个 pack + agent.v1 协议 |
| 入口 | comac_* 6 个 DSH 工具 + CLI | comac_* 4 个 pack 工具 + CLI + 工作台工程师页 |
| 时间 | 08-19 起，已提交至 08-31 | 09-05 起，**全部未提交** |
| 状态 | 31/52 integrated，~2700 任务 | P0 ✅ / P1 约 70% / P2-P4 未启动 |

支持设施（两线共用）：DSH 插件（10 工具）、工作台 UI（只读 + 工程师入口）、B02/B04 可信复跑协议、license/PROVENANCE 纪律、civair-kb 知识底座（外部）。

## 2. 开发现状时间线

| 时段 | 里程碑 | 证据 |
| --- | --- | --- |
| 08-19~08-23 | M0-M4：registry 建制、首批 8 基准、批次2/3（通识锚）、九维基线报告、工作台 UI 规格 + v1-accept 快照 | M1-M4-summary、wayfinder T1-T9 |
| 08-24 | v0.3 范式转向 harness-first（四臂 H0-H3）；structures 解零（calculix 21 题） | harness-eval-2026-08-24 |
| 08-25~08-26 | 办公维（engtable/awdoc/awext/ssb）、cad 草图、民机贴合度评估（十维）、深度巡查（26 审计 agent，10 major 当场闭环） | coverage-assessment、deep-audit |
| 08-28~08-31 | P1 awcom 适航合规（隐藏层 M10 兑现）、litbench（46 篇论文→60 题）、cfdb 三件套、pinnacle（PINN）、case_setup oracle 16/16 —— 收于 31/52·2701 | 各 integrated_note |
| 09-05 | **接手转向**：takeover 报告定新方向（可信复跑 + 交付闭环优先）；B02/B04/B03 修复；DeepSeek 通道 402 失败留痕、MiniMax 通道打通 | takeover、trusted-resume |
| 09-06 | **插件 v1 落地**：comacbench 包、3 packs、agent.v1 协议、双模型 24 题扩样、B03/B05 二修、CFD 敏感性研究（GCI 0.884% 未过 0.5% 门） | aviation-plugin-v1、expanded-24-v2 |
| 09-07~09-08 | CFD Re200/Re300 扩展（48 组研究）、第四网格、证据准入模块（admission/evidence）、96GB 原始场清理（保留 188 份摘要） | cfd-evidence-integration、storage-cleanup |
| 09-09~09-11 | **无文件改动**（停摆 3 天）；最后 commit 仍停在 08-31 | 文件系统 mtime |

### 2.1 版本管理状态（红色警报）

工作树：101 modified + 52 untracked + 1 deleted，**B 线全部内容未进 git**——comacbench/ 全包、packs/、docs/ 下 19 份 specs、evidence/、examples/、插件 packs.js、工作台 engineering.jsx、9 月全部报告目录。任何误操作（stash/checkout/clean）都可造成不可逆丢失。

建议分批提交：① B 系列 runner 修复 + 测试；② comacbench 包 + packs + quickstart/specs；③ 9 月报告 + evidence + 清理回执；④ 工作台/插件改动。

### 2.2 质量与运行状态

- 测试：24 个文件，文档化时点全绿（全量 139 例 88.4s + 准入 9 例 + 保留 2 例）；负例校准矩阵（正确/原样复制/部分完成/破坏一格）已成纪律。
- 运行期发现（本次研究实测）：本会话 `comac_registry` MCP 工具报错——插件 host 侧 `PY = "python3"`（index.js L44）走系统解释器，系统 python3 无 PyYAML，而 .venv 有（6.0.3）。registry 解析在无 yaml 的机器上必坏，属插件环境装配 bug。
- 数据资产遗留：`data/scicode/physics/test_data.h5` LFS 缺失（影响 52 题资产校验，takeover 已留档）；CFD 原始场已按需删除（复核须重解，已有声明与拒绝逻辑）。

## 3. 能力矩阵

### 3.1 A 线：评测对象覆盖（九维 → 08-25 办公 → 08-28 适航 = 十一维）

| 维度 | 承载基准（任务量） | 覆盖 | 基线要点 |
| --- | --- | --- | --- |
| knowledge | cfdquery 90 / aeroengqa 80 / mechvqa 180(VLM) / litbench 60 | 4/4 厚 | 文本 0.78-0.93；VLM 0.35-0.40「看得见判不稳」且单厂商 |
| coding | scicode 52 / cfdcode 15 / pinnacle 3 + 通识锚 6 项（~1557） | 1.00 | 领域 0.47-0.77 vs 通识 0.82-0.98 分水岭成立 |
| cad_geometry | cadgen 22 / sketch_lite 15（openvsp paused、seldon.hard proposed） | 2/4 | 3D 参数化 + 2D 草图；GLM 0.87 API 幻觉 |
| cfd | foam_basic 110 / superwing 100 / hilift 100 / cfdb 三件套 34 | 3/5→厚 | LLM 系数回归差 ML 4.7-19×；foam 双零（physics 层边界）；cfdb oracle 16/17 全真解 |
| structures | calculix.fea_basic 21（simjeb/engdesign 卡商业栈） | 1/3 | 双基线 0.24/0.38 落区分带；反力键独立捕获载荷路径错误 |
| propulsion | pycycle 28 | 1/1 厚 | H2 脚手架 0→1.0「知识注入」核心实证 |
| flight_control | gtm 25 + hard 17 | 1/1 | MATLAB live；hard 区分带 0.65-0.71 |
| mdo_design | aviary 27（engdesign/crm 未进） | 1/3 | 过 gate 即满分，区分度模式待改 |
| office_productivity | engtable 19 / awdoc 18 / awext 12 / ssb 25 | 1.00 | ssb 真实深水区 0.16-0.31；B03/B05 修复后重跑 glm 24/24 满分 |
| 适航合规 | awcom 15 + 隐藏池 45 | 首落 | M3 0.865 / GLM 0.884；hidden-public 分差监控上线 |
| robustness_audit | 横切 | 0.60 | 无独立承载，靠沙箱告警 + manifest 审计 |

### 3.2 A 线：评测体系自身能力（harness 雷达，08-26 发布口径为最新数值）

| 轴 | 值 | 备注 |
| --- | --- | --- |
| 公共可比层 | 0.95 | 11 基准双基线；HE+/MBPP+ 抗泄漏 |
| 工程可执行层 | 0.87 | 13 基准 live；扣分=商业 CFD/FEA 缺失（08-28~31 cfdb/pinnacle 落地后实际更高，未重发布数值） |
| 受控隐藏层 | 0.55 | awcom 兑现后实际提升；simulation 族接线未做 |
| 多模态评测 | 0.55 | 单厂商 VLM 是硬缺口 |
| Adapter 类型 | 1.00 | 5/5 全 live |
| 环境覆盖 | 0.67 | 6/9 env_class；缺 commercial_cfd/fea |
| 判分自检 | 0.84 | oracle 覆盖持续上升（cfdb case_setup 16/16 后更高） |
| 可复现审计 | 0.90 | B02/B04 后 trusted resume 已补强（09-05） |
| Harness 臂评测 | 0.75 | 四臂 20/20 + arm_router 生产化 |

### 3.3 B 线：工程师插件能力（P0-P4 阶段门，来自自家 spec）

| 阶段 | 状态 | 证据与缺口 |
| --- | --- | --- |
| P0 评测包/stdio agent/预检/校准/可视化 | ✅ | 六条验收有复查证据；10 个 DSH 工具；report.html 离线无 CDN |
| P1 工业仿真可信性 | 约 70% | 结构 ✅：六项输入检查 + 8 负例 + 完整证据（inp/dat/日志 SHA-256）。CFD ⚠️：单评分任务（Re=100）；GCI 0.884% 未过 0.5% 研究门；10% 容差沿演示口径未校准；Re200/300 仅研究证据（admission 边界清晰） |
| P2 企业数据与本体 | ❌ | core-v1 仅 2 个入门任务；文件级 ETL/血缘/PROV-O/SHACL 未动 |
| P3 贡献流水线隔离 | ❌ | 预检/校准有；隔离执行、签名、专家审查未自动化（by design：publishable=false） |
| P4 工程师插件产品化 | ❌ | 首次接入实测未做；内网实机未验 |

### 3.4 通道与固定对

固定对 {MiniMax-M3, GLM-5.3/5.3-flash} 全覆盖；VLM 单厂商（glm-4v-flash / 4.6v）；DeepSeek 通道 402 不可用（留痕，未充值未重试）。

## 4. 距离第一版测试版还有多远

### 4.1 定义先行（假设声明）

- **定义甲（推荐）**：comacbench **受控内测版**——交给 1-3 名真实工程师，用 structures-v2 + core-v1 两包评自己的 agent，CFD 作研究附录。
- 定义乙：A 线评测系统 v0.1 报告对外发布——实际已越过（M4 于 08 月完成，且 v0.3 已转向 harness-first），不构成「未来里程碑」。

### 4.2 对照自家《产品化验收指标》（roadmap L72-80）的差距表

| 指标 | 状态 | 差距 |
| --- | --- | --- |
| 工程师首次接入 15 分钟 | ❌ | **唯一的真 beta 门**，从未实测 |
| 可解释性（报告下钻到检查/修复方向） | ✅ | 六阶段/六项检查/证据路径已实现 |
| 贡献反馈（位置/原因/修复建议） | ✅ | 阻断/待审查分级，publishable=false 纪律 |
| 判分可靠性（按缺陷类型报误放行/误拒绝） | ⚠️ | 每包正负例校准 ✅；遗留：ssb 大表未变格多导致近满分、ssb_22_47 排序歧义隔离中、CFD 容差未校准 |
| 样本设计（公开/保留/隐藏分组） | ⚠️ | A 线 awcom 隐藏池 ✅；B 线包内单题、无保留集 |
| 可复现性（同身份续跑/身份变更拒绝） | ✅ | B02/B04 trusted resume + 测试覆盖 |
| 离线落地 | ⚠️ | report.html 无外部请求 ✅；三 venv + Docker pin + 系统 python3 装配复杂，内网实机未验 |

### 4.3 关键路径与工作量（定义甲：受控内测版）

| # | 事项 | 估时 |
| --- | --- | --- |
| 1 | 版本管理止血：分批提交 11 天工作 + 一次全量测试回归 | 0.5-1 天 |
| 2 | 内测范围冻结与声明：两包为主菜、CFD 标注研究性、明示「不代表模型排名/飞机级验收」 | 0.5 天 |
| 3 | 判分遗留处置：ssb 遗留列清单（修或声明排除）；comac_registry 插件 python 解析修复 | 1-3 天 |
| 4 | 安装故事：bootstrap 脚本（venv+依赖+CCX/OpenFOAM/Docker sha 探测）+ 插件安装实测 | 2-3 天 |
| 5 | 首个真实工程师 15 分钟接入实测 + 一轮反馈修复 | 2-4 天 |
| 6 | 发布物：版本号、离线包、快照 | 1 天 |
| 合计 | | **约 1-2 周专注** |

定义乙之外若要「公开测试版」还需：P2 文件级数据线（2-3 周）、贡献隔离执行（1-2 周）、CFD Re200/300 转正（校准+负例+工程审查，1-2 周+审查周期）、12 个结构/CFD 任务变体（roadmap 目标）、工作台 T7 原型/T8 内网确认——**合计约 4-8 周**。

### 4.4 风险清单（按严重度）

1. **未提交工作**（立即处理）：B 线全部资产在工作树裸奔 11 天。
2. **判分可信遗留**：大表近满分（权重结构项稀释关键变更）、ssb_22_47、CFD 10% 容差未校准——beta 声明必须显式排除或标注。
3. **零真实用户数据**：15 分钟指标、报告可解释性都停留在自测。
4. **装配复杂度**：.venv/.venv-aviary/.venv-cad 三栈 + Docker 镜像 sha + 系统 python3 兜底（已实锤出 bug）——新机器复现是 beta 最大摩擦源。
5. scicode test_data.h5 LFS 丢失（52 题资产校验）。
6. CFD 原始场已删：任何物理复核需重解（已声明，风险可控）。
7. 动量：09-08 后停摆 3 天，evidence-admission 里程碑收口后无后续。

## 5. 战略观察与建议

1. **今天就提交**（第 4.3 节清单①）。这是唯一一个零技术含量、高灾难风险的项。
2. **内测版范围收窄到两包**：structures-v2（判分最可信、证据最全）+ core-v1（流程冒烟）；CFD 用 admission 模块作「研究证据附录」——这个边界系统已经原生支持（retained_analysis_and_receipts / native_evidence_available=false），不需要新开发。
3. **15 分钟接入实测是唯一真正的 beta 门**。其余指标都已自测或可控；没有这一次实测，所有「工程师可用」都是推断。建议找一名非作者工程师，按 quickstart 从零走一遍并计时。
4. **判分冻结纪律**：B 系列遗留列成清单，能修则修，不能修的在内测声明中逐条排除——这套「边界承诺」写法正是本项目区别于排行榜产品的核心资产，应显式呈现在发布物里。
5. **装配即产品**：写一个 `bootstrap.sh`（或 Makefile target）把三 venv、CCX/OpenFOAM 探测、Docker sha 校验、插件安装一条化；顺带修 comac_registry 的解释器解析（走仓库 .venv 或打包 PyYAML）。
6. **A 线不必为 beta 阻塞**：31/52 资产线保持自己的节奏（cfdb case_setup 收尾、隐藏层扩族、第二厂商 VLM）；中期机会是 A↔B 互喂——A 线 evidence 两阶段协议与 B 线 admission 模块同构，任何 A 线基准都可打包成 B 线 pack 供工程师本地用。
