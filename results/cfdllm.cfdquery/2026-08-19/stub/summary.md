# qa_grounded 结果汇总（provider=stub, model=n/a, seed=0）

## ValidityGate 分布（先看 gate，再看子分）

- 任务总数: 90
- gate 通过: 90
- gate 失败: 0（直接 0 分）
- 作废（不计分）: 0
- gate 失败原因分布: 无

## 客观层（requirements）

- 正确: 25/90（accuracy = 0.2778，分母=计分任务数）
- 子分适用性: physics=N/A（无证据/拒答层）；objective=N/A（并入 requirements）；robustness=采样一致性（本配置样本=1，不适用）
- 权重（任务 YAML 覆写）: score = gate × 1.0×requirements

## 每题明细

| task | gate | answer_correct | score |
| --- | --- | --- | --- |
| cfdquery_q001 | 1 | 0 | 0.0 |
| cfdquery_q002 | 1 | 0 | 0.0 |
| cfdquery_q003 | 1 | 1 | 1.0 |
| cfdquery_q004 | 1 | 0 | 0.0 |
| cfdquery_q005 | 1 | 0 | 0.0 |
| cfdquery_q006 | 1 | 0 | 0.0 |
| cfdquery_q007 | 1 | 0 | 0.0 |
| cfdquery_q008 | 1 | 0 | 0.0 |
| cfdquery_q009 | 1 | 1 | 1.0 |
| cfdquery_q010 | 1 | 1 | 1.0 |
| cfdquery_q011 | 1 | 0 | 0.0 |
| cfdquery_q012 | 1 | 0 | 0.0 |
| cfdquery_q013 | 1 | 0 | 0.0 |
| cfdquery_q014 | 1 | 0 | 0.0 |
| cfdquery_q015 | 1 | 0 | 0.0 |
| cfdquery_q016 | 1 | 0 | 0.0 |
| cfdquery_q017 | 1 | 0 | 0.0 |
| cfdquery_q018 | 1 | 0 | 0.0 |
| cfdquery_q019 | 1 | 0 | 0.0 |
| cfdquery_q020 | 1 | 0 | 0.0 |
| cfdquery_q021 | 1 | 1 | 1.0 |
| cfdquery_q022 | 1 | 1 | 1.0 |
| cfdquery_q023 | 1 | 0 | 0.0 |
| cfdquery_q024 | 1 | 0 | 0.0 |
| cfdquery_q025 | 1 | 0 | 0.0 |
| cfdquery_q026 | 1 | 0 | 0.0 |
| cfdquery_q027 | 1 | 0 | 0.0 |
| cfdquery_q028 | 1 | 0 | 0.0 |
| cfdquery_q029 | 1 | 1 | 1.0 |
| cfdquery_q030 | 1 | 0 | 0.0 |
| cfdquery_q031 | 1 | 0 | 0.0 |
| cfdquery_q032 | 1 | 0 | 0.0 |
| cfdquery_q033 | 1 | 1 | 1.0 |
| cfdquery_q034 | 1 | 0 | 0.0 |
| cfdquery_q035 | 1 | 1 | 1.0 |
| cfdquery_q036 | 1 | 0 | 0.0 |
| cfdquery_q037 | 1 | 1 | 1.0 |
| cfdquery_q038 | 1 | 1 | 1.0 |
| cfdquery_q039 | 1 | 0 | 0.0 |
| cfdquery_q040 | 1 | 1 | 1.0 |
| cfdquery_q041 | 1 | 0 | 0.0 |
| cfdquery_q042 | 1 | 0 | 0.0 |
| cfdquery_q043 | 1 | 0 | 0.0 |
| cfdquery_q044 | 1 | 0 | 0.0 |
| cfdquery_q045 | 1 | 0 | 0.0 |
| cfdquery_q046 | 1 | 0 | 0.0 |
| cfdquery_q047 | 1 | 0 | 0.0 |
| cfdquery_q048 | 1 | 0 | 0.0 |
| cfdquery_q049 | 1 | 0 | 0.0 |
| cfdquery_q050 | 1 | 1 | 1.0 |
| cfdquery_q051 | 1 | 1 | 1.0 |
| cfdquery_q052 | 1 | 0 | 0.0 |
| cfdquery_q053 | 1 | 0 | 0.0 |
| cfdquery_q054 | 1 | 1 | 1.0 |
| cfdquery_q055 | 1 | 0 | 0.0 |
| cfdquery_q056 | 1 | 0 | 0.0 |
| cfdquery_q057 | 1 | 1 | 1.0 |
| cfdquery_q058 | 1 | 0 | 0.0 |
| cfdquery_q059 | 1 | 1 | 1.0 |
| cfdquery_q060 | 1 | 0 | 0.0 |
| cfdquery_q061 | 1 | 1 | 1.0 |
| cfdquery_q062 | 1 | 0 | 0.0 |
| cfdquery_q063 | 1 | 0 | 0.0 |
| cfdquery_q064 | 1 | 0 | 0.0 |
| cfdquery_q065 | 1 | 1 | 1.0 |
| cfdquery_q066 | 1 | 0 | 0.0 |
| cfdquery_q067 | 1 | 1 | 1.0 |
| cfdquery_q068 | 1 | 0 | 0.0 |
| cfdquery_q069 | 1 | 0 | 0.0 |
| cfdquery_q070 | 1 | 1 | 1.0 |
| cfdquery_q071 | 1 | 0 | 0.0 |
| cfdquery_q072 | 1 | 0 | 0.0 |
| cfdquery_q073 | 1 | 0 | 0.0 |
| cfdquery_q074 | 1 | 1 | 1.0 |
| cfdquery_q075 | 1 | 0 | 0.0 |
| cfdquery_q076 | 1 | 1 | 1.0 |
| cfdquery_q077 | 1 | 1 | 1.0 |
| cfdquery_q078 | 1 | 0 | 0.0 |
| cfdquery_q079 | 1 | 0 | 0.0 |
| cfdquery_q080 | 1 | 0 | 0.0 |
| cfdquery_q081 | 1 | 0 | 0.0 |
| cfdquery_q082 | 1 | 0 | 0.0 |
| cfdquery_q083 | 1 | 0 | 0.0 |
| cfdquery_q084 | 1 | 0 | 0.0 |
| cfdquery_q085 | 1 | 0 | 0.0 |
| cfdquery_q086 | 1 | 0 | 0.0 |
| cfdquery_q087 | 1 | 0 | 0.0 |
| cfdquery_q088 | 1 | 0 | 0.0 |
| cfdquery_q089 | 1 | 1 | 1.0 |
| cfdquery_q090 | 1 | 1 | 1.0 |
