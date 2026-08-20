# code_exec 结果汇总（provider=glm, model=glm-4.6, seed=0）

## ValidityGate 分布（先看 gate，再看子分）

- 任务总数: 52
- gate 通过: 29
- gate 失败: 23（直接 0 分）
- 作废: 0
- gate 失败原因分布: {'code_not_executable': 23}

## physics（隐藏测试/数值） 分布（n=52）

- =1.0: 11
- 0.5-1.0: 11
- 0-0.5: 5
- =0.0: 25

## robustness（确定性） 分布（n=52）

- =1.0: 29
- 0.5-1.0: 0
- 0-0.5: 0
- =0.0: 23

## 每任务明细

| task | gate | physics | robust | score | 关键信息 |
| --- | --- | --- | --- | --- | --- |
| scicode_p001 | 1 | 1.0 | 1.0 | 1.0 | steps 1/1, cases 3/3 |
| scicode_p002 | 0 | 0.0 | 0.0 | 0.0 |  |
| scicode_p003 | 1 | 1.0 | 1.0 | 1.0 | steps 1/1, cases 3/3 |
| scicode_p004 | 1 | 1.0 | 1.0 | 1.0 | steps 1/1, cases 3/3 |
| scicode_p005 | 1 | 0.6667 | 1.0 | 0.83335 | steps 0/1, cases 2/3 |
| scicode_p006 | 1 | 1.0 | 1.0 | 1.0 | steps 1/1, cases 4/4 |
| scicode_p007 | 1 | 0.0 | 1.0 | 0.5 | steps 0/1, cases 0/4 |
| scicode_p008 | 1 | 0.0 | 1.0 | 0.5 | steps 0/1, cases 0/4 |
| scicode_p009 | 1 | 0.3333 | 1.0 | 0.66665 | steps 0/1, cases 1/3 |
| scicode_p010 | 0 | 0.0 | 0.0 | 0.0 |  |
| scicode_p011 | 0 | 0.0 | 0.0 | 0.0 |  |
| scicode_p013 | 0 | 0.0 | 0.0 | 0.0 |  |
| scicode_p014 | 1 | 0.8333 | 1.0 | 0.91665 | steps 1/2, cases 5/6 |
| scicode_p015 | 1 | 1.0 | 1.0 | 1.0 | steps 2/2, cases 7/7 |
| scicode_p016 | 1 | 0.8333 | 1.0 | 0.91665 | steps 1/2, cases 5/6 |
| scicode_p017 | 0 | 0.0 | 0.0 | 0.0 |  |
| scicode_p018 | 0 | 0.0 | 0.0 | 0.0 |  |
| scicode_p019 | 1 | 1.0 | 1.0 | 1.0 | steps 2/2, cases 7/7 |
| scicode_p020 | 1 | 1.0 | 1.0 | 1.0 | steps 2/2, cases 6/6 |
| scicode_p022 | 0 | 0.0 | 0.0 | 0.0 |  |
| scicode_p023 | 1 | 0.9231 | 1.0 | 0.96155 | steps 2/3, cases 12/13 |
| scicode_p024 | 1 | 0.4444 | 1.0 | 0.7222 | steps 1/3, cases 4/9 |
| scicode_p028 | 0 | 0.0 | 0.0 | 0.0 |  |
| scicode_p029 | 1 | 1.0 | 1.0 | 1.0 | steps 3/3, cases 10/10 |
| scicode_p031 | 1 | 0.3 | 1.0 | 0.65 | steps 1/3, cases 3/10 |
| scicode_p032 | 0 | 0.0 | 0.0 | 0.0 |  |
| scicode_p033 | 1 | 0.3333 | 1.0 | 0.66665 | steps 1/3, cases 3/9 |
| scicode_p037 | 0 | 0.0 | 0.0 | 0.0 |  |
| scicode_p038 | 1 | 1.0 | 1.0 | 1.0 | steps 3/3, cases 10/10 |
| scicode_p040 | 1 | 0.3333 | 1.0 | 0.66665 | steps 1/3, cases 3/9 |
| scicode_p043 | 1 | 0.7 | 1.0 | 0.85 | steps 2/3, cases 7/10 |
| scicode_p045 | 1 | 0.5 | 1.0 | 0.75 | steps 2/4, cases 6/12 |
| scicode_p049 | 1 | 1.0 | 1.0 | 1.0 | steps 4/4, cases 13/13 |
| scicode_p050 | 1 | 0.75 | 1.0 | 0.875 | steps 3/4, cases 9/12 |
| scicode_p052 | 1 | 0.5833 | 1.0 | 0.79165 | steps 1/4, cases 7/12 |
| scicode_p054 | 0 | 0.0 | 0.0 | 0.0 |  |
| scicode_p055 | 0 | 0.0 | 0.0 | 0.0 |  |
| scicode_p057 | 0 | 0.0 | 0.0 | 0.0 |  |
| scicode_p058 | 1 | 0.625 | 1.0 | 0.8125 | steps 3/5, cases 10/16 |
| scicode_p059 | 0 | 0.0 | 0.0 | 0.0 |  |
| scicode_p061 | 0 | 0.0 | 0.0 | 0.0 |  |
| scicode_p062 | 0 | 0.0 | 0.0 | 0.0 |  |
| scicode_p065 | 0 | 0.0 | 0.0 | 0.0 |  |
| scicode_p067 | 0 | 0.0 | 0.0 | 0.0 |  |
| scicode_p069 | 0 | 0.0 | 0.0 | 0.0 |  |
| scicode_p070 | 0 | 0.0 | 0.0 | 0.0 |  |
| scicode_p071 | 0 | 0.0 | 0.0 | 0.0 |  |
| scicode_p072 | 1 | 0.8125 | 1.0 | 0.90625 | steps 6/9, cases 26/32 |
| scicode_p073 | 0 | 0.0 | 0.0 | 0.0 |  |
| scicode_p074 | 1 | 1.0 | 1.0 | 1.0 | steps 1/1, cases 3/3 |
| scicode_p075 | 0 | 0.0 | 0.0 | 0.0 |  |
| scicode_p078 | 1 | 0.6667 | 1.0 | 0.83335 | steps 2/3, cases 6/9 |
