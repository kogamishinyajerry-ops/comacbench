# code_exec 结果汇总（provider=oracle, model=n/a, seed=0）

## ValidityGate 分布（先看 gate，再看子分）

- 任务总数: 1
- gate 通过: 1
- gate 失败: 0（直接 0 分）
- 作废: 0
- gate 失败原因分布: 无

## pass@1（全部隐藏测试通过）

- 0/1 = 0.0000（physics=1.0 的任务占比；physics 均值含部分通过分，二者并读）

## physics（隐藏测试/数值） 分布（n=1）

- =1.0: 0
- 0.5-1.0: 1
- 0-0.5: 0
- =0.0: 0

## robustness（确定性） 分布（n=1）

- =1.0: 1
- 0.5-1.0: 0
- 0-0.5: 0
- =0.0: 0

## 每任务明细

| task | gate | physics | robust | score | 关键信息 |
| --- | --- | --- | --- | --- | --- |
| ontology_trace_01 | 1 | 0.7143 | 1.0 | 0.80001 | cases 5/7 |
