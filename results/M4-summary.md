# M4 总结报告（2026-08-19）

> 运行环境：dev 终端。本里程碑收口 v0.1：engdesign 许可清点 + superwing field_prediction
> 集成 + 首份九维度基线报告。

## 1. Registry 状态变化

| registry_id | 之前 | 之后 | 依据 |
| --- | --- | --- | --- |
| superwing.coeff_lite | proposed | **integrated** | 系数层镜像（CC BY-SA 4.0，SA 传染性声明）→ field_prediction adapter 跑通 → oracle 100/100 → stub + M3 基线 |
| engdesign.open | proposed（needs-per-task-audit） | proposed（**confirmed-split**，集成 blocked） | 逐任务许可清点完成（101 任务：专有软件 20+HDL 10+非目标域 63，收窄 28）；官方评测脚本未发布 → 判分不可本地复现，集成 blocked（待议） |

## 2. superwing.coeff_lite（field_prediction，五类 adapter 之五补齐）

- **五类 adapter 至此全部实现**：qa_grounded / code_exec / simulation_agent /
  design_artifact（未接线，batch-2）/ field_prediction；
- 系数层镜像 ~10MB（configs.dat + index.npy + train/test.parquet），**不触体数据**（3.49TB）；
- **划分纪律验证**：test 424 构型与 train 3815 构型零交集（按几何分组，满足 scoring §6）；
- 判分：gate（JSON 合法 + 系数物理包络）→ physics（相对误差带 cl/cm 5%、cd 10%）→
  划分纪律分组独立报告（几何外推/内插）；
- 基线（M3）：gate 100/100、physics 均值 0.080——**LLM 无法直接做气动系数回归**
  （能力边界，见九维度报告 §4）；ML 基线留待后续（torch 可选导入）。

## 3. engdesign.open（许可清点交付，集成 blocked）

- 题库 JSON（HF，`license: mit`）已镜像；逐任务审计 `data/engdesign/open/task_audit.csv`；
- 收窄子集 28 任务（机械 7/结构 7/控制 14，无专有软件 × 自包含）；
- **blocked 根因（如实）**：官方评测脚本 + 参考设计未随 HF/GitHub 发布（论文称 53 开源任务
  配 "manually authored evaluation scripts"），判分不可本地复现；自建 FEA/控制复算判分器属
  重大 scope 扩张且无法保证官方 473 评分项口径一致 → 不静默扩，进待议。

## 4. 九维度基线报告（v0.1 收官交付物）

`results/nine-dim-baseline-2026-08-19.md`：M3 基线下六维有数（knowledge 0.848 / coding
0.572 / cfd 0.22 部分 / mdo 0.250 + robustness 审计），三维 batch-2 补位；含 gate 失败率
分布与能力画像结论。**总分仅导航，不用于决策**。

## 5. v0.1 最终盘点（8 件套）

| # | registry_id | adapter | status |
| --- | --- | --- | --- |
| 1 | cfdllm.cfdquery | qa_grounded | ✅ integrated |
| 2 | aeroengqa.gold | qa_grounded | ✅ integrated |
| 3 | scicode.physics | code_exec | ✅ integrated |
| 4 | cfdllm.cfdcode | code_exec | ✅ integrated |
| 5 | engdesign.open | code_exec | 🟡 proposed（许可清点完成，集成 blocked） |
| 6 | cfdllm.foam_basic | simulation_agent | ✅ **integrated**（判分器 110/110 验证；M3 基线 0/110 为真实能力边界） |
| 7 | aviary.transport_mission | simulation_agent | ✅ integrated |
| 8 | superwing.coeff_lite | field_prediction | ✅ integrated |

**6/8 integrated**；engdesign 与 foam_basic 两项有明确解阻条件（见 M3/M4 待议）。

## 6. 在途与待议（跨里程碑汇总）

0. **【2026-08-19 已修正并重跑】**：`os.chmod` 曾误列沙箱黑名单致 foam_basic 首跑 33 例误判
   `sandbox_escape`；已移除 + 重跑 + 补跑 12 例 → 最终诚实分布 **87 code_not_executable +
   23 simulation_failed（0 sandbox_escape）**。foam_basic 已 integrated。
1. **foam_basic GLM 基线**（M3 已落盘）：共享端点 429 待配额恢复后单跑；
2. **GLM 共享端点 429**（M2 遗留）：scicode/cfdcode/foam/superwing 的 GLM 基线待配额恢复单跑；
3. **engdesign 集成解阻**：官方发布 eval 脚本，或验收人裁定自建判分口径；
4. **superwing CRMpert 迁移测试**：独立数据集需单独获取 + 许可核对；
5. **superwing ML 基线**（AeroTransformer 系，torch 可选）——否则 field_prediction 维度
   只有「LLM 不会」的零基线，缺正例；
6. **git 未初始化**：manifest 的 git_commit=unknown，建议 git init 后首提交固化布局。

## 7. 产出文件

```
benchmarks/
├── runners/field_prediction.py + gen_tasks_superwing.py
│          （五类 adapter 齐备：qa_grounded/code_exec/simulation_agent/field_prediction/design_artifact 待 batch-2）
├── tasks/superwing.coeff_lite/    100 yaml + 100 md
├── data/superwing/coeff_lite/     系数层镜像 + PROVENANCE + sha256.txt
├── data/engdesign/open/           题库 + task_audit.csv + subset_ids.json + PROVENANCE
├── results/superwing.coeff_lite/2026-08-19/{README.md, oracle/, stub/, minimax-m3/}
├── results/nine-dim-baseline-2026-08-19.md（九维度报告）
├── results/M4-summary.md（本文件）
└── registry/{registry.yaml, license-notes.md}
```
