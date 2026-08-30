# CFD 仿真论文调研与 Benchmark 转化报告（agent-CFD 优先）

> 调研日期：2026-08-28。本文件是 registry 批次 `v0.3-cfd-agent`（11 条）与
> litbench/cfdb 镜像的证据基线，内容冻结不再编辑；后续更新走新日期文件。
> 核验方式：arXiv Atom API 逐篇抓取（36 篇，摘要 sha256 锁定于
> `data/cfdagent/litbench/papers.json`）+ 子代理 Crossref/NTRS/GitHub-HF 元数据核验
> （V&V 10 篇、许可证矩阵，明细 `research/cfd_bench_papers_2020plus.json`、
> `research/cfd_paper_code_licenses.json`）。

## 1. 核心结论

1. **agent-CFD（LLM/多智能体驱动 CFD 仿真）在 2024-2026 已从概念期进入基准期**：
   共核验 20 篇核心工作，其中至少 9 篇自带可复用评测资产（任务列表/case 集/评分器）。
   评测范式收敛为三层：知识（MCQ）→ 代码（NL→solver 配置）→ 端到端案例（NL→可运行
   OpenFOAM 案例 + 物理保真度）。
2. **上游基准资产质量参差，"可判分"比"有代码"更稀缺**：FoamBench（110+16）、
   cfdb（42 案例，MIT）、ChatCFD 315 案例、IteraSim 28 案例、MOOSEnger 125 提示为
   可直接转化层；OpenFOAMGPT 2.0（450+ 仿真）等只有论文内协议，无公开资产。
3. **本项目已有条目覆盖了该方向最好的公开基准（CFDLLMBench 三组件）**；本次增量
   价值在：文献知识层（litbench，新建并 integrated）、solver-agnostic 任务书与经典
   V&V 执行层（cfdb 三域，镜像并 staged）、以及 5 个数据集型候选的许可清点。
4. **许可证红线**：DrivAerNet++/FlowBench 数据为 CC BY-NC 4.0（同 camb，法务澄清前
   不镜像，条目 deferred）；UniFoil CC BY-SA 4.0 可用（注意 SA 传染性）；cfdb 全套 MIT。

## 2. agent-CFD 核心论文（20 篇，2024-07 ~ 2026-08）

| # | 论文 | arXiv/venue | 核心贡献 | 可复用评测资产 | 转化去向 |
| --- | --- | --- | --- | --- | --- |
| 1 | MetaOpenFOAM | 2407.21320 | 首个 OpenFOAM LLM 多智能体（MetaGPT 范式+RAG） | 8 任务 NL→CFD 基准（85% 通过率自报） | registry `cfdagent.metaopenfoam8`（proposed，GPL-3.0，上游已 deprecated 需锁版本） |
| 2 | MetaOpenFOAM 2.0 | 2502.00498 | CoT 分解+迭代验证，扩展到后处理 | 仿真+后处理基准（6.3/7 Executability） | 并入 litbench；资产随 #1 仓库 |
| 3 | OptMetaOpenFOAM | 2503.01273 | 桥接外部分析/优化工具库 | 11 个分析/优化任务 | 并入 litbench |
| 4 | Foam-Agent | 2505.04997 (CMAME 2026) | 多索引 RAG+依赖感知生成+轨迹审查环；六 agent | FoamBench 110 Basic/16 Advanced 执行结果 | 与既有 cfdllm.foam_basic 对读（其 SOTA 基线）；代码 MIT |
| 5 | Foam-Agent 2.0 | 2509.18178 | 端到端（Gmsh 网格/HPC 脚本/ParaView）+ MCP 可组合服务 | 110 任务 88.2%（Claude 3.5 Sonnet） | 同上；MCP 模式为 FLAi-OS 借鉴点 |
| 6 | OpenFOAMGPT | 2501.06327 (PoF) | GPT-4o+o1 双模型 agent + RAG | 无公开基准（多任务演示） | 仅 litbench 知识点 |
| 7 | OpenFOAMGPT 2.0 | 2504.19338 (IJHFF 2026) | 四 agent 端到端 | 450+ 仿真协议（100% 自报，无公开资产） | 仅 litbench |
| 8 | OpenFOAMGPT 多模型横评 | 2504.02888 | ChatGPT/Qwen/DeepSeek 成本-效果横评 | 内部任务集（未公开） | 仅 litbench |
| 9 | ChatCFD | 2506.02019 | 结构化知识库+错误定位器；**物理保真度指标** | 315 案例基准（82.1%；vs MetaOpenFOAM 6.2%） | 候选后续接入（代码 GPL，基准协议未独立发布→观察）；litbench 覆盖 |
| 10 | CFDagent | 2507.23693 (PoF) | 零样本三 agent（Point-E 文生几何+浸入边界） | 圆球 Re100/300 演示（无公开资产） | 仅 litbench |
| 11 | CFD-copilot | 2512.07917 | 微调 LLM + MCP 后处理 | NACA0012 + 30P-30N（论文内定义） | 与 cfdb NACA 系对读；litbench 覆盖 |
| 12 | SwarmFoam | 2601.07252 | 多类型 LLM 多模态感知 | 25 案例（NL 80% / 多模态 86.7%） | 仅 litbench |
| 13 | AutoFOAM | 2608.00003 | 自进化 agent（252 prompts 微调+反坍缩流） | 无公开基准 | 仅 litbench |
| 14 | IteraSim RAG | 2607.20346 | 多阶段检索（扩展+RRF+MMR+路由）+三 agent 分工 | **公开 28 案例基准+评分rubric** | 候选接入（待仓库定位）；litbench 覆盖 |
| 15 | PhyNiKCE | 2602.11666 | 神经符号（约束满足验证，守恒刚性） | OpenFOAM 非教程任务集（部分公开） | 观察项；litbench 覆盖 |
| 16 | TurboAgent | 2604.06747 | 叶轮机气动设计闭环（生成→预测→优化→CFD 验证） | 跨声速单转子压气机验证协议 | 与 tudaglr.openstage 互补；litbench 覆盖 |
| 17 | FoamPilot（火灾） | 2412.17146 (NeurIPS WS) | FireFOAM 三功能 agent（RAG 源码洞察/配置/HPC） | 功能演示（无基准） | 仅 litbench |
| 18 | FlamePilot（燃烧） | 2601.01357 | 文献感知自纠错燃烧 CFD（OpenFOAM+DeepFlame） | 公开基准 1.0/0.438（先例 0.625/0.250） | litbench 覆盖；DeepFlame 支持为内网替代路线参考 |
| 19 | AI CFD Scientist | 2605.06607 | 视觉-语言物理验证门（14/16 静默失效检出） | 5 任务+植入失效消融集；代码/提示/产物开源 | 候选接入（github csml-rpi/cfd-scientist，license 未标→需核验）；litbench 覆盖 |
| 20 | MOOSEnger | 2603.04756 | MOOSE 多物理域 agent（125 提示基准 0.90 vs 0.06） | **125 提示基准**（HIT 输入族） | 结构力学/多物理扩展方向候选（本批不立条） |

邻接 2 篇：SmartFlow（2508.00645，DRL 求解器无关框架——非 LLM-agent，作为 HPC/RL
执行层参考）；CFDLLMBench（2509.20374，JDMLR——**已接入** cfdllm.cfdquery/cfdcode/
foam_basic 三条目，本次补充其论文级引用与 FoamBench 110/16 结构对读）。

LLM+湍流建模 2 篇：AutoTurb（2410.10657，LLM 符号发现湍流封闭，periodic hills
Re=10,595）、LLM 驱动湍流模型开发（2505.01681，DeepSeek-R1 平等伙伴闭环）。二者进入
litbench；其"模型发现"任务型态暂不可客观判分，不立 registry 条目。

## 3. ML-CFD 数据集/基准论文（11 篇）

| 论文 | arXiv | 数据规模 | 许可证（核验） | 转化去向 |
| --- | --- | --- | --- | --- |
| FNO | 2010.08895 (ICLR'21) | Burgers/Darcy/NS .mat | 代码 MIT | litbench（方法知识）；数据不镜像（规模小但被 PDEBench 覆盖） |
| MeshGraphNets | 2010.03409 (ICLR'21) | 6 类网格数据集 | 代码 Apache-2.0 | 同上 |
| PINNacle | 2306.08827 (NeurIPS'24) | 20+ PDE×约10 方法 | MIT | **registry `pinnacle.suite`（integrated 2026-08-29）**：3 道 PINN 前向解算 code_exec 任务（burgers1d/helmholtz2d/poisson1d），冻结 loader rel L2 阈值判分，oracle 满分自检 |
| BLASTNet 2.0 | 2309.13457 (NeurIPS'23) | 2.2TB/744 样本/34 DNS | 数据 CC BY 4.0 | 超 resolution 方向候选，本批不立条（3D 体数据成本高，tier 外） |
| DrivAerNet | 2403.08055 | 4,000 车完整气动 | 数据 CC BY-NC 4.0 | 并入 DrivAerNet++ 条目 |
| DrivAerNet++ | 2406.09624 (NeurIPS D&B'24) | 8,000 车/39TB | 数据 CC BY-NC 4.0 | **registry `drivanetpp.coeff`（deferred，NC 待法务）** |
| FlowBench | 2409.18032 | 10K+ DNS 样本 | 数据 CC BY-NC 4.0（HF 核验） | **registry `flowbench.lite`（deferred，NC 待法务）** |
| The Well | 2412.00568 (NeurIPS D&B'24) | 15TB/16 数据集 | 代码 BSD-3/数据 CC BY 4.0 为主 | **registry `thewell.fluiddyn`（proposed，confirmed-split）** |
| UniFoil | 2505.21124 | 50 万翼型 RANS（NLF 4,800+FT 30,000） | CC BY-SA 4.0（HF 核验） | **registry `unifoil.airfoil`（staged，⚠ 数据质量门）**：transi analysis.csv 为优化中间态（CL 全量 ≈0 无升力线斜率，不可作真值）；真系数层在 turb_data 包（889MB+）下载探针待重试——任务生成冻结于数据质量门 |
| Transolver | 2402.02366 | 方法（复用 6 基准） | 代码 MIT | litbench；不独立立条（无自有数据） |
| 可压 NS 长程 rollout 基准 | 2601.22541 | 无公开代码/数据 | unknown | litbench（知识点）；数据获取待作者 |

湍流封闭数据线补充（未进 corpus，许可/入口已核）：McConkey 策展数据集
（2103.11515，Sci Data 2021，89.5 万带标签点，Kaggle）、The Closure Challenge
（2603.28884，2026，社区基准挑战，repo rmcconke/closure-challenge-benchmark）——
**建议后续批次一并评估为 `closurechallenge.turb`（proposed，license 待核）**，本批未立条。

## 4. V&V / 研讨会方向论文（10 篇，Crossref/NTRS 核验，均非 arXiv）

这批**不进 litbench**（无可核验摘要文本），价值是具体化既有条目并指明转化路径：

| 论文 | 年 | 具体化对象 | 转化结论 |
| --- | --- | --- | --- |
| DPW-VII 官方数据汇总（AIAA 2023-3492） | 2023 | crm_dpw_hlpw.coarse | 标模几何+五族网格 NASA 免费公开 → 网格收敛/气动曲线复现任务族 |
| HLPW-4 固定网格 RANS 总结（J. Aircraft） | 2023 | crm_dpw_hlpw.coarse | 100+ 提交数据集统计 → 高升力 RANS 最佳实践评测 |
| HLPW-5 总览（AIAA 2025-0045） | 2025 | crm_dpw_hlpw.coarse | 接续届次，锁版本时直接对准 HLPW-5 |
| NASA Juncture Flow 经验总结（J. Aircraft） | 2022 | nasa_tmr.verification | 完整公开验证数据包（TMR 托管）→ 角区分离验证任务 |
| SA-QCR2000 验证套件（AIAA 2021-1552） | 2021 | nasa_tmr.verification | 三案例完整规格 → **湍流模型实现正确性自动判分**（agent-CFD 执行层最贴合的 V&V 源） |
| HFCVW 2024 发布/总结（2023-1244 / 2024-3698） | 2023/24 | nasa_tmr.verification | 7 求解器提交汇总 → 新一代社区验证工作坊体系 |
| 加热超声速轴对称射流 TMR 案例（2025-2577） | 2025 | nasa_tmr.verification | TMR 案例库扩充 |
| CFD Vision 2030 进展（AIAA 2021-2726） | 2021 | 战略引用 | 定位/论证素材，无评测资产 |
| TUDa-GLR-OpenStage V&V（JGPPS，CC BY 4.0） | 2023 | **新条目 `tudaglr.openstage`（proposed）** | 压气机级特性线对账；叶轮机械唯一标模候选；数据申请制 |
| BARC 5:1 矩形柱 GCI/LS 验证（ASME JVVUQ） | 2023 | 方法论参考 | 离散不确定度评定 → 容差设计模板 |

## 5. 本批落地产物（已完成）

| 产物 | 位置 | 状态 |
| --- | --- | --- |
| litbench 语料（36 篇 arXiv 摘要+元数据，sha256 锁定） | data/cfdagent/litbench/ | 完成 |
| litbench 题库（60 题，逐题引文锚定+强校验） | data/cfdagent/litbench/questions.json | 完成 |
| litbench 任务（60 YAML+MD，qa_grounded） | tasks/cfdagent.litbench/ | 完成，oracle 1.0 / stub 0.25 / minimax 0.8667 / glm-5.3 0.7833 |
| cfdb 镜像（42 案例，MIT，b26799e） | data/cfdb/ | 完成 |
| cfdb 任务（verification 9 + validation 8 + case_setup 17） | tasks/cfdb.*/ | verification/validation **integrated**（oracle 满分自检），case_setup staged（evidence 休眠待工具通道） |
| registry 批次 v0.3（11 条） | registry/registry.yaml | 完成（litbench/cfdb.verification/cfdb.validation integrated） |
| 许可证矩阵追加 | registry/license-notes.md | 完成 |
| 生成器（--check 防漂移） | runners/gen_tasks_cfdagent.py, runners/gen_tasks_cfdb.py, runners/arxiv_corpus.py | 完成 |

## 6. 后续工作（按价值排序）

1. **cfdb.case_setup 升 integrated**：14 evidence 任务需工具执行通道接入 providers
   （agent 自驱求解器提交证据包——FLAi 内核/容器 agent 方向）；3 managed 任务判分
   分支已就绪，随域整体验收。dam_break/naca0012_sa_tmr 的重纳依赖上游预算/几何修订。
2. **unifoil/thewell 数据镜像（均有外部依赖）**：unifoil = turb_data 探针重试
   （2026-08-30 网络停滞；包内若同 transi 的简并 CL 则转 CGNS 路线评估）；
   thewell = HF gated repo，需账号接受 PolymathicAI/the_well 条款并确认/更新
   keychain hf-token 后重探（2026-08-30 实测 401）。
3. ~~litbench 补充真实 LLM 基线~~ ✅（minimax 0.8667 / glm-5.3 0.7833）；
   ~~pinnacle.suite 真实 LLM 基线待补~~ ✅（glm-5.3 0.7667 / minimax 0.6667）。
4. 法务确认 NC 边界后重审 drivanetpp/flowbench；TU Darmstadt 申请 TUDa 数据。
5. ChatCFD 315 案例 / IteraSim 28 案例 / AI CFD Scientist 5 任务三个"论文自带基准"
   的资产定位与接入评估（代码许可已核：GPL/MIT-missing）。
6. `closurechallenge.turb`（湍流封闭社区基准，repo rmcconke/closure-challenge-benchmark
   已克隆待核许可）按 §3 建议立条。

## 7. 方法论备注

- 摘要级事实一律取自 arXiv API 原文（sha256 锁定），题目 evidence 必须是其逐字子串，
  生成器校验失败即退出非零——"论文→题"转化全程可审计、可重放。
- 所有量化声明在报告中标注"自报"（上游论文口径），litbench 考文献知识、不背书结论。
- web_search 配额耗尽期间，全部核验改走 arXiv/Crossref/NTRS/GitHub-raw 一手 API，
  无一条目依赖二手转述。
