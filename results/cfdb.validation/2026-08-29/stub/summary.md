# simulation_agent 结果汇总（provider=stub, model=n/a, seed=0）

## ValidityGate 分布（先看 gate，再看子分）

- 任务总数: 8
- gate 通过: 0
- gate 失败: 8（直接 0 分）
- 作废: 0
- gate 失败原因分布: {'missing_output': 8}

## physics（NMSE 阈值分）分布（n=8）

- 1.0: 0
- 0.5: 0
- 0.0: 8

## 每任务明细

| task | gate | nmse | nmse_score | score | 关键信息 |
| --- | --- | --- | --- | --- | --- |
| cfdb_vd_backward_facing_step_laminar | 0 | - | 0.0 | 0.0 | missing=['case/system/controlDict', 'case/constant', 'case/0'] |
| cfdb_vd_cylinder_re100 | 0 | - | 0.0 | 0.0 | missing=['case/system/controlDict', 'case/constant', 'case/0'] |
| cfdb_vd_cylinder_re40 | 0 | - | 0.0 | 0.0 | missing=['case/system/controlDict', 'case/constant', 'case/0'] |
| cfdb_vd_lid_driven_cavity_re1000 | 0 | - | 0.0 | 0.0 | missing=['case/system/controlDict', 'case/constant', 'case/0'] |
| cfdb_vd_lid_driven_cavity_re400 | 0 | - | 0.0 | 0.0 | missing=['case/system/controlDict', 'case/constant', 'case/0'] |
| cfdb_vd_natural_convection_cavity | 0 | - | 0.0 | 0.0 | missing=['case/system/controlDict', 'case/constant', 'case/0'] |
| cfdb_vd_turbulent_channel_retau180 | 0 | - | 0.0 | 0.0 | missing=['case/system/controlDict', 'case/constant', 'case/0'] |
| cfdb_vd_turbulent_flat_plate | 0 | - | 0.0 | 0.0 | missing=['case/system/controlDict', 'case/constant', 'case/0'] |
