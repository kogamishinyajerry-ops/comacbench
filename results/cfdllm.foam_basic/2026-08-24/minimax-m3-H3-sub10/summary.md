# simulation_agent 结果汇总（provider=minimax, model=MiniMax-M3, seed=0）

## ValidityGate 分布（先看 gate，再看子分）

- 任务总数: 10
- gate 通过: 10
- gate 失败: 0（直接 0 分）
- 作废: 0
- gate 失败原因分布: 无

## 迭代协议（rounds_to_success，不进 score）

- 收敛任务: 10/10；轮次分布: {1: 8, 2: 1, 3: 1}
- 收敛任务平均轮数: 1.30（rounds_to_success；单轮协议下该值恒为 1）

## physics（NMSE 阈值分）分布（n=10）

- 1.0: 0
- 0.5: 0
- 0.0: 10

## 每任务明细

| task | gate | nmse | nmse_score | score | 关键信息 |
| --- | --- | --- | --- | --- | --- |
| foam_bernardcells_1 | 1 | 417052168.266623 | 0.0 | 0.4 | last=1000 fields=['U', 'p', 'T'] |
| foam_bernardcells_10 | 1 | 105257974.250482 | 0.0 | 0.4 | last=50 fields=['U', 'p', 'T'] |
| foam_bernardcells_2 | 1 | 104717631.859389 | 0.0 | 0.4 | last=50 fields=['U', 'p', 'T'] |
| foam_bernardcells_3 | 1 | 420147260.150572 | 0.0 | 0.4 | last=1000 fields=['U', 'p', 'T'] |
| foam_bernardcells_4 | 1 | 424092205.335086 | 0.0 | 0.4 | last=1000 fields=['U', 'p', 'T'] |
| foam_bernardcells_5 | 1 | 417638864.375614 | 0.0 | 0.4 | last=50 fields=['U', 'p', 'T'] |
| foam_bernardcells_6 | 1 | 103962374.811131 | 0.0 | 0.4 | last=50 fields=['U', 'p', 'T'] |
| foam_bernardcells_7 | 1 | 104515245.474502 | 0.0 | 0.4 | last=100 fields=['U', 'p', 'T'] |
| foam_bernardcells_8 | 1 | 417983008.374822 | 0.0 | 0.4 | last=1000 fields=['U', 'p', 'T'] |
| foam_bernardcells_9 | 1 | 106397515.52638 | 0.0 | 0.4 | last=1000 fields=['U', 'p', 'T'] |
