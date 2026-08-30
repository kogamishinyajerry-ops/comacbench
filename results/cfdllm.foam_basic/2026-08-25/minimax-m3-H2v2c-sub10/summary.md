# simulation_agent 结果汇总（provider=minimax, model=MiniMax-M3, seed=0）

## ValidityGate 分布（先看 gate，再看子分）

- 任务总数: 10
- gate 通过: 6
- gate 失败: 4（直接 0 分）
- 作废: 0
- gate 失败原因分布: {'code_not_executable': 3, 'simulation_failed': 1}

## physics（NMSE 阈值分）分布（n=10）

- 1.0: 0
- 0.5: 0
- 0.0: 10

## 每任务明细

| task | gate | nmse | nmse_score | score | 关键信息 |
| --- | --- | --- | --- | --- | --- |
| foam_bernardcells_1 | 1 | 9999.0 | 0.0 | 0.4 | last=1000 fields=[] |
| foam_bernardcells_10 | 1 | 9999.0 | 0.0 | 0.4 | last=1000 fields=[] |
| foam_bernardcells_2 | 1 | 9999.0 | 0.0 | 0.4 | last=1000 fields=[] |
| foam_bernardcells_3 | 0 | - | 0.0 | 0.0 |  |
| foam_bernardcells_4 | 1 | 9999.0 | 0.0 | 0.4 | last=1000 fields=[] |
| foam_bernardcells_5 | 0 | - | 0.0 | 0.0 |  |
| foam_bernardcells_6 | 1 | 9999.0 | 0.0 | 0.4 | last=1000 fields=[] |
| foam_bernardcells_7 | 0 | - | 0.0 | 0.0 | missing=exec_fail |
| foam_bernardcells_8 | 1 | 9999.0 | 0.0 | 0.4 | last=1000 fields=[] |
| foam_bernardcells_9 | 0 | - | 0.0 | 0.0 |  |
