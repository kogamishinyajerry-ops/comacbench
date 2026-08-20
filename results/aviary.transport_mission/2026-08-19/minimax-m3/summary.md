# simulation_agent 结果汇总（provider=minimax, model=MiniMax-M3, seed=0）

## ValidityGate 分布（先看 gate，再看子分）

- 任务总数: 8
- gate 通过: 2
- gate 失败: 6（直接 0 分）
- 作废: 0
- gate 失败原因分布: {'code_not_executable': 5, 'missing_output': 1}

## physics（NMSE 阈值分）分布（n=8）

- 1.0: 2
- 0.5: 0
- 0.0: 6

## 每任务明细

| task | gate | nmse | nmse_score | score | 关键信息 |
| --- | --- | --- | --- | --- | --- |
| av_fuel_ratio | 0 | - | 0.0 | 0.0 | missing=exec_fail |
| av_grossmass_trade | 0 | - | 0.0 | 0.0 | missing=exec_fail |
| av_range_2500_m75 | 0 | - | 0.0 | 0.0 | missing=exec_fail |
| av_range_3000_m80 | 1 | - | 1.0 | 1.0 | missing=exec_fail |
| av_range_3200_m785 | 0 | - | 0.0 | 0.0 | missing=exec_fail |
| av_range_sweep | 0 | - | 0.0 | 0.0 | missing=exec_fail |
| av_repair_grossmass | 1 | - | 1.0 | 1.0 | missing=exec_fail |
| av_repair_range | 0 | - | 0.0 | 0.0 | missing=result.json |
