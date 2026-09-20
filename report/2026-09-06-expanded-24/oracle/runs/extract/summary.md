# qa_grounded 结果汇总（provider=oracle, model=n/a, seed=20260906）

## ValidityGate 分布（先看 gate，再看子分）

- 任务总数: 6
- gate 通过: 0
- gate 失败: 0（直接 0 分）
- 作废（不计分）: 6
- gate 失败原因分布: {'crash': 6}

## 客观层（requirements）

- 正确: 0/0（accuracy = 0.0000，分母=计分任务数）
- 子分适用性: physics=N/A（无证据/拒答层）；objective=N/A（并入 requirements）；robustness=采样一致性（本配置样本=1，不适用）
- 权重（任务 YAML 覆写）: score = gate × 1.0×requirements

## 每题明细

| task | gate | answer_correct | score |
| --- | --- | --- | --- |
| awx_ce_03 | 0 | 0 | 0.0 |
| awx_ce_04 | 0 | 0 | 0.0 |
| awx_ce_05 | 0 | 0 | 0.0 |
| awx_ce_06 | 0 | 0 | 0.0 |
| awx_ce_07 | 0 | 0 | 0.0 |
| awx_ce_08 | 0 | 0 | 0.0 |
