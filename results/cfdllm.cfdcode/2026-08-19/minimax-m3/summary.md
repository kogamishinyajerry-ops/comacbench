# code_exec 结果汇总（provider=minimax, model=MiniMax-M3, seed=0）

## ValidityGate 分布（先看 gate，再看子分）

- 任务总数: 15
- gate 通过: 8
- gate 失败: 7（直接 0 分）
- 作废: 0
- gate 失败原因分布: {'code_not_executable': 4, 'non_physical_values': 2, 'missing_output': 1}

## physics（隐藏测试/数值） 分布（n=15）

- =1.0: 0
- 0.5-1.0: 6
- 0-0.5: 2
- =0.0: 7

## robustness（确定性） 分布（n=10）

- =1.0: 8
- 0.5-1.0: 0
- 0-0.5: 0
- =0.0: 2

## 每任务明细

| task | gate | physics | robust | score | 关键信息 |
| --- | --- | --- | --- | --- | --- |
| cfdcode_1d_burgers_equation | 1 | 0.9928 | 1.0 | 0.9964 | fields ['u'] missing=[] |
| cfdcode_1d_diffusion | 1 | 0.9765 | 1.0 | 0.98825 | fields ['u'] missing=[] |
| cfdcode_1d_euler_shock_tube | 1 | 0.9743 | 1.0 | 0.98715 | fields ['E', 'rho', 'u'] missing=[] |
| cfdcode_1d_linear_convection | 0 | 0.0 | None | 0.0 | fields [] missing=['u'] |
| cfdcode_1d_nonlinear_convection | 1 | 0.1782 | 1.0 | 0.5891 | fields ['u'] missing=[] |
| cfdcode_2d_burgers_equation | 0 | 0.0 | 0.0 | 0.0 |  |
| cfdcode_2d_convection | 1 | 0.979 | 1.0 | 0.9895 | fields ['u', 'v'] missing=[] |
| cfdcode_2d_inviscid_burgers | 1 | 0.9549 | 1.0 | 0.97745 | fields ['u', 'v'] missing=[] |
| cfdcode_2d_laplace_equation | 0 | 0.0 | None | 0.0 | fields [] missing=[] |
| cfdcode_2d_linear_convection | 1 | 0.9345 | 1.0 | 0.96725 | fields ['u'] missing=[] |
| cfdcode_2d_navier_stokes_channel | 0 | 0.0 | None | 0.0 | fields [] missing=[] |
| cfdcode_2d_poisson_equation | 0 | 0.0 | None | 0.0 | fields [] missing=['p'] |
| cfdcode_2d_steady_heat_equation | 1 | 0.1091 | 1.0 | 0.55455 | fields ['T'] missing=[] |
| cfdcode_flow_past_circular_cylinder | 0 | 0.0 | 0.0 | 0.0 |  |
| cfdcode_lid_driven_cavity | 0 | 0.0 | None | 0.0 | fields [] missing=['u', 'v', 'p'] |
