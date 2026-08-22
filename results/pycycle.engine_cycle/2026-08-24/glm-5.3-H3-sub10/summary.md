# simulation_agent 结果汇总（provider=glm, model=glm-5.3, seed=0）

## ValidityGate 分布（先看 gate，再看子分）

- 任务总数: 10
- gate 通过: 9
- gate 失败: 1（直接 0 分）
- 作废: 0
- gate 失败原因分布: {'code_not_executable': 1}

## 迭代协议（rounds_to_success，不进 score）

- 收敛任务: 9/10；轮次分布: {1: 4, 2: 4, 3: 2}
- 收敛任务平均轮数: 1.67（rounds_to_success；单轮协议下该值恒为 1）

## physics（NMSE 阈值分）分布（n=10）

- 1.0: 9
- 0.5: 0
- 0.0: 1

## 每任务明细

| task | gate | nmse | nmse_score | score | 关键信息 |
| --- | --- | --- | --- | --- | --- |
| pc_design_fn10k_t2300_opr12 | 1 | - | 1.0 | 1.0 | missing=exec_fail |
| pc_design_fn10p5k_t2750_opr145 | 1 | - | 1.0 | 1.0 | missing=exec_fail |
| pc_design_fn11k_t2550_opr11 | 1 | - | 1.0 | 1.0 | missing=exec_fail |
| pc_design_fn12k_t2450 | 1 | - | 1.0 | 1.0 | missing=exec_fail |
| pc_design_fn13k_t2650_opr13 | 1 | - | 1.0 | 1.0 | missing=exec_fail |
| pc_design_fn13p5k_t2400_opr115 | 1 | - | 1.0 | 1.0 | missing=exec_fail |
| pc_design_fn14k_t2900_opr16 | 1 | - | 1.0 | 1.0 | missing=exec_fail |
| pc_design_fn14p5k_t2850_opr125 | 0 | - | 0.0 | 0.0 |  |
| pc_design_fn15k_t2800 | 1 | - | 1.0 | 1.0 | missing=exec_fail |
| pc_design_fn15p5k_t2500_opr135 | 1 | - | 1.0 | 1.0 | missing=exec_fail |
