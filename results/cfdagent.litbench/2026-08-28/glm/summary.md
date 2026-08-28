# qa_grounded 结果汇总（provider=glm, model=glm-4.6, seed=0）

## ValidityGate 分布（先看 gate，再看子分）

- 任务总数: 60
- gate 通过: 60
- gate 失败: 0（直接 0 分）
- 作废（不计分）: 0
- gate 失败原因分布: 无

## 客观层（requirements）

- 正确: 47/60（accuracy = 0.7833，分母=计分任务数）
- 子分适用性: physics=N/A（无证据/拒答层）；objective=N/A（并入 requirements）；robustness=采样一致性（本配置样本=1，不适用）
- 权重（任务 YAML 覆写）: score = gate × 1.0×requirements

## 每题明细

| task | gate | answer_correct | score |
| --- | --- | --- | --- |
| cfdagent_q001 | 1 | 0 | 0.0 |
| cfdagent_q002 | 1 | 1 | 1.0 |
| cfdagent_q003 | 1 | 1 | 1.0 |
| cfdagent_q004 | 1 | 0 | 0.0 |
| cfdagent_q005 | 1 | 1 | 1.0 |
| cfdagent_q006 | 1 | 1 | 1.0 |
| cfdagent_q007 | 1 | 1 | 1.0 |
| cfdagent_q008 | 1 | 1 | 1.0 |
| cfdagent_q009 | 1 | 0 | 0.0 |
| cfdagent_q010 | 1 | 1 | 1.0 |
| cfdagent_q011 | 1 | 1 | 1.0 |
| cfdagent_q012 | 1 | 1 | 1.0 |
| cfdagent_q013 | 1 | 0 | 0.0 |
| cfdagent_q014 | 1 | 1 | 1.0 |
| cfdagent_q015 | 1 | 1 | 1.0 |
| cfdagent_q016 | 1 | 0 | 0.0 |
| cfdagent_q017 | 1 | 0 | 0.0 |
| cfdagent_q018 | 1 | 1 | 1.0 |
| cfdagent_q019 | 1 | 1 | 1.0 |
| cfdagent_q020 | 1 | 0 | 0.0 |
| cfdagent_q021 | 1 | 1 | 1.0 |
| cfdagent_q022 | 1 | 1 | 1.0 |
| cfdagent_q023 | 1 | 1 | 1.0 |
| cfdagent_q024 | 1 | 1 | 1.0 |
| cfdagent_q025 | 1 | 1 | 1.0 |
| cfdagent_q026 | 1 | 1 | 1.0 |
| cfdagent_q027 | 1 | 0 | 0.0 |
| cfdagent_q028 | 1 | 1 | 1.0 |
| cfdagent_q029 | 1 | 1 | 1.0 |
| cfdagent_q030 | 1 | 1 | 1.0 |
| cfdagent_q031 | 1 | 0 | 0.0 |
| cfdagent_q032 | 1 | 1 | 1.0 |
| cfdagent_q033 | 1 | 1 | 1.0 |
| cfdagent_q034 | 1 | 0 | 0.0 |
| cfdagent_q035 | 1 | 1 | 1.0 |
| cfdagent_q036 | 1 | 1 | 1.0 |
| cfdagent_q037 | 1 | 1 | 1.0 |
| cfdagent_q038 | 1 | 1 | 1.0 |
| cfdagent_q039 | 1 | 1 | 1.0 |
| cfdagent_q040 | 1 | 1 | 1.0 |
| cfdagent_q041 | 1 | 1 | 1.0 |
| cfdagent_q042 | 1 | 0 | 0.0 |
| cfdagent_q043 | 1 | 1 | 1.0 |
| cfdagent_q044 | 1 | 1 | 1.0 |
| cfdagent_q045 | 1 | 1 | 1.0 |
| cfdagent_q046 | 1 | 0 | 0.0 |
| cfdagent_q047 | 1 | 1 | 1.0 |
| cfdagent_q048 | 1 | 1 | 1.0 |
| cfdagent_q049 | 1 | 1 | 1.0 |
| cfdagent_q050 | 1 | 1 | 1.0 |
| cfdagent_q051 | 1 | 1 | 1.0 |
| cfdagent_q052 | 1 | 1 | 1.0 |
| cfdagent_q053 | 1 | 0 | 0.0 |
| cfdagent_q054 | 1 | 1 | 1.0 |
| cfdagent_q055 | 1 | 1 | 1.0 |
| cfdagent_q056 | 1 | 1 | 1.0 |
| cfdagent_q057 | 1 | 1 | 1.0 |
| cfdagent_q058 | 1 | 1 | 1.0 |
| cfdagent_q059 | 1 | 1 | 1.0 |
| cfdagent_q060 | 1 | 1 | 1.0 |
