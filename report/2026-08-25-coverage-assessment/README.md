# Benchmark 覆盖范围深度评估（2026-08-25，structures 解零后更新）

> 接续 `report/2026-08-21-coverage-assessment/`（含其晚间与 08-22 追更）。数据来源：
> `registry/registry.yaml`（**40 条目**）、`tasks/*/` 任务 YAML 实数（**20 integrated = 2424**；
> 另 `tasks/.foam_tail` 20 题在制未转正）、`results/*/` provider 落盘实数（oracle 16/20、
> 双基线 20/20）、`results/nine-dim-{baseline,increment}*.md`、`results/harness-eval-2026-08-24.md`、
> `results/harness-lineage-2026-08-25.md`、**`results/structures-calculix-2026-08-24.md`（structures 解零）**、
> `report/2026-08-19-benchmark-survey.md`。
> 配图：`radar_nine_dim.png`（九维度）、`radar_harness.png`（评测体系）；生成脚本 `make_radars.py`（可复算）。

## 0. 一句话结论

**评测系统已完成三层九维骨架的九维全景闭合：20/40 基准 integrated、2424 任务、九维全部有数（structures 以开源 CalculiX 自建解零）、五类 adapter 与 6 类执行环境 live、集成项双基线全覆盖；评测对象已翻转为「harness」（四臂 H0-H3 矩阵、蒸馏脚手架谱系化、臂自动路由）。「懂航空」与「会工程」的分界已量化；剩余最大空洞是商业求解器线（Fluent/StarCCM+/MAPDL）与 simjeb/engdesign 原计划的商业 FEA 复算层。**

## 1. 总量盘点（registry 40 条目）

| 状态 | 数量 | 占比 | 较 08-24 上午变化 | 含义 |
| --- | --- | --- | --- | --- |
| **integrated** | 20 | 50% | 19→20（+calculix.fea_basic） | adapter 跑通 + 双基线落盘 |
| proposed | 4 | 10% | 不变 | 探查/许可清点完成，集成 blocked |
| paused-env | 2 | 5% | 不变 | dev/内网均无启动环境（openvsp、bscw） |
| deferred | 8 | 20% | 不变 | 许可或价值存疑，暂缓 |
| excluded | 6 | 15% | 不变 | 调研淘汰 |

任务量：**integrated 20 项共 2424 个任务 YAML**（08-21 时点 2119 → +305），另有
`tasks/.foam_tail` 20 题在制。锚点纪律：饱和锚 6/20（校准用，不参与模型排序）。

## 2. 已集成 19 项明细（评测能力主表）

| # | registry_id | adapter | env | 任务 | oracle 自检 | 基线（M3 / GLM 系） | harness 增益（H0→最优臂） |
| --- | --- | --- | --- | --- | --- | --- | --- |
| 1 | cfdllm.cfdquery | qa_grounded | qa | 90 | — | 0.8111 / 0.8667 | — |
| 2 | aeroengqa.gold | qa_grounded | qa | 80 | — | 0.8852 / 拒答 0.925 | — |
| 3 | mechvqa.public_eval | qa_grounded(free_vqa) | qa+VLM | 180 | 180/180 | 双 VLM：flash 0.3504 / 4.6v 0.4044 | — |
| 4 | gsm8k.math_reasoning | qa_grounded | qa | 250 | 250/250 | 0.9720 / 0.9600（锚点） | — |
| 5 | math500.math_reasoning | qa_grounded | qa | 500 | 500/500 | 0.9020 / 0.8860 | — |
| 6 | scicode.physics | code_exec | python_sandbox | 52 | — | 0.6738 / 0.477（gate 42/29） | — |
| 7 | cfdllm.cfdcode | code_exec | python_sandbox | 15 | — | 0.4700 / 0.586 | — |
| 8 | humaneval.python | code_exec | python_sandbox | 164 | 164/164 | 0.9817 / 0.9756（锚点） | — |
| 9 | humaneval.python_plus | code_exec | python_sandbox | 164 | 164/164 | 0.9268 / 0.9207 | — |
| 10 | mbpp.sanitized | code_exec | python_sandbox | 257 | 257/257 | 0.9455 / 0.9416（锚点） | — |
| 11 | mbpp.sanitized_plus | code_exec | python_sandbox | 222 | 222/222 | 0.8198 / 0.8447 | — |
| 12 | cfdllm.foam_basic | simulation_agent | openfoam_dev | 110 | 110/110 | 0.000 / 0.000（双模型真实边界） | sub10：M3 0→**0.40**（H2v2c，结构层开、physics 仍 0） |
| 13 | aviary.transport_mission | simulation_agent | python_sandbox | 27 | 27/27 | 0.2222 / 0.3111（过 gate 即高分） | — |
| 14 | pycycle.engine_cycle | simulation_agent | python_sandbox | 28 | 28/28 | 0.0393 / 0.0000（双模型全灭） | sub10：M3 0→**1.00**（H2 脚手架） |
| 15 | gtm.transport_control | simulation_agent(matlab) | matlab | 25 | 25/25 | 0.9800 / 0.8900（可达域锚点） | — |
| 16 | gtm.transport_control_hard | simulation_agent(matlab) | matlab | 17 | 17/17 | 0.7059 / 0.6520 / glm-5.3 0.6471 | sub10：M3 0.65→**0.80**；5.3 0.525→0.60 |
| 17 | superwing.coeff_lite | field_prediction | data_only | 100 | 100/100 | 0.4415 / 0.4135 | ML 参照 0.7525（RF 正例） |
| 18 | hilift_aeroml.lite | field_prediction | data_only | 100 | 100/100 | 0.4855 / 0.4885 | ML 参照 0.904（RF 正例） |
| 19 | cadgen.local_validity | design_artifact | python+OCP | 22 | 22/22 | 0.7083 / 0.6515 / glm-5.3 0.8636 | 全量：M3→**0.9792**(H3)；5.3→**1.0000**(H2) |
| 20 | calculix.fea_basic | simulation_agent(ccx_fea) | calculix_native | 21 | 21/21 | **0.2381** / — / glm-5.3 **0.3810**（structures 维，08-24 解零） | —（H2 脚手架为下一个高价值臂） |

- 双基线覆盖 **20/20**（mechvqa 为双 VLM；gtm_hard/ccx 为固定对 {minimax-m3, glm-5.3}）；
  oracle 满分自检 **16/20**（qa_grounded 两项与 scicode/cfdcode 无 oracle 目录，判分依赖规则与 stub 地板）。
- 分数仅导航用（scoring/README §1）；gate 失败率与原因分布才是决策口径。
- v0.3 起模型间排序不再是评测目标；双模型对照表转为历史档案，固定对 {minimax-m3, glm-5.3}。

### 未集成 20 项清单（按阻塞原因归类）

| 阻塞类型 | 条目 |
| --- | --- |
| 商业求解器环境缺失 | simjeb.structure(ANSYS MAPDL，proposed)、nasa_tmr.verification(Fluent/StarCCM+，proposed)、crm_dpw_hlpw.coarse(同，needs-version-lock)、bscw.aeroelastic(气弹链，paused-env) |
| 原生二进制缺失 | openvsp.geometry_aero（paused-env，needs-legal-review） |
| 判分不可复现（待议） | engdesign.open（官方 eval 脚本未发布；收窄子集 28 题已清点，confirmed-split） |
| 许可受阻/待核 | designqa.fsae(无许可)、afbench.airfoil(模糊)、camb.selective(NC 边界)、cadbench.cadquery(逐任务审计)、aircraftverse/pdebench/airfrans/openconcept(待核) |
| 调研淘汰（excluded） | alue_preflight / repospace / cfdbench / blendednet / hilift_full / runtime_commonsense |

## 3. 九维度覆盖（雷达图 1：`radar_nine_dim.png`）

| # | 维度 | 在册基准 | 已集成 | 覆盖度 | 基线可得 | 证据要点（08-25 时点） |
| --- | --- | --- | --- | --- | --- | --- |
| 1 | knowledge | cfdquery、aeroengqa、mechvqa、camb(deferred) | 3/4 | 0.75 | ✅ | 文本 0.85+；VLM 0.35-0.40「看得见、判不稳」；单厂商 VLM |
| 2 | coding | scicode、cfdcode（+6 通识锚） | 2/2 | **1.00** | ✅ | 领域科学代码 0.47-0.67 vs 通识 0.82-0.98 分水岭成立；+变体压泄漏 |
| 3 | cad_geometry | cadgen、openvsp(paused) | 1/2 | 0.50 | ✅ | cadgen 22 题+H3 后 M3 0.98/5.3 1.0；openvsp 仍卡环境 |
| 4 | cfd | superwing、hilift、foam_basic、nasa_tmr、crm | 3/5 | 0.60 | ✅+ML 正例 | LLM 系数回归差 ML 4.7-19×；foam 0/110 双败（H2 后结构层开、physics 0） |
| 5 | structures | calculix.fea_basic、simjeb、engdesign | 1/3 | **0.33** | ✅ | 08-24 解零（CalculiX 自建 21 题，双基线 0.24/0.38 正落区分带）；simjeb/engdesign 仍卡商业栈/官方判分 |
| 6 | propulsion | pycycle | 1/1 | **1.00** | ✅(厚) | 28 题；H0 双模型全灭 → H2 脚手架 M3 1.0（「知识注入=0→1」核心证据） |
| 7 | flight_control | gtm v1+hard | 1/1 | **1.00** | ✅ | v1 锚点 0.98/0.89 + hard 区分带 0.71/0.65/0.65；MATLAB live |
| 8 | mdo_design | aviary、engdesign、crm | 1/3 | 0.33 | ✅(厚) | 27 题；过 gate 即满分（门槛在可执行脚本）；crm 待商业 CFD |
| 9 | robustness_audit | 横切全部 | 部分 | 0.60 | 部分 | 确定性双跑仅过 gate 子集；沙箱越界曾有 15 例信号；manifest 审计达标 |

**读图**：形状从「偏科五角」→「八维有数、独缺结构」→ **九维全景闭合（08-24 晚）**——structures 轴以开源 CalculiX 自建解零（0→0.33，基线可得 0→1.00）；有数各轴基线可得性全部拉满（红线外包蓝线），唯 robustness_audit 仍靠横切证据支撑、无独立承载。

## 4. 评测体系能力（雷达图 2：`radar_harness.png`，9 轴）

| 轴 | 08-24 上午 | 08-24 晚 | 口径 |
| --- | --- | --- | --- |
| 公共可比层 | 0.95 | 0.95 | 11 基准（qa 5 含双 VLM + code_exec 6 含 +变体）双基线；HE+/MBPP+ 抗泄漏纯测试升级，排序反转可测 |
| 工程可执行层 | 0.80 | **0.82** | 9 基准端到端可运行（foam/aviary/pycycle/superwing/hilift/cadgen/gtm×2/**calculix**）；商业 CFD/FEA 全缺 |
| 受控隐藏层 | 0.30 | 0.30 | 生成器+几何分组划分纪律；题库轮换与 hidden-public 分差监控未建 |
| 多模态评测 | 0.55 | 0.55 | VLM 通道+free_vqa 判分+双 VLM 基线；单厂商（GLM 系），无第二来源 |
| Adapter 类型 | 1.00 | 1.00 | 5/5：qa_grounded×5 / code_exec×6 / simulation_agent×5 / field_prediction×2 / design_artifact×1 |
| 环境覆盖 | 0.56 | **0.62** | live 6 类：qa / python_sandbox / openfoam_dev / data_only / matlab / **calculix_native**（新）；缺 commercial_cfd/fea、原生 openvsp、内网栈 |
| 判分自检 | 0.79 | **0.80** | oracle 满分自检 16/20（+calculix 21/21，max_rel_err=0）；4 项无 oracle 目录 |
| 可复现审计 | 0.90 | **0.92** | run_manifest+seed+sha256+PROVENANCE 全覆盖；git 已 init（8-24 起 manifest 带 commit） |
| Harness 臂评测 | 0.75 | 0.75 | 四臂 H0-H3×{pycycle,foam} 矩阵 20/20 实测；scaffold 谱系化 4/5 命中；arm_router 策略表生产化 |

## 5. v0.3 范式转向要点（harness-first，评测能力的新增维度）

- **被测对象翻转**：内网离线生产环境 → 模型锁定固定对 {minimax-m3, glm-5.3}，harness 成为唯一变量；模型间排序退役。
- **四臂协议**：H0 单发 / H1 反馈(iterate) / H2 脚手架(蒸馏文档注入) / H3 脚手架+反馈——评分语义不变，增益=臂间均分差。
- **核心实证**：蒸馏工作流是「不可为→可为」开关（M3+pycycle 0/10→10/10）；H1 单独全零（反馈不救语料外知识）；模型×臂有交互（遵循型吃 H2、改写型需 H3）。
- **边界发现**：glm-5.3 长度墙（32768 token 被思考耗尽，数据矩阵截断）；foam physics 层非 prompt 知识可注入（数值稳定性=配置×求解器×硬件）。
- **资产**：3 份已定稿 scaffold（pycycle/foam v2.4/cadgen/gtm-hard）+ `runners/arm_router.py` 策略表路由。

## 6. 缺口清单（按优先级）

1. ~~structures 维零覆盖~~（**2026-08-24 已解零**：calculix.fea_basic 自建 21 题 integrated，双基线 0.24/0.38 正落区分带；simjeb 原计划的商业 FEA 复算层仍为内网移植目标）；
2. **商业求解器线全缺**：nasa_tmr / crm / simjeb / bscw 四项 blocked-env；CFD 判分仅 OpenFOAM 单后端，FEA 判分仅 CalculiX 单后端——无 Fluent/StarCCM+/MAPDL 交叉验证；
3. **受控隐藏层停在建制试点**：防记忆题库轮换、hidden-public 分差监控（scoring §5 承诺）未闭环——语料泄漏风险随通识锚饱和升高；
4. **多模态单厂商**：VLM 通道仅 GLM 系（flash+4.6v 同源），MiniMax/Gemini 通道事实性缺失，mechvqa 结论的外部效度受限；
5. **mdo_design 仅 1/3**：engdesign/crm 未进，Aviary 单基准承载「总体设计」整维，过 gate 即满分的区分度模式未变；
6. **foam physics 层判分保真**：H2v2c 后结构层开但 NMSE 全 0（GT 与 scaffold 算例在 qemu docker 均发散），需逐项消融定位发散源；
7. **calculix 加厚路径**（structures 维厚度）：ccx 侧应力类任务（*EL PRINT von Mises/带孔板 Kt）、非线性（*PLASTIC）、H2 脚手架（CalculiX 方言语料稀缺，pycycle 式 0→1 机会）；
8. **robustness_audit 无独立承载**：确定性双跑未覆盖全部任务，越界检测靠沙箱告警横切汇总；
9. **oracle 缺口 4/20**：cfdquery/aeroengqa/cfdcode/scicode 无 oracle 满分自检目录。

## 7. 强项（相对优势）

- **判分纪律**：ValidityGate 先于子分、gate 失败原因强制落盘、oracle 满分自检、LLM judge 禁止替代物理判分；误封教训（os.chmod、add_subsystem）均已修正固化；
- **抗泄漏设计**：同提示纯测试升级（HE+/MBPP+）分离语料残余分；field_prediction 几何分组内插/外推分报；
- **正例参照**：ml-superwing / ml-hilift 给「LLM 不会」以数量级对照；harness 四臂矩阵给「harness 有多大用」以定量上界；
- **可复现性**：全部结果离线可复算（run_manifest.rerun_command / seed / sha256 / PROVENANCE）；git 已初始化；
- **区分度管理**：锚点/区分带口径工具化（bench_stats），哑铃形分布如实报告，饱和题不参与排序；calculix.fea_basic 首日即落区分带（0.24/0.38，反力键独立捕获载荷路径错误）；
- **harness 知识产权**：3 份自检过（裸跑收敛/实跑出时间目录）的蒸馏 scaffold + 防泄漏纪律 + 臂路由器——评测本身开始产出可迁移工程资产。

## 8. 建议下一步（若继续投入）

1. calculix 谱系化：H2 脚手架（INP 骨架+折行纪律+集合名契约）与应力类任务加厚（*EL PRINT/带孔板 Kt/非线性）——pycycle 式「知识注入 0→1」高价值机会；
2. foam 发散源二分消融（一个会话量级）——当前 sub10 gate 8+/10 但 physics 0，判分保真是 harness 增益兑现的卡点；
3. 第二厂商 VLM 通道（或 mechvqa 降级标注外部效度），消除单源结论风险；
4. 隐藏层轮换与 hidden-public 分差监控闭环，兑现 scoring §5；
5. 内网移植演练：arm_router + scaffold 资产 + 固定模型对 + ccx（源码编译/离线二进制）打包，验证「评测能力」在生产环境的可部署性；
6. simjeb/engdesign 于内网商业 FEA 就绪后排期（structures 维从 0.33 加厚到多后端互证）。
