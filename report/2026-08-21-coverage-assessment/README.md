# Benchmark 覆盖范围深度评估（2026-08-21）

> **同日晚间更新**：本文 §5 建议的 1/2/3 三项（mechvqa VLM 通道、cadgen design_artifact
> 接线、pycycle/aviary 扩题）当日已完成——integrated 15→17、任务 2119→2376、
> cad_geometry 0→0.50、多模态 0.05→0.55、adapter 5/5 类接线。终值与证据见
> `results/nine-dim-increment-2026-08-21.md`；下文保留评估时点快照。

> 数据来源：`registry/registry.yaml`（38 条目）、`tasks/*/`（任务 YAML 实数）、`results/*/`（provider 落盘实数）、
> `results/nine-dim-baseline-2026-08-19.md` / `M4-summary.md` / `batch2-round1-summary.md` / `batch3-*-summary.md`。
> 配图：`radar_nine_dim.png`（九维度）、`radar_harness.png`（评测体系）；生成脚本 `make_radars.py`（可复算）。

## 0. 一句话结论

**评测系统已从"答题器"长成三层九维框架的骨架：15/38 基准 integrated、2119 个任务、双模型基线（GLM-4.6 + MiniMax-M3）全覆盖、五类 adapter 落地四类；但九维度中 CAD/几何、结构、飞控三维为零覆盖，多模态与商业求解器（Fluent/StarCCM+/MAPDL/MATLAB）两条环境线未打通，受控隐藏层仅试点——「懂航空」可测、「会工程」刚立起门框。**

## 1. 总量盘点（registry 38 条目）

| 状态 | 数量 | 占比 | 含义 |
| --- | --- | --- | --- |
| **integrated** | 15 | 39% | adapter 跑通 + 基线报告落盘 |
| staged | 1 | 3% | 数据镜像完成、通道受阻（mechvqa 多模态） |
| proposed | 6 | 16% | 探查/许可清点完成，多数 blocked-env |
| paused-env | 2 | 5% | dev/内网均无启动环境（openvsp、bscw） |
| deferred | 8 | 21% | 许可或价值存疑，暂缓 |
| excluded | 6 | 16% | 调研淘汰（alue_preflight/repospace/cfdbench/blendednet/hilift_full/runtime_commonsense） |

任务量：**integrated 15 项共 2119 个任务 YAML**（另有 mechvqa 1185 题已镜像未出题）。

## 2. 已集成 15 项明细（评测能力主表）

| # | registry_id | adapter | env_class | 任务数 | oracle 自检 | M3 基线 | GLM-4.6 基线 | ML/oracle 参照 |
| --- | --- | --- | --- | --- | --- | --- | --- | --- |
| 1 | cfdllm.cfdquery | qa_grounded | qa | 90 | — | 0.8111 | **0.8667** | stub 0 |
| 2 | aeroengqa.gold | qa_grounded | qa | 80 | — | **0.8852** | 拒答 0.925/evid 0.894 | stub 0 |
| 3 | scicode.physics | code_exec | python_sandbox | 52 | — | **0.6738**(gate 42/52) | 0.477(gate 29/52) | stub 0 |
| 4 | cfdllm.cfdcode | code_exec | python_sandbox | 15 | — | 0.4700(gate 8/15) | **0.586**(gate 11/15) | stub 0 |
| 5 | cfdllm.foam_basic | simulation_agent | openfoam_dev | 110 | **110/110** | 0.000(0/110) | 0.000(0/110) | oracle 满分证判分管线 |
| 6 | aviary.transport_mission | simulation_agent | python_sandbox | 8 | 8/8 | 0.250 | 0.375(gate 3/8) | oracle 8/8 |
| 7 | pycycle.engine_cycle | simulation_agent | python_sandbox | 7 | 7/7 | 0/7 幻觉 API | 0/7 幻觉 API | oracle 7/7 |
| 8 | superwing.coeff_lite | field_prediction | data_only | 100 | 100/100 | 0.4415 | 0.4135 | **ml-superwing 0.7525** |
| 9 | hilift_aeroml.lite | field_prediction | data_only | 100 | 100/100 | 0.4855 | 0.4885 | **ml-hilift 0.904** |
| 10 | gsm8k.math_reasoning | qa_grounded | qa | 250 | 250/250 | **0.9720** | 0.9600 | oracle 1.0 |
| 11 | math500.math_reasoning | qa_grounded | qa | 500 | 500/500 | **0.9020** | 0.8860 | oracle 1.0 |
| 12 | humaneval.python | code_exec | python_sandbox | 164 | 164/164 | **0.9817** | 0.9756 | oracle 1.0 |
| 13 | humaneval.python_plus | code_exec | python_sandbox | 164 | 164/164 | **0.9268** | 0.9207 | oracle 1.0 |
| 14 | mbpp.sanitized | code_exec | python_sandbox | 257 | 257/257 | **0.9455** | 0.9416 | oracle 1.0 |
| 15 | mbpp.sanitized_plus | code_exec | python_sandbox | 222 | 222/222 | 0.8198 | **0.8447** | oracle 1.0 |

- **双模型基线覆盖：15/15**；oracle 满分自检 11/15（qa_grounded 两项与 scicode/cfdcode 无 oracle 目录，判分依赖规则与 stub 地板）。
- 分数仅导航用（scoring/README §1）；gap 失败率与原因分布才是决策口径。

### 未集成 23 项清单（按阻塞原因归类）

| 阻塞类型 | 条目 |
| --- | --- |
| **环境缺失（dev 无商业栈）** | simjeb.structure(ANSYS MAPDL)、nasa_tmr.verification(Fluent/StarCCM+)、crm_dpw_hlpw.coarse(同)、gtm.transport_control(MATLAB)、openvsp.geometry_aero(无原生二进制)、bscw.aeroelastic(无气弹链) |
| **多模态通道缺失** | mechvqa.public_eval（镜像已落，VLM provider 未接） |
| **判分不可复现（待议）** | engdesign.open（官方 eval 脚本未发布；收窄子集 28 题已清点） |
| **三重前置（adapter+多模态+GT 私有）** | cadgen.local_validity |
| **许可未核/受阻** | designqa.fsae(无许可)、afbench.airfoil、camb.selective(许可模糊)、cadbench.cadquery(逐任务审计)、aircraftverse/pdebench/airfrans/openconcept(待核) |

## 3. 九维度覆盖（雷达图 1：`radar_nine_dim.png`）

| # | 维度 | 在册基准 | 已集成 | 覆盖度 | 基线可得 | 证据要点 |
| --- | --- | --- | --- | --- | --- | --- |
| 1 | knowledge | cfdquery、aeroengqa、mechvqa(staged)、camb(deferred) | 2/4 | 0.50 | ✅双基线 | M3 0.848/GLM 更优；aeroengqa 引用纪律强、事实作答弱 |
| 2 | coding | scicode、cfdcode（+humaneval/mbpp 6 项通识锚） | 2/2 | **1.00** | ✅双基线 | 领域科学代码 0.47-0.67 vs 通识编程 0.82-0.98——分水岭成立 |
| 3 | cad_geometry | cadgen、openvsp(paused) | 0/2 | **0.00** | ❌ | design_artifact adapter 未接线 |
| 4 | cfd | superwing、hilift、foam_basic、nasa_tmr、crm | 3/5 | 0.60 | ✅双基线+ML 正例 | LLM 系数回归差 ML 4.7-19×；foam 0/110 双模型同败 |
| 5 | structures | simjeb、engdesign | 0/2 | **0.00** | ❌ | 无 MAPDL；engdesign 判分 blocked |
| 6 | propulsion | pycycle | 1/1 | **1.00** | ✅双基线(薄) | 仅 7 任务，双模型 0/7 幻觉 API——边界清晰但样本薄 |
| 7 | flight_control | gtm | 0/1 | **0.00** | ❌ | 无 MATLAB（JSBSim 快层许可未核） |
| 8 | mdo_design | aviary、engdesign、crm | 1/3 | 0.33 | ✅双基线(薄) | 仅 8 任务；过 gate 即满分的区分度有限 |
| 9 | robustness_audit | 横切全部基准 | 部分 | 0.60 | 部分 | 确定性双跑仅覆盖过 gate 子集；foam 曾暴露 15 例越界尝试；审计日志达标 |

**读图结论**：形状呈"偏科五角"——知识/编程/CFD/动力/总体有数据，CAD/结构/飞控三轴塌陷为 0；有数据的轴里 propulsion 与 mdo 只有 7-8 个任务，证据厚度不足。

## 4. 评测体系能力（雷达图 2：`radar_harness.png`）

| 轴 | 分值 | 口径 |
| --- | --- | --- |
| 公共可比层 | 0.95 | 10 个基准（qa 4 + code_exec 6，含 +加强测试变体）双基线落盘；HE+/MBPP+ 抗泄漏纯测试升级，排序反转可测 |
| 工程可执行层 | 0.65 | 5 基准端到端可运行（foam/aviary/pycycle 仿真执行 + superwing/hilift 数据预测）；商业求解器全缺 |
| 受控隐藏层 | 0.30 | aviary 隐藏动态生成器 + pycycle 试点 1 例 + field_prediction 几何分组划分纪律；无题库轮换与泄漏监控 |
| 多模态评测 | 0.05 | mechvqa 1185 题已镜像（383MB），VLM provider 未接 |
| Adapter 类型覆盖 | 0.80 | 五类已实现、四类接线（qa_grounded×4 / code_exec×6 / simulation_agent×3 / field_prediction×2）；design_artifact 0 |
| 评测环境覆盖 | 0.50 | live：qa / python_sandbox / openfoam_dev / data_only；缺：commercial_cfd / commercial_fea / matlab / CATIA / 内网栈 |
| 判分自检 | 0.73 | oracle 100% 自检 11/15；两轮判分器误封缺陷已修正并固化教训 |
| 可复现审计 | 0.90 | run_manifest + rerun_command + seed + sha256 + PROVENANCE 全覆盖；历史 manifest git_commit=unknown |

## 5. 缺口清单（按优先级）

1. **三维零覆盖**（cad_geometry / structures / flight_control）：九维雷达 3/9 轴为 0，全部卡环境或 adapter 前置——design_artifact 接线 + intranet 商业栈是唯一解阻路径；
2. **多模态通道**：mechvqa 数据已在盘上，缺 expect="vlm" 的 provider——是低成本补齐 knowledge 维的下一步；
3. **薄证据维**：propulsion 7 题、mdo 8 题，不足以支撑版本选型结论；pycycle 高度权衡任务待参数化 OD 序列；
4. **受控隐藏层**：仅有试点。防记忆题库轮换、hidden-public 分差监控（scoring §5）未建；
5. **商业求解器线**：nasa_tmr/crm/simjeb/gtm 四项全 blocked-env，内网移植前 CFD 判分只剩 OpenFOAM 单后端；
6. **robustness_audit**：确定性双跑未覆盖全部任务、无独立基准承载。

## 6. 强项（相对优势）

- **判分纪律**：ValidityGate 先于子分、gate 失败原因强制落盘、oracle 满分自检、LLM judge 禁止替代物理判分（scoring §3/§4）——两轮误封教训（os.chmod、add_subsystem 子串）均已修正固化；
- **抗泄漏设计**：同提示纯测试升级（+变体）分离"语料残余分"；field_prediction 几何分组划分（内插/外推分报）；
- **正例参照**：ml-superwing / ml-hilift 让「LLM 不会」有了数量级对照（差 4.7-19×）；
- **可复现性**：全部结果可离线复算（stub/oracle 逐字节），API 基线带 seed/manifest；
- **画像分化有效**：双模型在 scicode/cfdcode/foam 上强弱势互补，证明基准具备区分模型画像的分辨力。

## 7. 建议下一步（若继续投入）

1. 接 VLM provider 放 mechvqa（staged→integrated，knowledge 维 +1，多模态 0.05→0.5）；
2. design_artifact adapter 用 cadgen 或 aircraftverse.selective 先接一个纯 Python 可判分基准（cad_geometry 0→0.5）；
3. pycycle/aviary 扩题（各 7-8 → ≥25），补厚 propulsion/mdo 证据；
4. 内网 intranet 环境就绪后排 simjeb/gtm/nasa_tmr/crm 四项（structures/flight_control 解阻 + 环境覆盖 +0.25）；
5. 建隐藏层轮换与 hidden-public 分差监控闭环，兑现 scoring §5 承诺。
