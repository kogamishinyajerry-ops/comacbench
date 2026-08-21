# simulation_agent 结果汇总（provider=minimax, model=MiniMax-M3, seed=0）

## ValidityGate 分布（先看 gate，再看子分）

- 任务总数: 27
- gate 通过: 6
- gate 失败: 21（直接 0 分）
- 作废: 0
- gate 失败原因分布: {'code_not_executable': 20, 'sandbox_escape_attempt': 1}

## physics（NMSE 阈值分）分布（n=27）

- 1.0: 6
- 0.5: 0
- 0.0: 21

## 每任务明细

| task | gate | nmse | nmse_score | score | 关键信息 |
| --- | --- | --- | --- | --- | --- |
| av_fuel_ratio | 0 | - | 0.0 | 0.0 | missing=exec_fail |
| av_fuel_ratio_3300_over_2700 | 0 | - | 0.0 | 0.0 | missing=exec_fail |
| av_fuel_ratio_3500_over_2500 | 0 | - | 0.0 | 0.0 | missing=exec_fail |
| av_grossmass_sweep | 0 | - | 0.0 | 0.0 | missing=exec_fail |
| av_grossmass_trade | 0 | - | 0.0 | 0.0 | missing=exec_fail |
| av_grossmass_trade2 | 0 | - | 0.0 | 0.0 | missing=exec_fail |
| av_grossmass_trade3 | 0 | - | 0.0 | 0.0 | missing=exec_fail |
| av_range_2400_m72 | 1 | - | 1.0 | 1.0 | missing=exec_fail |
| av_range_2500_m75 | 0 | - | 0.0 | 0.0 | missing=exec_fail |
| av_range_2600_m75 | 1 | - | 1.0 | 1.0 | missing=exec_fail |
| av_range_2600_m82 | 0 | - | 0.0 | 0.0 | missing=exec_fail |
| av_range_2800_m75 | 1 | - | 1.0 | 1.0 | missing=exec_fail |
| av_range_2800_m78 | 1 | - | 1.0 | 1.0 | missing=exec_fail |
| av_range_3000_m80 | 0 | - | 0.0 | 0.0 | missing=exec_fail |
| av_range_3000_m82 | 0 | - | 0.0 | 0.0 | missing=exec_fail |
| av_range_3200_m785 | 0 | - | 0.0 | 0.0 | missing=exec_fail |
| av_range_3400_m72 | 1 | - | 1.0 | 1.0 | missing=exec_fail |
| av_range_3400_m80 | 0 | - | 0.0 | 0.0 | missing=exec_fail |
| av_range_3600_m78 | 1 | - | 1.0 | 1.0 | missing=exec_fail |
| av_range_3600_m82 | 0 | - | 0.0 | 0.0 | missing=exec_fail |
| av_range_sweep | 0 | - | 0.0 | 0.0 | missing=exec_fail |
| av_range_sweep_fine | 0 | - | 0.0 | 0.0 | missing=exec_fail |
| av_range_sweep_m78 | 0 | - | 0.0 | 0.0 | missing=exec_fail |
| av_repair_grossmass | 0 | - | 0.0 | 0.0 | missing=exec_fail |
| av_repair_grossmass_v2 | 0 | - | 0.0 | 0.0 | missing=exec_fail |
| av_repair_range | 0 | - | 0.0 | 0.0 | missing=exec_fail |
| av_repair_range_v2 | 0 | - | 0.0 | 0.0 |  |
