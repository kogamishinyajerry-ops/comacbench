# 民机设计 LLM/Agent Benchmark 调研报告（归档）

> 调研日期：2026-08-19。本文件是 registry.yaml 与全部接入决策的证据基线，内容冻结不再编辑；后续更新走新日期文件。

## 核心结论

**不存在一套现成的开源 benchmark，能够完整覆盖民航飞机总体设计、气动、结构、动力、飞控、系统工程和适航要求。** 现有资源分三类：

1. **可直接接入**：有题目、标准答案或自动评测器 —— CFDLLMBench、AeroEngQA、SciCode；
2. **需自行包装**：公开数据集/经典验证案例 —— SuperWing、NASA CRM/HLPW、HiLiftAeroML、SimJEB；
3. **适合生成动态题**：开源工程工具 —— NASA Aviary、OpenVSP、pyCycle、GTM、JSBSim。

Harness 建设为三层：公共可比层（横向对比）/ 工程可执行层（真生成代码、模型、网格并运行）/ 受控隐藏层（动态生成防记忆）。

## 筛选标准（权重）

| 维度 | 权重 |
| --- | --- |
| 民机设计直接相关性 | 25% |
| 可客观自动判分 | 20% |
| 工程可信度 | 15% |
| Harness 接入成熟度 | 15% |
| 许可证可用性 | 10% |
| 可复现性 | 10% |
| 算力与存储成本 | 5% |

## 现成 benchmark 评级

| 基准 | 评级 | 要点 |
| --- | --- | --- |
| CFDLLMBench（CFDQuery/CFDCodeBench/FoamBench） | S | 90 MCQ + 24 编程 + 110 基础/16 高级 OpenFOAM 任务；BSD-3-Clause；三子基准拆开报告 |
| AeroEngQA | S | 80 专家题（NASA/NTSB/专利），平衡可答/不可答、短/长上下文；测 RAG 引用与拒答；Zenodo 许可待核 |
| SciCode | A | 80 主问题/338 子问题；Apache-2.0；有 inspect_ai 集成与 DeepSeek 配置；作底层能力门槛 |
| EngDesign-OPEN | A | 101 任务/473 评分项中 53 个完全开源；逐任务许可证清点后接入 |
| CADGenBench | A− | 49 生成 + 32 编辑；代码 Apache-2.0/数据 ODC-BY；完整分依赖私有 GT，仅纳入本地可复现部分 |
| MechVQA | B+ | 工程图/装配图理解；multimodal_only；LLM judge 只评解释 |
| CADBench | B+ | MIT 代码/数据各异；数据级许可矩阵建立后再审 |
| DesignQA | A−(能力)/暂缓(接入) | 无 LICENSE；仅借鉴"条款-证据-合规"任务设计 |
| CAMB | C+ | CC BY-NC-SA 4.0；法务澄清 NC 边界后仅取术语/分类/故障树/部分 QA |

## 需自建包装的项目

| 项目 | 评级 | 用途 |
| --- | --- | --- |
| NASA CRM / DPW / HLPW | S（战略核心） | CivilTransportCFD-Pack，L1-L6 六层任务；锁 Workshop 版本与 geometry revision |
| NASA Aviary | S | 总体设计与航程任务包；尺寸设计/约束优化/权衡/模型修复 |
| SuperWing + CRMpert | S−（必须做 Lite） | 4,239 构型/28,856 样本只取系数层（3.49TB 体流场不下载）；按几何构型划分 |
| OpenVSP / VSPAERO | A | 参数化几何任务包；NOSA 法务确认；回归测试快层 |
| pyCycle | A | 发动机循环与飞机-动力匹配；设计点/非设计点/喘振裕度约束 |
| SimJEB | A− | 支架 CAD-网格-FEA-优化；ODC 许可；加隐藏 FEA 复算层 |
| NASA GTM + JSBSim | A | 飞行动力学与控制；JSBSim 快层 + GTM 高价值层 |
| HiLiftAeroML | S(价值)/A−(优先级) | 180 构型×10 迎角 WMLES；66.9TB 只做 Lite（几何/工况/总力/截面/分离标签） |
| AirfRANS | B+ | 2D RANS 翼型；仅作 surrogate level-1；ODbL |
| NASA TMR | A− | 湍流模型验证层；CRM/HLPW 前置门槛 |

## 条件纳入 / 排除

- 条件纳入：AFBench（许可冲突待澄清）、BSCW/AePW（后续）、AircraftVerse（UAV 为主）、PDEBench（仅可压缩 NS 子集）、OpenConcept（排 Aviary/pyCycle 后）、CFDBench（许可不明暂缓）、BlendedNet（发布状态不稳）、ALUE/Pre-Flight（不进核心）、RepoSpace（不纳入）、HiLiftAeroML 全量（不进日常 CI）。

## 接入顺序（18 项）

1. cfdllm.cfdquery → 2. aeroengqa.gold → 3. scicode.physics → 4. cfdllm.cfdcode → 5. engdesign.open → 6. cfdllm.foam_basic → 7. aviary.transport_mission → 8. openvsp.geometry_aero → 9. pycycle.engine_cycle → 10. superwing.coeff_lite → 11. cadgen.local_validity → 12. simjeb.structure → 13. gtm.transport_control → 14. mechvqa.public_eval → 15. nasa_tmr.verification → 16. crm_dpw_hlpw.coarse → 17. hilift_aeroml.lite → 18. bscw.aeroelastic

v0.1 核心八件套：**CFDQuery、AeroEngQA、SciCode-Physics、CFDCodeBench、EngDesign-OPEN、FoamBench-Basic、Aviary-Mini、SuperWing-Lite** —— 可区分：只会问答的模型 / 会写代码不会工程的模型 / 会调工具不会判断结果的 Agent / 能完成多步可验证设计任务的 Agent。

## 五类 Adapter

qa_grounded（Exact/F1、证据支持、拒答率）/ code_exec（隐藏测试、数值容差）/ simulation_agent（可执行、收敛、物理合理、目标量误差）/ design_artifact（文件有效、几何接口质量、结构指标）/ field_prediction（系数误差、场误差、外推鲁棒）。

## 评分原则

1. 九维度报告，总分仅导航；
2. ValidityGate × (0.35 physics + 0.30 requirements + 0.20 objective + 0.15 robustness)，gate 失败条件硬编码；
3. LLM judge 不决定物理正确性，只评解释与审计质量；
4. 公共 benchmark 只用于可比，选型用开源工具动态生成的隐藏题。

## 主要来源

- CFDLLMBench: https://github.com/NREL-Theseus/cfdllmbench
- AeroEngQA: https://www.southampton.ac.uk/~sem03/aiaa-2025-preprint.pdf
- SciCode: https://github.com/scicode-bench/SciCode
- EngDesign: https://agi4engineering.github.io/Eng-Design/
- CADGenBench: https://github.com/huggingface/cadgenbench
- MechVQA: https://github.com/xiaofengShi/MechVQA
- CADBench: https://github.com/anniedoris/CADBench
- DesignQA: https://github.com/anniedoris/design_qa/
- CAMB: https://github.com/CamLLM/CamBenchmark
- NASA CRM: https://commonresearchmodel.larc.nasa.gov/
- DPW: https://www.aiaa-dpw.org/Workshop4/DPW4-geom.html
- Aviary: https://github.com/openmdao/Aviary
- SuperWing: https://huggingface.co/datasets/yunplus/SuperWing
- AeroTransformer: https://github.com/tum-pbs/AeroTransformer
- OpenVSP: https://github.com/openvsp/openvsp
- pyCycle: https://github.com/openmdao/pycycle
- SimJEB: https://simjeb.github.io/
- GTM: https://github.com/nasa/GTM_DesignSim
- JSBSim: https://github.com/JSBSim-Team/jsbsim
- HiLiftAeroML: https://huggingface.co/datasets/nvidia/HiLiftAeroML
- AirfRANS: https://github.com/Extrality/airfrans_lib
- NASA TMR: https://turbmodels.larc.nasa.gov/
- AFBench: https://github.com/hitcslj/AFBench
- AePW/BSCW: https://nescacademy.nasa.gov/workshops/AePW2/public/BSCW/publications
- AircraftVerse: https://arxiv.org/abs/2306.05562
- PDEBench: https://github.com/pdebench/PDEBench
- OpenConcept: https://github.com/mdolab/openconcept
- CFDBench: https://github.com/luo-yining/CFDBench
- BlendedNet: https://arxiv.org/html/2509.07209v1
- ALUE: https://github.com/mitre/alue
- RepoSpace: https://www.mdpi.com/2226-4310/12/6/498
