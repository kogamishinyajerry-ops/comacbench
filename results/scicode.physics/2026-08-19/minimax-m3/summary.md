# code_exec 结果汇总（provider=minimax, model=MiniMax-M3, seed=0）

## ValidityGate 分布（先看 gate，再看子分）

- 任务总数: 52
- gate 通过: 42
- gate 失败: 10（直接 0 分）
- 作废: 0
- gate 失败原因分布: {'code_not_executable': 8, 'sandbox_escape_attempt': 1, 'timeout': 1}

## physics（隐藏测试/数值） 分布（n=52）

- =1.0: 14
- 0.5-1.0: 14
- 0-0.5: 12
- =0.0: 12

## robustness（确定性） 分布（n=52）

- =1.0: 42
- 0.5-1.0: 0
- 0-0.5: 0
- =0.0: 10

## 每任务明细

| task | gate | physics | robust | score | 关键信息 |
| --- | --- | --- | --- | --- | --- |
| scicode_p001 | 1 | 1.0 | 1.0 | 1.0 | steps 1/1, cases 3/3 |
| scicode_p002 | 1 | 0.25 | 1.0 | 0.625 | steps 0/1, cases 1/4 |
| scicode_p003 | 1 | 1.0 | 1.0 | 1.0 | steps 1/1, cases 3/3 |
| scicode_p004 | 1 | 1.0 | 1.0 | 1.0 | steps 1/1, cases 3/3 |
| scicode_p005 | 1 | 0.6667 | 1.0 | 0.83335 | steps 0/1, cases 2/3 |
| scicode_p006 | 1 | 1.0 | 1.0 | 1.0 | steps 1/1, cases 4/4 |
| scicode_p007 | 1 | 1.0 | 1.0 | 1.0 | steps 1/1, cases 4/4 |
| scicode_p008 | 1 | 0.25 | 1.0 | 0.625 | steps 0/1, cases 1/4 |
| scicode_p009 | 1 | 1.0 | 1.0 | 1.0 | steps 1/1, cases 3/3 |
| scicode_p010 | 1 | 0.5952 | 1.0 | 0.7976 | steps 6/11, cases 25/42 |
| scicode_p011 | 0 | 0.0 | 0.0 | 0.0 |  |
| scicode_p013 | 1 | 0.3488 | 1.0 | 0.6744 | steps 5/14, cases 15/43 |
| scicode_p014 | 1 | 0.8333 | 1.0 | 0.91665 | steps 1/2, cases 5/6 |
| scicode_p015 | 1 | 1.0 | 1.0 | 1.0 | steps 2/2, cases 7/7 |
| scicode_p016 | 1 | 1.0 | 1.0 | 1.0 | steps 2/2, cases 6/6 |
| scicode_p017 | 1 | 0.25 | 1.0 | 0.625 | steps 0/2, cases 2/8 |
| scicode_p018 | 1 | 0.1667 | 1.0 | 0.58335 | steps 0/2, cases 1/6 |
| scicode_p019 | 1 | 1.0 | 1.0 | 1.0 | steps 2/2, cases 7/7 |
| scicode_p020 | 0 | 0.0 | 0.0 | 0.0 |  |
| scicode_p022 | 0 | 0.0 | 0.0 | 0.0 |  |
| scicode_p023 | 1 | 1.0 | 1.0 | 1.0 | steps 3/3, cases 13/13 |
| scicode_p024 | 1 | 0.3333 | 1.0 | 0.66665 | steps 1/3, cases 3/9 |
| scicode_p028 | 1 | 0.0 | 1.0 | 0.5 | steps 0/3, cases 0/10 |
| scicode_p029 | 1 | 1.0 | 1.0 | 1.0 | steps 3/3, cases 10/10 |
| scicode_p031 | 1 | 0.3 | 1.0 | 0.65 | steps 1/3, cases 3/10 |
| scicode_p032 | 1 | 0.4 | 1.0 | 0.7 | steps 1/3, cases 4/10 |
| scicode_p033 | 1 | 0.3333 | 1.0 | 0.66665 | steps 1/3, cases 3/9 |
| scicode_p037 | 0 | 0.0 | 0.0 | 0.0 |  |
| scicode_p038 | 1 | 1.0 | 1.0 | 1.0 | steps 3/3, cases 10/10 |
| scicode_p040 | 1 | 0.3333 | 1.0 | 0.66665 | steps 1/3, cases 3/9 |
| scicode_p043 | 0 | 0.0 | 0.0 | 0.0 |  |
| scicode_p045 | 1 | 0.5 | 1.0 | 0.75 | steps 1/4, cases 6/12 |
| scicode_p049 | 1 | 1.0 | 1.0 | 1.0 | steps 4/4, cases 13/13 |
| scicode_p050 | 1 | 0.6667 | 1.0 | 0.83335 | steps 2/4, cases 8/12 |
| scicode_p052 | 1 | 0.5833 | 1.0 | 0.79165 | steps 1/4, cases 7/12 |
| scicode_p054 | 0 | 0.0 | 0.0 | 0.0 |  |
| scicode_p055 | 1 | 0.4 | 1.0 | 0.7 | steps 1/4, cases 6/15 |
| scicode_p057 | 1 | 0.8667 | 1.0 | 0.93335 | steps 4/5, cases 13/15 |
| scicode_p058 | 1 | 0.9375 | 1.0 | 0.96875 | steps 4/5, cases 15/16 |
| scicode_p059 | 1 | 1.0 | 1.0 | 1.0 | steps 5/5, cases 15/15 |
| scicode_p061 | 1 | 0.8125 | 1.0 | 0.90625 | steps 4/5, cases 13/16 |
| scicode_p062 | 0 | 0.0 | 0.0 | 0.0 |  |
| scicode_p065 | 1 | 0.9 | 1.0 | 0.95 | steps 4/6, cases 18/20 |
| scicode_p067 | 0 | 0.0 | 0.0 | 0.0 |  |
| scicode_p069 | 0 | 0.0 | 0.0 | 0.0 |  |
| scicode_p070 | 1 | 0.72 | 1.0 | 0.86 | steps 6/8, cases 18/25 |
| scicode_p071 | 1 | 0.4828 | 1.0 | 0.7414 | steps 4/9, cases 14/29 |
| scicode_p072 | 1 | 0.9062 | 1.0 | 0.9531 | steps 7/9, cases 29/32 |
| scicode_p073 | 0 | 0.0 | 0.0 | 0.0 |  |
| scicode_p074 | 1 | 0.0 | 1.0 | 0.5 | steps 0/1, cases 0/3 |
| scicode_p075 | 1 | 0.5714 | 1.0 | 0.7857 | steps 2/3, cases 4/7 |
| scicode_p078 | 1 | 0.6667 | 1.0 | 0.83335 | steps 2/3, cases 6/9 |
