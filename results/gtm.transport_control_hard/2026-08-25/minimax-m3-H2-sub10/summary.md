# simulation_agent 结果汇总（provider=minimax, model=MiniMax-M3, seed=0）

## ValidityGate 分布（先看 gate，再看子分）

- 任务总数: 10
- gate 通过: 8
- gate 失败: 2（直接 0 分）
- 作废: 0
- gate 失败原因分布: {'code_not_executable': 2}

## physics（NMSE 阈值分）分布（n=10）

- 1.0: 8
- 0.5: 0
- 0.0: 2

## 每任务明细

| task | gate | nmse | nmse_score | score | 关键信息 |
| --- | --- | --- | --- | --- | --- |
| gtmh_gs_01 | 1 | - | 1.0 | 1.0 | missing=exec_fail |
| gtmh_gs_02 | 1 | - | 1.0 | 1.0 | missing=exec_fail |
| gtmh_gs_03 | 1 | - | 1.0 | 1.0 | missing=exec_fail |
| gtmh_id_01 | 1 | - | 1.0 | 1.0 | missing=exec_fail |
| gtmh_id_02 | 0 | - | 0.0 | 0.0 | missing=exec_fail |
| gtmh_id_03 | 1 | - | 1.0 | 1.0 | missing=exec_fail |
| gtmh_id_04 | 0 | - | 0.0 | 0.0 | missing=exec_fail |
| gtmh_margin_01 | 1 | - | 1.0 | 1.0 | missing=exec_fail |
| gtmh_margin_02 | 1 | - | 1.0 | 1.0 | missing=exec_fail |
| gtmh_margin_03 | 1 | - | 1.0 | 1.0 | missing=exec_fail |
