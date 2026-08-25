# design_artifact 结果汇总（provider=glm, model=glm-5.3, seed=0）

## ValidityGate 分布（先看 gate，再看子分）

- 任务总数: 25
- gate 通过: 9
- gate 失败: 16（直接 0 分）
- 作废: 0
- gate 失败原因分布: {'code_not_executable': 15, 'sandbox_escape_attempt': 1}

## 均分: 0.2869（gate 均值 9/25）

## 每任务明细

| task | gate | 失败模式 | vol_rel | bbox_max_rel | iface | physics | req | score |
| --- | --- | --- | --- | --- | --- | --- | --- | --- |
| ssb_13_1 | 0 | code_not_executable | - | - | - | 0.0 | 0.0 | 0.0 |
| ssb_17_35 | 1 | - | - | - | - | 0.1952 | 1.0 | 0.5976 |
| ssb_22_47 | 1 | - | - | - | - | 0.1481 | 1.0 | 0.57405 |
| ssb_23_24 | 0 | code_not_executable | - | - | - | 0.0 | 0.0 | 0.0 |
| ssb_24_23 | 0 | code_not_executable | - | - | - | 0.0 | 0.0 | 0.0 |
| ssb_262_17 | 1 | - | - | - | - | 1.0 | 1.0 | 1.0 |
| ssb_263_1 | 0 | sandbox_escape_attempt | - | - | - | 0.0 | 0.0 | 0.0 |
| ssb_267_18 | 1 | - | - | - | - | 0.0 | 1.0 | 0.5 |
| ssb_267_21 | 0 | code_not_executable | - | - | - | 0.0 | 0.0 | 0.0 |
| ssb_269_43 | 1 | - | - | - | - | 1.0 | 1.0 | 1.0 |
| ssb_269_44 | 1 | - | - | - | - | 0.0 | 1.0 | 0.5 |
| ssb_279_23 | 0 | code_not_executable | - | - | - | 0.0 | 0.0 | 0.0 |
| ssb_280_17 | 0 | code_not_executable | - | - | - | 0.0 | 0.0 | 0.0 |
| ssb_28_7 | 0 | code_not_executable | - | - | - | 0.0 | 0.0 | 0.0 |
| ssb_290_1 | 0 | code_not_executable | - | - | - | 0.0 | 0.0 | 0.0 |
| ssb_290_27 | 1 | - | - | - | - | 1.0 | 1.0 | 1.0 |
| ssb_297_42 | 0 | code_not_executable | - | - | - | 0.0 | 0.0 | 0.0 |
| ssb_304_35 | 1 | - | - | - | - | 1.0 | 1.0 | 1.0 |
| ssb_341_40 | 0 | code_not_executable | - | - | - | 0.0 | 0.0 | 0.0 |
| ssb_384_4 | 0 | code_not_executable | - | - | - | 0.0 | 0.0 | 0.0 |
| ssb_408_5 | 0 | code_not_executable | - | - | - | 0.0 | 0.0 | 0.0 |
| ssb_433_47 | 0 | code_not_executable | - | - | - | 0.0 | 0.0 | 0.0 |
| ssb_455_35 | 0 | code_not_executable | - | - | - | 0.0 | 0.0 | 0.0 |
| ssb_469_9 | 1 | - | - | - | - | 1.0 | 1.0 | 1.0 |
| ssb_60_7 | 0 | code_not_executable | - | - | - | 0.0 | 0.0 | 0.0 |
