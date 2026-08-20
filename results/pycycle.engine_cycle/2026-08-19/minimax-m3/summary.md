# simulation_agent 结果汇总（provider=minimax, model=MiniMax-M3, seed=0）

## ValidityGate 分布（先看 gate，再看子分）

- 任务总数: 7
- gate 通过: 0
- gate 失败: 7（直接 0 分）
- 作废: 0
- gate 失败原因分布: {'code_not_executable': 7}

## physics（NMSE 阈值分）分布（n=7）

- 1.0: 0
- 0.5: 0
- 0.0: 7

## 每任务明细

| task | gate | nmse | nmse_score | score | 关键信息 |
| --- | --- | --- | --- | --- | --- |
| pc_design_fn12k_t2450 | 0 | - | 0.0 | 0.0 | missing=exec_fail |
| pc_design_fn15k_t2800 | 0 | - | 0.0 | 0.0 | missing=exec_fail |
| pc_fuel_ratio | 0 | - | 0.0 | 0.0 | missing=exec_fail |
| pc_od_throttle_t2200 | 0 | - | 0.0 | 0.0 | missing=exec_fail |
| pc_opr_sweep | 0 | - | 0.0 | 0.0 |  |
| pc_repair_fn | 0 | - | 0.0 | 0.0 | missing=exec_fail |
| pc_repair_t4 | 0 | - | 0.0 | 0.0 | missing=exec_fail |
