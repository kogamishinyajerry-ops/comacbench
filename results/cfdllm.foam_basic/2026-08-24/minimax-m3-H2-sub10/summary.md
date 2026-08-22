# simulation_agent 结果汇总（provider=minimax, model=MiniMax-M3, seed=0）

## ValidityGate 分布（先看 gate，再看子分）

- 任务总数: 10
- gate 通过: 9
- gate 失败: 1（直接 0 分）
- 作废: 0
- gate 失败原因分布: {'simulation_failed': 1}

## physics（NMSE 阈值分）分布（n=10）

- 1.0: 0
- 0.5: 0
- 0.0: 10

## 每任务明细

| task | gate | nmse | nmse_score | score | 关键信息 |
| --- | --- | --- | --- | --- | --- |
| foam_bernardcells_1 | 1 | 417052168.272549 | 0.0 | 0.4 | last=50 fields=['U', 'p', 'T'] |
| foam_bernardcells_10 | 1 | 108528620.671675 | 0.0 | 0.4 | last=1000 fields=['U', 'p', 'T'] |
| foam_bernardcells_2 | 1 | 104623369.061754 | 0.0 | 0.4 | last=5 fields=['U', 'p', 'T'] |
| foam_bernardcells_3 | 1 | 420147260.150105 | 0.0 | 0.4 | last=50 fields=['U', 'p', 'T'] |
| foam_bernardcells_4 | 1 | 107218539.746093 | 0.0 | 0.4 | last=1000 fields=['U', 'p', 'T'] |
| foam_bernardcells_5 | 1 | 417638864.376261 | 0.0 | 0.4 | last=1000 fields=['U', 'p', 'T'] |
| foam_bernardcells_6 | 1 | 415779737.229342 | 0.0 | 0.4 | last=1000 fields=['U', 'p', 'T'] |
| foam_bernardcells_7 | 1 | 417478772.652776 | 0.0 | 0.4 | last=10 fields=['U', 'p', 'T'] |
| foam_bernardcells_8 | 1 | 417983008.376732 | 0.0 | 0.4 | last=50 fields=['U', 'p', 'T'] |
| foam_bernardcells_9 | 0 | - | 0.0 | 0.0 | missing=exec_fail |
