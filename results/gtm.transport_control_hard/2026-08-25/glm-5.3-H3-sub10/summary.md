# simulation_agent 结果汇总（provider=glm, model=glm-5.3, seed=0）

## ValidityGate 分布（先看 gate，再看子分）

- 任务总数: 10
- gate 通过: 6
- gate 失败: 4（直接 0 分）
- 作废: 0
- gate 失败原因分布: {'code_not_executable': 4}

## 迭代协议（rounds_to_success，不进 score）

- 收敛任务: 6/10；轮次分布: {1: 6, 3: 4}
- 收敛任务平均轮数: 1.00（rounds_to_success；单轮协议下该值恒为 1）

## physics（NMSE 阈值分）分布（n=10）

- 1.0: 6
- 0.5: 0
- 0.0: 4

## 每任务明细

| task | gate | nmse | nmse_score | score | 关键信息 |
| --- | --- | --- | --- | --- | --- |
| gtmh_gs_01 | 1 | - | 1.0 | 1.0 | missing=exec_fail |
| gtmh_gs_02 | 1 | - | 1.0 | 1.0 | missing=exec_fail |
| gtmh_gs_03 | 1 | - | 1.0 | 1.0 | missing=exec_fail |
| gtmh_id_01 | 0 | - | 0.0 | 0.0 | missing=exec_fail |
| gtmh_id_02 | 0 | - | 0.0 | 0.0 | missing=exec_fail |
| gtmh_id_03 | 0 | - | 0.0 | 0.0 | missing=exec_fail |
| gtmh_id_04 | 0 | - | 0.0 | 0.0 | missing=exec_fail |
| gtmh_margin_01 | 1 | - | 1.0 | 1.0 | missing=exec_fail |
| gtmh_margin_02 | 1 | - | 1.0 | 1.0 | missing=exec_fail |
| gtmh_margin_03 | 1 | - | 1.0 | 1.0 | missing=exec_fail |
