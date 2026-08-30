# simulation_agent 结果汇总（provider=oracle, model=n/a, seed=0）

## ValidityGate 分布（先看 gate，再看子分）

- 任务总数: 15
- gate 通过: 13
- gate 失败: 2（直接 0 分）
- 作废: 0
- gate 失败原因分布: {'code_not_executable': 1, 'simulation_failed': 1}

## physics（NMSE 阈值分）分布（n=15）

- 1.0: 12
- 0.5: 0
- 0.0: 3

## 每任务明细

| task | gate | nmse | nmse_score | score | 关键信息 |
| --- | --- | --- | --- | --- | --- |
| cfdb_cs_blasius_plate_from_brief | 1 | - | 1.0 | 1.0 | missing=exec_fail |
| cfdb_cs_cavity_from_brief | 1 | - | 1.0 | 1.0 | missing=exec_fail |
| cfdb_cs_cavity_re400_from_brief | 1 | - | 1.0 | 1.0 | missing=exec_fail |
| cfdb_cs_couette_from_brief | 1 | - | 1.0 | 1.0 | missing=exec_fail |
| cfdb_cs_heat_conduction_from_brief | 1 | - | 1.0 | 1.0 | missing=exec_fail |
| cfdb_cs_naca0012_force_from_brief | 1 | - | 1.0 | 1.0 | missing=exec_fail |
| cfdb_cs_natural_convection_from_brief | 1 | - | 1.0 | 1.0 | missing=exec_fail |
| cfdb_cs_oblique_shock_from_brief | 1 | - | 0.0 | 0.4 | missing=exec_fail |
| cfdb_cs_pipe_from_brief | 0 | - | 0.0 | 0.0 | missing=exec_fail |
| cfdb_cs_poiseuille_from_brief | 1 | - | 1.0 | 1.0 | missing=exec_fail |
| cfdb_cs_sod_shock_from_brief | 1 | - | 1.0 | 1.0 | missing=exec_fail |
| cfdb_cs_taylor_couette_from_brief | 1 | - | 1.0 | 1.0 | missing=exec_fail |
| cfdb_cs_taylor_green_from_brief | 0 | - | 0.0 | 0.0 | missing=exec_fail |
| cfdb_cs_turbulent_channel_from_brief | 1 | - | 1.0 | 1.0 | missing=exec_fail |
| cfdb_cs_turbulent_plate_from_brief | 1 | - | 1.0 | 1.0 | missing=exec_fail |
