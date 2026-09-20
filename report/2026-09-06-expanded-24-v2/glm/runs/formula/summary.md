# design_artifact 结果汇总（provider=glm, model=glm-5.3-flash, seed=20260906）

## ValidityGate 分布（先看 gate，再看子分）

- 任务总数: 6
- gate 通过: 5
- gate 失败: 1（直接 0 分）
- 作废: 0
- gate 失败原因分布: {'missing_output': 1}

## 均分: 0.7998（gate 均值 5/6）

## 每任务明细

| task | gate | 失败模式 | vol_rel | bbox_max_rel | iface | physics | req | score |
| --- | --- | --- | --- | --- | --- | --- | --- | --- |
| ssb_23_24 | 1 | - | - | - | - | 1.0 | 1.0 | 1.0 |
| ssb_269_43 | 1 | - | - | - | - | 1.0 | 1.0 | 1.0 |
| ssb_279_23 | 1 | - | - | - | - | 0.75 | 1.0 | 0.875 |
| ssb_290_27 | 1 | - | - | - | - | 0.8478 | 1.0 | 0.9239 |
| ssb_341_40 | 1 | - | - | - | - | 1.0 | 1.0 | 1.0 |
| ssb_455_35 | 0 | missing_output | - | - | - | 0.0 | 0.0 | 0.0 |
