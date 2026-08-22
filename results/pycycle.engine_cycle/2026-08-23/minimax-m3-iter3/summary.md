# simulation_agent 结果汇总（provider=minimax, model=MiniMax-M3, seed=0）

## ValidityGate 分布（先看 gate，再看子分）

- 任务总数: 10
- gate 通过: 0
- gate 失败: 10（直接 0 分）
- 作废: 0
- gate 失败原因分布: {'code_not_executable': 10}

## 迭代协议（rounds_to_success，不进 score）

- 收敛任务: 0/10；轮次分布: {3: 10}

## physics（NMSE 阈值分）分布（n=10）

- 1.0: 0
- 0.5: 0
- 0.0: 10

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
