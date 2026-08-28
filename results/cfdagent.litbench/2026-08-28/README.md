# cfdagent.litbench 2026-08-28 首批基线（60 任务）

> 基准来源与防幻觉纪律见 `registry/registry.yaml` 条目 + `data/cfdagent/litbench/PROVENANCE.md`。
> 每题 evidence 为 arXiv 摘要逐字子串（生成器强校验）；判分 qa_grounded MCQ（requirements=1.0）。

## 结果矩阵

| provider | 任务数 | gate | accuracy | 备注 |
| --- | --- | --- | --- | --- |
| oracle | 60 | 60/60 | **1.0000** | 判分管线自检（必须满分）✅ |
| stub | 60 | 60/60 | 0.2500 | 精确随机线（15/60），冒烟基线 ✅ |
| minimax | 60 | 60/60 | **0.8667** | MiniMax-M3 真实基线（52/60；失分 = 3 数值细节 + 3 组件/架构名 + 2 跨论文题，即细粒度文献事实而非通用知识） |
| glm | 60 | 60/60 | **0.7833** | glm-5.3 真实基线（47/60）；429 限流中断 2 次后 resume 幂等续跑完成 |

## 口径说明

- 子分适用性：physics=N/A、objective=N/A（并入 requirements）、robustness=N/A（样本=1），
  权重经任务 YAML 覆写塌缩到 requirements（adapter 契约机制，见 cfdquery 先例）。
- 题目为闭卷文献知识题（题面不含摘要原文）；证据引文仅用于审计链，不进入模型输入。
