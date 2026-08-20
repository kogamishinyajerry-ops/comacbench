# 评分体系规范（v0.1）

## 1. 报告维度：不用一个总分掩盖能力缺口

每次评测报告至少输出九个维度分，外加一个仅作导航的总分（明确标注"总分不用于决策"）：

| # | 维度 | 主要数据来源 |
| --- | --- | --- |
| 1 | 航空知识与文档理解 knowledge | cfdquery、aeroengqa、mechvqa、camb |
| 2 | 科学编程 coding | scicode、cfdcode |
| 3 | CAD/几何 cad_geometry | cadgen；openvsp 已 paused-env |
| 4 | CFD cfd | nasa_tmr、crm_dpw_hlpw（Fluent/StarCCM）、superwing；foambench 已 paused-env |
| 5 | 结构 structures | simjeb、engdesign 结构子集 |
| 6 | 动力 propulsion | pycycle |
| 7 | 飞控 flight_control | gtm/jsbsim |
| 8 | 总体设计与 MDO mdo_design | aviary、engdesign、crm 优化层 |
| 9 | 鲁棒性与审计性 robustness_audit | 全部基准的 robustness 子分 + 审计日志质量 |

规则：一个模型 CFD 强而系统设计弱的事实必须能在报告里直接读出来；任何"平均后单分数"仅允许出现在报告首页导航区。

## 2. 任务级计分公式

```
Score = ValidityGate × (0.35·S_physics + 0.30·S_requirements + 0.20·S_objective + 0.15·S_robustness)
```

- 权重可被任务 YAML 覆写，但四个子分必须全部报告（缺项按 0 计并标注）；
- `ValidityGate ∈ {0, 1}`，硬门槛，见下节；
- 基准级分数 = 任务分数的**加权聚合**（默认按任务等权，hidden 题单独成组）；
- 报告必须给出每基准的 gate 失败率（多少任务直接 0 分）与原因分布——这往往比均分更有信息量。

## 3. ValidityGate：工程有效性硬门槛

出现以下**任一**情况，`ValidityGate = 0`：

- 代码无法执行（含 sandbox 违规）；
- CAD 无法解析 / B-Rep 非法；
- 网格非法 / 边界条件不完备 / 单位错误；
- 仿真发散或未达任务声明的收敛标准；
- 结果违反基本守恒或场变量物理范围；
- 漏掉任务声明的硬性设计约束；
- 缺少 output_contract 声明的产物。

设计意图：**不能让"解释写得很好"补偿一个完全不可用的工程结果。** gate 失败原因必须写入 result.json 的 `gate_failures`，用于聚合分析。

## 4. LLM Judge 的边界（强制）

LLM judge 允许评估（单独报告，不进 `score`）：

- 解释是否完整、风险说明是否充分；
- 审计记录是否清晰；
- 是否正确区分事实与推断。

LLM judge **禁止**替代：

- 仿真复算；
- 几何/网格检查；
- 单元测试；
- 数值容差判定；
- 守恒性检查;
- 约束求解验证。

MechVQA 类含 judge 的外部基准接入时：客观题必须先规则判分，judge 分数单列 `judge_explain` 字段。

## 5. 公共可比层 vs 受控隐藏层

| 层 | 用途 | 数据来源 | 泄漏风险处理 |
| --- | --- | --- | --- |
| public_comparable | 与论文/其他模型横向对比 | 公开 benchmark 原题 | 明知可能已入训练语料；结论只用于"可比性"，不用于版本选型 |
| hidden_dynamic | 版本选型、防记忆 | 开源工具动态生成（Aviary/OpenVSP/pyCycle/SuperWing 几何族/CRM 工况故障注入/SimJEB 载荷组合） | 采样种子与参考答案不明文入库；题目参数每次评测轮换；泄漏率定期用"公开题 vs 隐藏题分差"监控 |

hidden 任务的生成器要求：

1. 参数空间与采样策略版本化（生成器本身进 git）；
2. 参考答案由工具预计算生成并加密/隔离存储；
3. 每轮评测后统计 hidden-public 分差；分差持续收窄视为泄漏信号，触发题库轮换。

## 6. field_prediction 划分纪律（防泄漏泛化虚高）

- 任何 train/test 划分必须**按几何构型分组**；
- 禁止同一构型不同迎角/Mach 跨集分布；
- 报告必须分别给出：内插 / 几何外推 / 工况外推 三组误差；
- SuperWing-Coeff-Lite 首批以 CRMpert 为保留测试集（SuperWing 训练），沿用 AeroTransformer 的迁移设定。

## 7. 数据与环境冻结

- 每个基准接入时登记：`assets_revision`（数据版本）+ `environment_digest`（镜像/依赖摘要）；
- 任何一项变更 = 新评测周期，旧分与新分不得直接混排（报告标注版本断点）；
- 随机种子：判分侧全固定；Agent 侧如需采样，任务声明次数并报告方差。

## 8. 基线与发布

- 每个基准 integrated 时必须同时产出至少一个基线模型的完整报告（含 gate 失败率分布）；
- 基线报告进入 `benchmarks/results/<registry_id>/<date>/`，作为后续回归对照；
- 评测代码与判分器随报告一并归档（判分器变更需 diff 说明）。
