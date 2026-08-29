# simulation_agent 结果汇总（provider=stub, model=n/a, seed=0）

## ValidityGate 分布（先看 gate，再看子分）

- 任务总数: 9
- gate 通过: 0
- gate 失败: 9（直接 0 分）
- 作废: 0
- gate 失败原因分布: {'missing_output': 9}

## physics（NMSE 阈值分）分布（n=9）

- 1.0: 0
- 0.5: 0
- 0.0: 9

## 每任务明细

| task | gate | nmse | nmse_score | score | 关键信息 |
| --- | --- | --- | --- | --- | --- |
| cfdb_vf_channel_poiseuille | 0 | - | 0.0 | 0.0 | missing=['case/system/controlDict', 'case/constant', 'case/0'] |
| cfdb_vf_couette_shear | 0 | - | 0.0 | 0.0 | missing=['case/system/controlDict', 'case/constant', 'case/0'] |
| cfdb_vf_flat_plate_blasius_of | 0 | - | 0.0 | 0.0 | missing=['case/system/controlDict', 'case/constant', 'case/0'] |
| cfdb_vf_heat_conduction_1d | 0 | - | 0.0 | 0.0 | missing=['case/system/controlDict', 'case/constant', 'case/0'] |
| cfdb_vf_oblique_shock | 0 | - | 0.0 | 0.0 | missing=['case/system/controlDict', 'case/constant', 'case/0'] |
| cfdb_vf_pipe_poiseuille | 0 | - | 0.0 | 0.0 | missing=['case/system/controlDict', 'case/constant', 'case/0'] |
| cfdb_vf_sod_shock_tube | 0 | - | 0.0 | 0.0 | missing=['case/system/controlDict', 'case/constant', 'case/0'] |
| cfdb_vf_taylor_couette | 0 | - | 0.0 | 0.0 | missing=['case/system/controlDict', 'case/constant', 'case/0'] |
| cfdb_vf_taylor_green_vortex | 0 | - | 0.0 | 0.0 | missing=['case/system/controlDict', 'case/constant', 'case/0'] |
