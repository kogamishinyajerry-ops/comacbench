# design_artifact 结果汇总（provider=openai_compat, model=MiniMax-M3, seed=20260905）

## ValidityGate 分布（先看 gate，再看子分）

- 任务总数: 2
- gate 通过: 0
- gate 失败: 2（直接 0 分）
- 作废: 0
- gate 失败原因分布: {'code_not_executable': 2}

## 均分: 0.0000（gate 均值 0/2）

## 每任务明细

| task | gate | 失败模式 | vol_rel | bbox_max_rel | iface | physics | req | score |
| --- | --- | --- | --- | --- | --- | --- | --- | --- |
| ssb_17_35 | 0 | code_not_executable | - | - | - | 0.0 | 0.0 | 0.0 |
| ssb_22_47 | 0 | code_not_executable | - | - | - | 0.0 | 0.0 | 0.0 |
