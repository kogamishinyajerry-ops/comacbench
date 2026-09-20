# simulation_agent 结果汇总（provider=external, model=minimax-live-v2-recorded-replay, seed=0）

## ValidityGate 分布（先看 gate，再看子分）

- 任务总数: 1
- gate 通过: 0
- gate 失败: 1（直接 0 分）
- 作废: 0
- gate 失败原因分布: {'engineering_contract_failed': 1}

## physics（NMSE 阈值分）分布（n=1）

- 1.0: 0
- 0.5: 0
- 0.0: 1

## 每任务明细

| task | gate | nmse | nmse_score | score | 关键信息 |
| --- | --- | --- | --- | --- | --- |
| beam_static_01 | 0 | - | 0.0 | 0.0 | missing=exec_fail |
