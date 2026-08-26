# COMACBench 深度巡查报告（2026-08-26）

> 方法：多 agent 编排审计——8 条独立 lane 并行（判分纪律/adapter 代码/任务契约/许可
> SSOT/gold 质量/结果完整性/泄漏效度/报告口径），critical/major 发现逐条**对抗复核**
> （独立复核员试图证伪，亲读证据行号）。共 26 个审计 agent + 8 个复核 agent。
> 全程只读纪律；本报告 §6 列出的「立即整改」由 orchestrator 在审计后执行并回归验证。
> 每条发现带 文件:行号 证据；复核裁定标注（confirmed/partial/refuted）。

## 0. 总裁定

**设计合理性：扎实（结构性优势真实成立）；工程深度：高（可复算性罕见地好）；
主要风险不在判分数学，而在「治理面」——SSOT 同步纪律跟不上交付速度，以及三处
判分器边界缺陷（均在新接入的办公基准上，均不影响既有已记录结论的方向）。**

| 维度 | 裁定 |
| --- | --- |
| 判分纪律（gate 先行/无 judge/失败模式） | ✅ 结构性成立，非文案（复核确认） |
| 结果可复算性 | ✅ 133 run 中 132 个 summary 与 JSON 独立重算一致；对外报告数字全部可溯源 |
| 任务契约机械一致性 | ✅ 2513 任务 0 失败（必填字段/id/摘要/资产 100% 一致） |
| gold 质量 | ✅ 抽查全部可独立复算，容差留 6-10 倍余量，零题面泄漏 |
| 判分器边界（新增办公基准） | ⚠️ 2 条 confirmed major + 1 条潜在崩溃路径 |
| SSOT 治理（license/env/registry/覆盖报告） | ⚠️ 4 条 confirmed major（文档滞后/错数字/漏行） |
| 效度声明诚实度 | ⚠️ 总体诚实；1 条排序结论强于证据、锚点账本滞后 |

## 1. 结构性优势（复核确认，非泛泛而谈）

1. **gate=0 置零是结构实现**：五 adapter 全部正常路径经 `aggregate_score` 乘
   validity_gate（common.py:165-171），提前返回分支均显式 gate=0+score=0——
   「解释不能补偿不可用结果」不可绕过；
2. **LLM judge 禁令零代码路径**：全仓 grep 无 judge 进 score；oracle 语义 =
   「必须 100 分否则判分器有 bug」（providers.py:9-10），21 个 oracle 目录重算均分
   全部恰为 1.0；
3. **gold 与判分单一事实源 + 全链自检**：生成器直接 import 判分算子并以 gold 实跑
   断言满分（gen_tasks_cbsk/engtable）；2513 任务的 prompt_sha256/oracle_source/
   assets digest 全量重算 100% 一致；
4. **反馈迭代无答案泄漏**：build_feedback_prompt 白名单键核对，gold 值键在 gate=0
   失败详情中不存在；scaffold 参数与任务参考 grep 无重叠；
5. **镜像红线执行到位**：data/ 27 个子目录全部映射在册条目、无孤儿数据；excluded
   六条零落盘；needs-verification 条目盘上确无其数据（gtm PROVENANCE 明确未镜像）；
6. **实验/基线隔离实证**：bench_stats 排除规则经带/无规则对照实验验证，24 个实验
   目录（-iter/-H*/sub10）未污染任何基线数字。

## 2. Major 发现（全部经对抗复核）

### 判分器（3 条）

| # | 发现 | 位置 | 复核 |
| --- | --- | --- | --- |
| M1 | **awext json_extract 对离散字段放 2% 容差**：amendment_year 2022 vs 1990、cycles 1000 vs 990 均判命中——9 字段中 2 个离散字段（≈22%）可用错误值得分；simulation_agent 已有 exact_keys 机制未沿用 | qa_grounded.py:255-257 | **confirmed/high**（复现得满分 1.0） |
| M2 | **ssb formula_cell sheet 回退 + requirements 恒 1.0**：answer_sheet 缺失静默读首表（声明契约不检验），权重 0.5 下任何可执行输出有 0.5 地板；25 golden 中 2 个 answer_sheet 非首表 | design_artifact.py:992/1037 | **confirmed/high** |
| M3 | **_SIM_FAIL 未定义**：soffice 重算失败分支触发即 NameError→crash 误归类（voided），模型失败被伪装成 harness 故障；历史数据未触发（0 例） | design_artifact.py:984 | **partial/high**（影响=分类失真而非分数，已当场修复） |

### SSOT 治理（4 条）

| # | 发现 | 位置 | 复核 |
| --- | --- | --- | --- |
| M4 | **license-notes 漏 5 行**（含 SSB 外部 CC-BY-SA 数据集 42MB 已落盘无放行记录），违反「先 notes 后镜像」自定门禁 | license-notes.md | **confirmed/high**（已回填） |
| M5 | **registry mbpp_plus note 是 humaneval_plus 的逐字复制**：oracle 164/164 vs 实际 222/222、GLM 夸大 7.6pp、M3 夸大 10.7pp、证据路径指向错误基准 | registry.yaml:494 | **confirmed/high**（已勘误） |
| M6 | **env-matrix 滞后 12 条 + 自相矛盾**：qa/python_sandbox/matlab 覆盖列落后 registry；missing 行残留已恢复的 foam_basic；ssb 的 soffice 依赖无承载 | env-matrix.md §1 | **confirmed/high**（已同步） |
| M7 | **aviary rerun_command 解释器失真**：5 个 run 记录 .venv（无 aviary）而实跑 .venv-aviary；按 manifest 字面重跑会环境性压分 | simulation_agent.py:731 | **partial/high**（核心成立；已改 sys.executable） |

### 结果与报告（2 条）

| # | 发现 | 位置 | 复核 |
| --- | --- | --- | --- |
| M8 | **awdoc oracle 声称 18/18 但未落盘**（cp 静默失败）→ 覆盖报告 21/25 计数失实（应为 20/25）；office-wave2 报告声称无盘上证据 | results/awdoc…/2026-08-26/ | 当场核実+**已补跑落盘 18/18**（21/25 恢复成立） |
| M9 | **0819 批溯源断链**：29/133 manifest git=unknown 且 rerun 指向已删目录——v0.1 九维基线的判分代码版本永久不可回放（result JSON 本身在且重算一致） | results/*/2026-08-19 | 成立（历史不可逆，标注勘误） |

### 效度声明（1 条）

| # | 发现 | 复核 |
| --- | --- | --- |
| M10 | **hidden_dynamic 声明 4 条但 0 个 hidden 任务在运营**：2513 任务 hidden 全 false，运行时无任何代码消费 hidden/answers.b64——scoring §5 防记忆闭环结构性缺失（覆盖评估已列缺口但 registry 标志失真，gtm v1 虚标） | 成立（major，二选一修复：接线或改标志） |

## 3. Minor 摘选（22 条，全文见各 lane 存档）

**判分器**：match_sketch 对「弦替代样条」崩溃→FM_CRASH 误归类（design_artifact.py:242）；closed_profiles 退化几何计环（:361）；_xlsx_match 近零容差比注释紧 200 倍（:594）；grade_json_extract 字符串归一化单侧（qa_grounded.py:265）；oracle 旁路五 adapter 不一致（simulation_agent/code_exec 豁免静态检查、field_prediction 直填 true）；code_exec 两处分母收缩可虚高（scicode error 行、cfdcode 异常字段剔除）；SSB 生成器模板与盘上 YAML 漂移（重生成会丢 filesystem-copy/oracle_source）；scaffold sha256 未落 manifest（与注释声明不符）；拒答短语表 'unknown' 误报。
**纪律/契约**：FM_ENV_MISMATCH/OOM/TOOL_VIOLATION/TIMEOUT 四常量零产生点（死词汇表）；TaskSpec 校验弱（畸形任务深处崩→crash）；DEFAULT_WEIGHTS 五处定义已漂移一处；environment_digest 不含 solvers 代码与外部求解器版本（ccx/soffice/matlab 升级不可检测）；iterate applicability 键名写错恒 False（已修）；cfdquery/mechvqa 270 题无 prompt_sha256（漂移不可检测）。
**报告口径**：覆盖 README 三时点数字混存（19/22/25 与 16/20/21）；harness 雷达两轴无算术口径（已改可复算）；雷达参照线 cad_geometry 0.50 应为 0.33（已修）；MBPP+ 排序反转结论建立在 1-3 题噪声上无显著性检验、且 mbpp 系属锚点集（batch3-wave2:44）；scoring §6 承诺三组误差只交付两组、CRMpert 替换未列缺口；simjeb「ODC Attribution 类」未定变体却标 confirmed。
**其他**：ssb glm 一例 summary/json 不一致（并行覆写，1/133）；4 个半截 run 目录残留；.foam_tail 20 题为已合并残留副本；calculix 模态题 boilerplate 自相矛盾（not printed vs parses set names）。

## 4. 设计合理性裁定（针对「设计」本身）

1. **三层九维+办公维框架**：维度划分与 adapter 分类经得起审——五类 adapter 各自
   判分语义清晰、模式扩展（sketch_2d/xlsx_table/doc_document/formula_cell/
   json_extract）证明 seam 干净；
2. **「gate 失败率优先于均分」「锚点不参与排序」两条纪律是本仓最有价值的测评学
   决策**——审计未发现任何违反（除 §3 所列 MBPP+ 排序表述一处，属结论措辞过强）；
3. **v0.3 harness-first 转向**（被测对象= harness 而非模型）与固定模型对设计自洽，
   四臂矩阵方法论成立；
4. **系统性弱点是「手工 SSOT 回填」**：registry/notes/env-matrix/覆盖报告四个文档
   靠人工同步，交付速度（3 天 7 基准）远超回填速度——major 里 4/10 条源于此。
   根治方案是机械化（integrated_note 数字从 results 重算生成、notes 行从 registry
   派生校验），已列入 §6 建议。

## 5. 深度裁定（针对「深度」本身）

- 正例：判分算子与生成器同源+gold 实跑断言；解析互证（calculix）；泄漏扫描机械
  化；133 run 全量对账。这套自检密度在同类 harness 中罕见。
- 负例：隐藏层 0 运营（声明与实现脱节）；效度威胁（语料污染对锚点的意义、
  hidden-public 分差）只有声明没有监控闭环；无显著性检验（1-3 题分差下排序结论）。
- 结论：**深度达标但集中在「判分正确性」，「效度工程」（防泄漏、防记忆、统计
  显著性）是下阶段的真实深水区。**

## 6. 立即整改（本次已完成，全部零分数影响+回归验证）

| 项 | 动作 |
| --- | --- |
| M3 | design_artifact 补 `_SIM_FAIL` 常量（分支从未触发，零行为变化） |
| M8 | awdoc oracle 补跑落盘 results/…/2026-08-26/oracle/（18/18 mean 1.0） |
| M5 | registry mbpp_plus note 勘误为实测值（222/222、0.8198/0.8447）+ engtable/awdoc 补 anchor_note |
| M4 | license-notes 回填 5 行 + 取值表补 confirmed-selfbuilt/confirmed-adapted + 表头日期 |
| M6 | env-matrix §1 覆盖列同步（qa 8/python_sandbox 17/matlab 2）+ missing 行去 foam_basic 残留 + Phase-E soffice 专条 + matlabengine 废弃标注 |
| — | SSB PROVENANCE 重写（许可证据链+SA/BY 义务，对标 superwing） |
| — | qa_grounded 死代码删除；iterate applicability 键名修复 ×2；simulation_agent rerun 改 sys.executable |
| — | 雷达参照线 0.33 修复；harness 轴全部改为可复算口径（6/9、21/25、13 基准）；覆盖 README §2 补至 25 行+计数统一 |
| 回归 | 三 runner 语法+oracle/stub 冒烟全过；awext oracle 12/12 重验 |

## 7. 待办 backlog（按优先级，需判分语义变更/基线重跑者未擅动）

1. **M1 修复**：grade_json_extract 增 exact_keys（年份/次数精确）→ awext 双基线重跑；
2. **M2 修复**：formula_cell 删首表回退（缺 sheet→gate=0）+ requirements 真实结构检查 → ssb 双基线重跑；
3. **M10 裁决**：hidden 层接线（generator+answers.b64 运行时出题+分差监控）或将 4 条 hidden_dynamic 改 false 如实登记；
4. match_sketch 弦替代崩溃修复（失败归类 correction）；SSB 生成器模板与盘上 YAML 同步；
5. SSOT 机械化：integrated_note 数字从 results 机械生成、notes 行从 registry 派生校验、env 覆盖列从 registry 聚合生成；
6. environment_digest 纳入 solvers 代码+外部求解器版本（ccx/soffice/matlab）；
7. 效度工程：hidden-public 分差监控、MBPP+ 类排序结论补显著性检验、scoring §6 第三组误差或降级声明；
8. cfdquery/mechvqa prompt_sha256 回填（新评测周期）；.foam_tail 残留清理。

## 8. 审计过程记录

- 波次 1（10 agent）：8 lane 中 7 条因 schema 校验静默失败（已改容错文本协议）；
- 波次 2（15 agent）：4 lane 成功 + 6 major 对抗复核；
- 波次 3（3 agent）：补齐余下 3 lane；
- 全程只读（1 名审计员在 /tmp 曾写 git-show 临时副本并即删，已在报告披露）；
- 本报告 §6 整改为 orchestrator 审后执行，均有回归验证。
