# simulation_agent 结果汇总（provider=minimax, model=MiniMax-M3, seed=0）

## ValidityGate 分布（先看 gate，再看子分）

- 任务总数: 28
- gate 通过: 2
- gate 失败: 26（直接 0 分）
- 作废: 0
- gate 失败原因分布: {'code_not_executable': 25, 'missing_output': 1}

## physics（NMSE 阈值分）分布（n=28）

- 1.0: 0
- 0.5: 1
- 0.0: 27

## 每任务明细

| task | gate | nmse | nmse_score | score | 关键信息 |
| --- | --- | --- | --- | --- | --- |
| pc_design_fn10k_t2300_opr12 | 0 | - | 0.0 | 0.0 | missing=exec_fail |
| pc_design_fn10p5k_t2750_opr145 | 0 | - | 0.0 | 0.0 | missing=exec_fail |
| pc_design_fn11k_t2550_opr11 | 0 | - | 0.0 | 0.0 | missing=exec_fail |
| pc_design_fn12k_t2450 | 0 | - | 0.0 | 0.0 | missing=exec_fail |
| pc_design_fn13k_t2650_opr13 | 0 | - | 0.0 | 0.0 |  |
| pc_design_fn13p5k_t2400_opr115 | 0 | - | 0.0 | 0.0 | missing=exec_fail |
| pc_design_fn14k_t2900_opr16 | 0 | - | 0.0 | 0.0 | missing=exec_fail |
| pc_design_fn14p5k_t2850_opr125 | 0 | - | 0.0 | 0.0 | missing=exec_fail |
| pc_design_fn15k_t2800 | 0 | - | 0.0 | 0.0 | missing=exec_fail |
| pc_design_fn15p5k_t2500_opr135 | 0 | - | 0.0 | 0.0 | missing=exec_fail |
| pc_design_fn16k_t2350_opr155 | 0 | - | 0.0 | 0.0 | missing=exec_fail |
| pc_fn_sweep | 0 | - | 0.0 | 0.0 | missing=exec_fail |
| pc_fuel_ratio | 0 | - | 0.0 | 0.0 | missing=exec_fail |
| pc_fuel_ratio_hi | 0 | - | 0.0 | 0.0 | missing=exec_fail |
| pc_fuel_ratio_lo | 0 | - | 0.0 | 0.0 | missing=exec_fail |
| pc_fuel_ratio_t2700_over_t2300 | 0 | - | 0.0 | 0.0 | missing=exec_fail |
| pc_od_throttle_t2200 | 0 | - | 0.0 | 0.0 | missing=exec_fail |
| pc_od_throttle_t2300 | 0 | - | 0.0 | 0.0 | missing=exec_fail |
| pc_od_throttle_t2500 | 0 | - | 0.0 | 0.0 |  |
| pc_od_throttle_t2700 | 0 | - | 0.0 | 0.0 | missing=exec_fail |
| pc_opr_sweep | 1 | - | 0.0 | 0.4 | missing=exec_fail |
| pc_opr_sweep_hi | 0 | - | 0.0 | 0.0 | missing=exec_fail |
| pc_repair_fn | 1 | - | 0.5 | 0.7 | missing=exec_fail |
| pc_repair_fn_v2 | 0 | - | 0.0 | 0.0 | missing=exec_fail |
| pc_repair_opr | 0 | - | 0.0 | 0.0 | missing=exec_fail |
| pc_repair_t4 | 0 | - | 0.0 | 0.0 | missing=exec_fail |
| pc_repair_t4_v2 | 0 | - | 0.0 | 0.0 | missing=result.json |
| pc_t4_sweep | 0 | - | 0.0 | 0.0 |  |
