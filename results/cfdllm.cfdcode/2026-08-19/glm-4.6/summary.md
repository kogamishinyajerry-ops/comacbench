# code_exec 结果汇总（provider=glm, model=glm-4.6, seed=0）

## ValidityGate 分布（先看 gate，再看子分）

- 任务总数: 15
- gate 通过: 11
- gate 失败: 4（直接 0 分）
- 作废: 0
- gate 失败原因分布: {'non_physical_values': 2, 'missing_output': 2}

## physics（隐藏测试/数值） 分布（n=15）

- =1.0: 0
- 0.5-1.0: 6
- 0-0.5: 5
- =0.0: 4

## robustness（确定性） 分布（n=11）

- =1.0: 11
- 0.5-1.0: 0
- 0-0.5: 0
- =0.0: 0

## 每任务明细

| task | gate | physics | robust | score | 关键信息 |
| --- | --- | --- | --- | --- | --- |
| cfdcode_1d_burgers_equation | 0 | 0.0 | None | 0.0 | fields [] missing=[] |
| cfdcode_1d_diffusion | 1 | 0.9762 | 1.0 | 0.9881 | fields ['u'] missing=[] |
| cfdcode_1d_euler_shock_tube | 0 | 0.0 | None | 0.0 | fields [] missing=['E'] |
| cfdcode_1d_linear_convection | 0 | 0.0 | None | 0.0 | fields [] missing=['u'] |
| cfdcode_1d_nonlinear_convection | 1 | 0.1765 | 1.0 | 0.58825 | fields ['u'] missing=[] |
| cfdcode_2d_burgers_equation | 1 | 0.9993 | 1.0 | 0.99965 | fields ['u', 'v'] missing=[] |
| cfdcode_2d_convection | 1 | 0.9933 | 1.0 | 0.99665 | fields ['u', 'v'] missing=[] |
| cfdcode_2d_inviscid_burgers | 1 | 0.9653 | 1.0 | 0.98265 | fields ['u', 'v'] missing=[] |
| cfdcode_2d_laplace_equation | 1 | 0.8015 | 1.0 | 0.90075 | fields ['p'] missing=[] |
| cfdcode_2d_linear_convection | 1 | 0.9909 | 1.0 | 0.99545 | fields ['u'] missing=[] |
| cfdcode_2d_navier_stokes_channel | 1 | 0.3362 | 1.0 | 0.6681 | fields ['p', 'u', 'v'] missing=[] |
| cfdcode_2d_poisson_equation | 1 | 0.219 | 1.0 | 0.6095 | fields ['p'] missing=[] |
| cfdcode_2d_steady_heat_equation | 1 | 0.1091 | 1.0 | 0.55455 | fields ['T'] missing=[] |
| cfdcode_flow_past_circular_cylinder | 0 | 0.0 | None | 0.0 | fields [] missing=[] |
| cfdcode_lid_driven_cavity | 1 | 0.0064 | 1.0 | 0.5032 | fields ['p', 'u', 'v'] missing=[] |
