# design_artifact 结果汇总（provider=minimax, model=MiniMax-M3, seed=0）

## ValidityGate 分布（先看 gate，再看子分）

- 任务总数: 25
- gate 通过: 7
- gate 失败: 18（直接 0 分）
- 作废: 0
- gate 失败原因分布: {'code_not_executable': 17, 'missing_output': 1}

## 均分: 0.1600（gate 均值 7/25）

## 每任务明细

| task | gate | 失败模式 | vol_rel | bbox_max_rel | iface | physics | req | score |
| --- | --- | --- | --- | --- | --- | --- | --- | --- |
| ssb_13_1 | 0 | code_not_executable | - | - | - | 0.0 | 0.0 | 0.0 |
| ssb_17_35 | 0 | code_not_executable | - | - | - | 0.0 | 0.0 | 0.0 |
| ssb_22_47 | 0 | code_not_executable | - | - | - | 0.0 | 0.0 | 0.0 |
| ssb_23_24 | 1 | - | - | - | - | 1.0 | 1.0 | 1.0 |
| ssb_24_23 | 0 | code_not_executable | - | - | - | 0.0 | 0.0 | 0.0 |
| ssb_262_17 | 1 | - | - | - | - | 0.0 | 1.0 | 0.5 |
| ssb_263_1 | 0 | code_not_executable | - | - | - | 0.0 | 0.0 | 0.0 |
| ssb_267_18 | 0 | code_not_executable | - | - | - | 0.0 | 0.0 | 0.0 |
| ssb_267_21 | 0 | code_not_executable | - | - | - | 0.0 | 0.0 | 0.0 |
| ssb_269_43 | 1 | - | - | - | - | 0.0 | 1.0 | 0.5 |
| ssb_269_44 | 1 | - | - | - | - | 0.0 | 1.0 | 0.5 |
| ssb_279_23 | 1 | - | - | - | - | 0.0 | 1.0 | 0.5 |
| ssb_280_17 | 0 | code_not_executable | - | - | - | 0.0 | 0.0 | 0.0 |
| ssb_28_7 | 0 | code_not_executable | - | - | - | 0.0 | 0.0 | 0.0 |
| ssb_290_1 | 0 | code_not_executable | - | - | - | 0.0 | 0.0 | 0.0 |
| ssb_290_27 | 1 | - | - | - | - | 0.0 | 1.0 | 0.5 |
| ssb_297_42 | 0 | missing_output | - | - | - | 0.0 | 0.0 | 0.0 |
| ssb_304_35 | 0 | code_not_executable | - | - | - | 0.0 | 0.0 | 0.0 |
| ssb_341_40 | 1 | - | - | - | - | 0.0 | 1.0 | 0.5 |
| ssb_384_4 | 0 | code_not_executable | - | - | - | 0.0 | 0.0 | 0.0 |
| ssb_408_5 | 0 | code_not_executable | - | - | - | 0.0 | 0.0 | 0.0 |
| ssb_433_47 | 0 | code_not_executable | - | - | - | 0.0 | 0.0 | 0.0 |
| ssb_455_35 | 0 | code_not_executable | - | - | - | 0.0 | 0.0 | 0.0 |
| ssb_469_9 | 0 | code_not_executable | - | - | - | 0.0 | 0.0 | 0.0 |
| ssb_60_7 | 0 | code_not_executable | - | - | - | 0.0 | 0.0 | 0.0 |
