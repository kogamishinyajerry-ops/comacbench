# simulation_agent 结果汇总（provider=glm, model=glm-5.3, seed=0）

## ValidityGate 分布（先看 gate，再看子分）

- 任务总数: 10
- gate 通过: 1
- gate 失败: 9（直接 0 分）
- 作废: 0
- gate 失败原因分布: {'code_not_executable': 9}

## 迭代协议（rounds_to_success，不进 score）

- 收敛任务: 1/10；轮次分布: {2: 1, 3: 9}
- 收敛任务平均轮数: 2.00（rounds_to_success；单轮协议下该值恒为 1）

## physics（NMSE 阈值分）分布（n=10）

- 1.0: 0
- 0.5: 0
- 0.0: 10

## 每任务明细

| task | gate | nmse | nmse_score | score | 关键信息 |
| --- | --- | --- | --- | --- | --- |
| foam_bernardcells_1 | 0 | - | 0.0 | 0.0 |  |
| foam_bernardcells_10 | 1 | 420111928.795389 | 0.0 | 0.4 | last=10 fields=['U', 'p', 'T'] |
| foam_bernardcells_2 | 0 | - | 0.0 | 0.0 |  |
| foam_bernardcells_3 | 0 | - | 0.0 | 0.0 |  |
| foam_bernardcells_4 | 0 | - | 0.0 | 0.0 |  |
| foam_bernardcells_5 | 0 | - | 0.0 | 0.0 |  |
| foam_bernardcells_6 | 0 | - | 0.0 | 0.0 |  |
| foam_bernardcells_7 | 0 | - | 0.0 | 0.0 |  |
| foam_bernardcells_8 | 0 | - | 0.0 | 0.0 |  |
| foam_bernardcells_9 | 0 | - | 0.0 | 0.0 |  |
