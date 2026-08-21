# design_artifact 结果汇总（provider=minimax, model=MiniMax-M3, seed=0）

## ValidityGate 分布（先看 gate，再看子分）

- 任务总数: 22
- gate 通过: 16
- gate 失败: 6（直接 0 分）
- 作废: 0
- gate 失败原因分布: {'code_not_executable': 5, 'invalid_geometry': 1}

## 均分: 0.7083（gate 均值 16/22）

## 每任务明细

| task | gate | 失败模式 | vol_rel | bbox_max_rel | iface | physics | req | score |
| --- | --- | --- | --- | --- | --- | --- | --- | --- |
| cg_bossplate_001 | 1 | - | 0.00e+00 | 0.00e+00 | 3/3 | 1.0 | 1.0 | 1.0 |
| cg_bossplate_002 | 1 | - | 0.00e+00 | 0.00e+00 | 3/3 | 1.0 | 1.0 | 1.0 |
| cg_bossplate_003 | 1 | - | 0.00e+00 | 0.00e+00 | 3/3 | 1.0 | 1.0 | 1.0 |
| cg_flange_001 | 1 | - | 0.00e+00 | 0.00e+00 | 3/3 | 1.0 | 1.0 | 1.0 |
| cg_flange_002 | 1 | - | 0.00e+00 | 0.00e+00 | 3/3 | 1.0 | 1.0 | 1.0 |
| cg_flange_003 | 1 | - | 0.00e+00 | 0.00e+00 | 3/3 | 1.0 | 1.0 | 1.0 |
| cg_flange_004 | 1 | - | 0.00e+00 | 0.00e+00 | 3/3 | 1.0 | 1.0 | 1.0 |
| cg_lbracket_001 | 1 | - | 3.24e-01 | 1.00e+00 | 2/3 | 0.5 | 0.6667 | 0.58335 |
| cg_lbracket_002 | 0 | code_not_executable | - | - | - | 0.0 | 0.0 | 0.0 |
| cg_lbracket_003 | 0 | code_not_executable | - | - | - | 0.0 | 0.0 | 0.0 |
| cg_lbracket_004 | 0 | code_not_executable | - | - | - | 0.0 | 0.0 | 0.0 |
| cg_plate_001 | 1 | - | 0.00e+00 | 0.00e+00 | 3/3 | 1.0 | 1.0 | 1.0 |
| cg_plate_002 | 0 | code_not_executable | - | - | - | 0.0 | 0.0 | 0.0 |
| cg_plate_003 | 1 | - | 0.00e+00 | 0.00e+00 | 3/3 | 1.0 | 1.0 | 1.0 |
| cg_plate_004 | 0 | code_not_executable | - | - | - | 0.0 | 0.0 | 0.0 |
| cg_shaft_001 | 0 | invalid_geometry | - | - | - | 0.0 | 0.0 | 0.0 |
| cg_shaft_002 | 1 | - | 0.00e+00 | 5.00e-09 | 5/5 | 1.0 | 1.0 | 1.0 |
| cg_shaft_003 | 1 | - | 0.00e+00 | 4.00e-09 | 5/5 | 1.0 | 1.0 | 1.0 |
| cg_shaft_004 | 1 | - | 0.00e+00 | 0.00e+00 | 5/5 | 1.0 | 1.0 | 1.0 |
| cg_sleeve_001 | 1 | - | 0.00e+00 | 0.00e+00 | 3/3 | 1.0 | 1.0 | 1.0 |
| cg_sleeve_002 | 1 | - | 0.00e+00 | 0.00e+00 | 3/3 | 1.0 | 1.0 | 1.0 |
| cg_sleeve_003 | 1 | - | 0.00e+00 | 0.00e+00 | 3/3 | 1.0 | 1.0 | 1.0 |
