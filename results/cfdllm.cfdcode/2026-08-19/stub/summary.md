# code_exec 结果汇总（provider=stub, model=n/a, seed=0）

## ValidityGate 分布（先看 gate，再看子分）

- 任务总数: 15
- gate 通过: 0
- gate 失败: 15（直接 0 分）
- 作废: 0
- gate 失败原因分布: {'missing_output': 15}

## physics（隐藏测试/数值） 分布（n=15）

- =1.0: 0
- 0.5-1.0: 0
- 0-0.5: 0
- =0.0: 15

## 每任务明细

| task | gate | physics | robust | score | 关键信息 |
| --- | --- | --- | --- | --- | --- |
| cfdcode_1d_burgers_equation | 0 | 0.0 | None | 0.0 | fields [] missing=['u'] |
| cfdcode_1d_diffusion | 0 | 0.0 | None | 0.0 | fields [] missing=['u'] |
| cfdcode_1d_euler_shock_tube | 0 | 0.0 | None | 0.0 | fields [] missing=['E', 'rho', 'u'] |
| cfdcode_1d_linear_convection | 0 | 0.0 | None | 0.0 | fields [] missing=['u'] |
| cfdcode_1d_nonlinear_convection | 0 | 0.0 | None | 0.0 | fields [] missing=['u'] |
| cfdcode_2d_burgers_equation | 0 | 0.0 | None | 0.0 | fields [] missing=['u', 'v'] |
| cfdcode_2d_convection | 0 | 0.0 | None | 0.0 | fields [] missing=['u', 'v'] |
| cfdcode_2d_inviscid_burgers | 0 | 0.0 | None | 0.0 | fields [] missing=['u', 'v'] |
| cfdcode_2d_laplace_equation | 0 | 0.0 | None | 0.0 | fields [] missing=['p'] |
| cfdcode_2d_linear_convection | 0 | 0.0 | None | 0.0 | fields [] missing=['u'] |
| cfdcode_2d_navier_stokes_channel | 0 | 0.0 | None | 0.0 | fields [] missing=['u', 'v', 'p'] |
| cfdcode_2d_poisson_equation | 0 | 0.0 | None | 0.0 | fields [] missing=['p'] |
| cfdcode_2d_steady_heat_equation | 0 | 0.0 | None | 0.0 | fields [] missing=['T'] |
| cfdcode_flow_past_circular_cylinder | 0 | 0.0 | None | 0.0 | fields [] missing=['psi', 'omega'] |
| cfdcode_lid_driven_cavity | 0 | 0.0 | None | 0.0 | fields [] missing=['u', 'v', 'p'] |
