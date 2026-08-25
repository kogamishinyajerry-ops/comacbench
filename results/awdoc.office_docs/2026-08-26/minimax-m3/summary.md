# design_artifact 结果汇总（provider=minimax, model=MiniMax-M3, seed=0）

## ValidityGate 分布（先看 gate，再看子分）

- 任务总数: 18
- gate 通过: 12
- gate 失败: 6（直接 0 分）
- 作废: 0
- gate 失败原因分布: {'code_not_executable': 4, 'missing_output': 2}

## 均分: 0.6667（gate 均值 12/18）

## 每任务明细

| task | gate | 失败模式 | vol_rel | bbox_max_rel | iface | physics | req | score |
| --- | --- | --- | --- | --- | --- | --- | --- | --- |
| awd_brf_load_01 | 0 | code_not_executable | - | - | - | 0.0 | 0.0 | 0.0 |
| awd_brf_load_02 | 1 | - | - | - | - | 1.0 | 1.0 | 1.0 |
| awd_brf_load_03 | 0 | code_not_executable | - | - | - | 0.0 | 0.0 | 0.0 |
| awd_brf_perf_01 | 0 | missing_output | - | - | - | 0.0 | 0.0 | 0.0 |
| awd_brf_perf_02 | 1 | - | - | - | - | 1.0 | 1.0 | 1.0 |
| awd_brf_perf_03 | 0 | missing_output | - | - | - | 0.0 | 0.0 | 0.0 |
| awd_brf_perf_04 | 1 | - | - | - | - | 1.0 | 1.0 | 1.0 |
| awd_brf_perf_05 | 1 | - | - | - | - | 1.0 | 1.0 | 1.0 |
| awd_brf_perf_06 | 1 | - | - | - | - | 1.0 | 1.0 | 1.0 |
| awd_rep_load_01 | 0 | code_not_executable | - | - | - | 0.0 | 0.0 | 0.0 |
| awd_rep_load_02 | 0 | code_not_executable | - | - | - | 0.0 | 0.0 | 0.0 |
| awd_rep_load_03 | 1 | - | - | - | - | 1.0 | 1.0 | 1.0 |
| awd_rep_perf_01 | 1 | - | - | - | - | 1.0 | 1.0 | 1.0 |
| awd_rep_perf_02 | 1 | - | - | - | - | 1.0 | 1.0 | 1.0 |
| awd_rep_perf_03 | 1 | - | - | - | - | 1.0 | 1.0 | 1.0 |
| awd_rep_perf_04 | 1 | - | - | - | - | 1.0 | 1.0 | 1.0 |
| awd_rep_perf_05 | 1 | - | - | - | - | 1.0 | 1.0 | 1.0 |
| awd_rep_perf_06 | 1 | - | - | - | - | 1.0 | 1.0 | 1.0 |
