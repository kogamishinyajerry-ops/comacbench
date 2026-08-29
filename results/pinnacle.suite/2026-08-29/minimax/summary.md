# code_exec 结果汇总（provider=minimax, model=MiniMax-M3, seed=0）

## ValidityGate 分布（先看 gate，再看子分）

- 任务总数: 3
- gate 通过: 2
- gate 失败: 1（直接 0 分）
- 作废: 0
- gate 失败原因分布: {'code_not_executable': 1}

## physics（隐藏测试/数值） 分布（n=3）

- =1.0: 2
- 0.5-1.0: 0
- 0-0.5: 0
- =0.0: 1

## 每任务明细

| task | gate | physics | robust | score | 关键信息 |
| --- | --- | --- | --- | --- | --- |
| pinnacle_burgers1d | 1 | 1.0 | None | 1.0 | fields [] missing=None |
| pinnacle_helmholtz2d | 0 | 0.0 | None | 0.0 | fields [] missing=None |
| pinnacle_poisson1d | 1 | 1.0 | None | 1.0 | fields [] missing=None |
