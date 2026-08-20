# simulation_agent 结果汇总（provider=glm, model=glm-4.6, seed=0）

## ValidityGate 分布（先看 gate，再看子分）

- 任务总数: 8
- gate 通过: 3
- gate 失败: 5（直接 0 分）
- 作废: 0
- gate 失败原因分布: {'code_not_executable': 4, 'sandbox_escape_attempt': 1}

## physics（NMSE 阈值分）分布（n=8）

- 1.0: 3
- 0.5: 0
- 0.0: 5

## 每任务明细

| task | gate | nmse | nmse_score | score | 关键信息 |
| --- | --- | --- | --- | --- | --- |
| av_fuel_ratio | 0 | - | 0.0 | 0.0 | missing=exec_fail |
| av_grossmass_trade | 0 | - | 0.0 | 0.0 | missing=exec_fail |
| av_range_2500_m75 | 1 | - | 1.0 | 1.0 | missing=exec_fail |
| av_range_3000_m80 | 1 | - | 1.0 | 1.0 | missing=exec_fail |
| av_range_3200_m785 | 1 | - | 1.0 | 1.0 | missing=exec_fail |
| av_range_sweep | 0 | - | 0.0 | 0.0 | missing=exec_fail |
| av_repair_grossmass | 0 | - | 0.0 | 0.0 | missing=exec_fail |
| av_repair_range | 0 | - | 0.0 | 0.0 |  |
