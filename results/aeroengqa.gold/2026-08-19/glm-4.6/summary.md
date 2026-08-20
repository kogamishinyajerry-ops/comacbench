# qa_grounded 结果汇总（provider=glm, model=glm-4.6, seed=0）

## ValidityGate 分布（先看 gate，再看子分）

- 任务总数: 80
- gate 通过: 80
- gate 失败: 0（直接 0 分）
- 作废（不计分）: 0
- gate 失败原因分布: 无

## 拒答层（refusal）

- 应拒答 40 题: 正确拒答 37（拒答正确率 0.9250）
- 应回答 40 题: 误拒答 3（误拒率 0.0750）

## 证据层（evidence support / fabrication）

- evidence_support 均值: 0.8938
- 捏造引用题数: 0/80（fabrication_rate>0）

## 客观层（requirements，仅应回答题）

- 满分 10/40；含部分分的均值 0.6304（归一化精确/数值容差=1，其余 token F1 部分分）

## 区分层（distinction：BASIS 结构声明）

- 合法声明率: 0.9750（80 题）
- 口径：BASIS ∈ report/computed/inferred；数据集无参考 basis 标签，逐字核验仅作诊断不进分（见任务 YAML grader 注释）

## 每题明细

| task | gate | refused | cite | support | fab | req | dist | score |
| --- | --- | --- | --- | --- | --- | --- | --- | --- |
| aeroengqa_mh_a001 | 1 | False | [2] | 0.5 | 0.0 | 0.2 | 1.0 | 0.5925 |
| aeroengqa_mh_a002 | 1 | False | [1] | 0.5 | 0.0 | 1.0 | 1.0 | 0.9125 |
| aeroengqa_mh_a003 | 1 | False | [1] | 0.5 | 0.0 | 0.2222 | 1.0 | 0.60138 |
| aeroengqa_mh_a004 | 1 | False | [1] | 0.5 | 0.0 | 1.0 | 1.0 | 0.9125 |
| aeroengqa_mh_a005 | 1 | False | [1, 2] | 1.0 | 0.0 | 0.5 | 1.0 | 0.8 |
| aeroengqa_mh_a006 | 1 | False | [2] | 0.5 | 0.0 | 0.9091 | 1.0 | 0.87614 |
| aeroengqa_mh_a007 | 1 | False | [1, 2] | 1.0 | 0.0 | 1.0 | 1.0 | 1.0 |
| aeroengqa_mh_a008 | 1 | False | [1, 2] | 1.0 | 0.0 | 1.0 | 1.0 | 1.0 |
| aeroengqa_mh_a009 | 1 | False | [2] | 0.5 | 0.0 | 0.5882 | 1.0 | 0.74778 |
| aeroengqa_mh_a010 | 1 | True | [1, 2] | 0.0 | 0.0 | 0.0 | 1.0 | 0.25 |
| aeroengqa_mh_a011 | 1 | False | [2] | 0.5 | 0.0 | 1.0 | 1.0 | 0.9125 |
| aeroengqa_mh_a012 | 1 | False | [2] | 0.5 | 0.0 | 0.1333 | 1.0 | 0.56582 |
| aeroengqa_mh_a013 | 1 | False | [1, 2] | 1.0 | 0.0 | 0.4 | 1.0 | 0.76 |
| aeroengqa_mh_a014 | 1 | False | [1, 2] | 1.0 | 0.0 | 0.1667 | 1.0 | 0.66668 |
| aeroengqa_mh_a015 | 1 | False | [2] | 0.5 | 0.0 | 0.5 | 1.0 | 0.7125 |
| aeroengqa_mh_a016 | 1 | False | [1, 2] | 1.0 | 0.0 | 0.4828 | 1.0 | 0.79312 |
| aeroengqa_mh_a017 | 1 | False | [1, 2] | 1.0 | 0.0 | 0.3478 | 1.0 | 0.73912 |
| aeroengqa_mh_a018 | 1 | False | [1] | 0.5 | 0.0 | 0.8 | 1.0 | 0.8325 |
| aeroengqa_mh_a019 | 1 | False | [1, 2] | 1.0 | 0.0 | 0.8 | 1.0 | 0.92 |
| aeroengqa_mh_a020 | 1 | False | [2] | 0.5 | 0.0 | 0.0 | 1.0 | 0.5125 |
| aeroengqa_mh_u001 | 1 | True | [1, 2] | 1.0 | 0.0 | N/A | 1.0 | 1.0 |
| aeroengqa_mh_u002 | 1 | True | [2] | 1.0 | 0.0 | N/A | 1.0 | 1.0 |
| aeroengqa_mh_u003 | 1 | False | [2] | 1.0 | 0.0 | N/A | 1.0 | 0.7 |
| aeroengqa_mh_u004 | 1 | True | [1, 2] | 1.0 | 0.0 | N/A | 1.0 | 1.0 |
| aeroengqa_mh_u005 | 1 | True | [2] | 1.0 | 0.0 | N/A | 1.0 | 1.0 |
| aeroengqa_mh_u006 | 1 | True | [1, 2] | 1.0 | 0.0 | N/A | 1.0 | 1.0 |
| aeroengqa_mh_u007 | 1 | True | [1, 2] | 1.0 | 0.0 | N/A | 1.0 | 1.0 |
| aeroengqa_mh_u008 | 1 | True | [2] | 1.0 | 0.0 | N/A | 1.0 | 1.0 |
| aeroengqa_mh_u009 | 1 | True | [1, 2] | 1.0 | 0.0 | N/A | 1.0 | 1.0 |
| aeroengqa_mh_u010 | 1 | True | [1, 2] | 1.0 | 0.0 | N/A | 1.0 | 1.0 |
| aeroengqa_mh_u011 | 1 | True | [1, 2] | 1.0 | 0.0 | N/A | 1.0 | 1.0 |
| aeroengqa_mh_u012 | 1 | True | [1, 2] | 1.0 | 0.0 | N/A | 1.0 | 1.0 |
| aeroengqa_mh_u013 | 1 | True | [1] | 1.0 | 0.0 | N/A | 1.0 | 1.0 |
| aeroengqa_mh_u014 | 1 | True | [1, 2] | 1.0 | 0.0 | N/A | 1.0 | 1.0 |
| aeroengqa_mh_u015 | 1 | True | [1, 2] | 1.0 | 0.0 | N/A | 1.0 | 1.0 |
| aeroengqa_mh_u016 | 1 | False | [1] | 1.0 | 0.0 | N/A | 1.0 | 0.7 |
| aeroengqa_mh_u017 | 1 | True | [1, 2] | 1.0 | 0.0 | N/A | 1.0 | 1.0 |
| aeroengqa_mh_u018 | 1 | True | [1, 2] | 1.0 | 0.0 | N/A | 1.0 | 1.0 |
| aeroengqa_mh_u019 | 1 | True | [1, 2] | 1.0 | 0.0 | N/A | 1.0 | 1.0 |
| aeroengqa_mh_u020 | 1 | True | [1, 2] | 1.0 | 0.0 | N/A | 1.0 | 1.0 |
| aeroengqa_sh_a001 | 1 | False | [1] | 1.0 | 0.0 | 1.0 | 1.0 | 1.0 |
| aeroengqa_sh_a002 | 1 | False | [1] | 1.0 | 0.0 | 0.8421 | 1.0 | 0.93684 |
| aeroengqa_sh_a003 | 1 | False | [1] | 1.0 | 0.0 | 1.0 | 1.0 | 1.0 |
| aeroengqa_sh_a004 | 1 | True | [1] | 0.0 | 0.0 | 0.0 | 1.0 | 0.25 |
| aeroengqa_sh_a005 | 1 | True | [1] | 0.0 | 0.0 | 0.0 | 1.0 | 0.25 |
| aeroengqa_sh_a006 | 1 | False | [1] | 1.0 | 0.0 | 1.0 | 1.0 | 1.0 |
| aeroengqa_sh_a007 | 1 | False | [1] | 1.0 | 0.0 | 0.8421 | 1.0 | 0.93684 |
| aeroengqa_sh_a008 | 1 | False | [1] | 1.0 | 0.0 | 0.8333 | 1.0 | 0.93332 |
| aeroengqa_sh_a009 | 1 | False | [1] | 1.0 | 0.0 | 0.3636 | 1.0 | 0.74544 |
| aeroengqa_sh_a010 | 1 | False | [1] | 1.0 | 0.0 | 0.9524 | 1.0 | 0.98096 |
| aeroengqa_sh_a011 | 1 | False | [1] | 1.0 | 0.0 | 0.6667 | 1.0 | 0.86668 |
| aeroengqa_sh_a012 | 1 | False | [1] | 1.0 | 0.0 | 0.8571 | 1.0 | 0.94284 |
| aeroengqa_sh_a013 | 1 | False | [1] | 1.0 | 0.0 | 1.0 | 1.0 | 1.0 |
| aeroengqa_sh_a014 | 1 | False | [1] | 1.0 | 0.0 | 0.8889 | 1.0 | 0.95556 |
| aeroengqa_sh_a015 | 1 | False | [1] | 1.0 | 0.0 | 0.8182 | 1.0 | 0.92728 |
| aeroengqa_sh_a016 | 1 | False | [1] | 1.0 | 0.0 | 0.6667 | 1.0 | 0.86668 |
| aeroengqa_sh_a017 | 1 | False | [1] | 1.0 | 0.0 | 0.6957 | 1.0 | 0.87828 |
| aeroengqa_sh_a018 | 1 | False | [1] | 1.0 | 0.0 | 0.5556 | 1.0 | 0.82224 |
| aeroengqa_sh_a019 | 1 | False | [1] | 1.0 | 0.0 | 0.1818 | 1.0 | 0.67272 |
| aeroengqa_sh_a020 | 1 | False | [1] | 1.0 | 0.0 | 1.0 | 1.0 | 1.0 |
| aeroengqa_sh_u001 | 1 | True | [1] | 1.0 | 0.0 | N/A | 1.0 | 1.0 |
| aeroengqa_sh_u002 | 1 | True | [1] | 1.0 | 0.0 | N/A | 1.0 | 1.0 |
| aeroengqa_sh_u003 | 1 | True | [1] | 1.0 | 0.0 | N/A | 1.0 | 1.0 |
| aeroengqa_sh_u004 | 1 | True | [1] | 1.0 | 0.0 | N/A | 1.0 | 1.0 |
| aeroengqa_sh_u005 | 1 | True | [1] | 1.0 | 0.0 | N/A | 1.0 | 1.0 |
| aeroengqa_sh_u006 | 1 | True | [1] | 1.0 | 0.0 | N/A | 0.0 | 0.6 |
| aeroengqa_sh_u007 | 1 | True | [1] | 1.0 | 0.0 | N/A | 1.0 | 1.0 |
| aeroengqa_sh_u008 | 1 | True | [1] | 1.0 | 0.0 | N/A | 0.0 | 0.6 |
| aeroengqa_sh_u009 | 1 | True | [1] | 1.0 | 0.0 | N/A | 1.0 | 1.0 |
| aeroengqa_sh_u010 | 1 | True | [1] | 1.0 | 0.0 | N/A | 1.0 | 1.0 |
| aeroengqa_sh_u011 | 1 | True | [1] | 1.0 | 0.0 | N/A | 1.0 | 1.0 |
| aeroengqa_sh_u012 | 1 | True | [1] | 1.0 | 0.0 | N/A | 1.0 | 1.0 |
| aeroengqa_sh_u013 | 1 | False | [1] | 1.0 | 0.0 | N/A | 1.0 | 0.7 |
| aeroengqa_sh_u014 | 1 | True | [1] | 1.0 | 0.0 | N/A | 1.0 | 1.0 |
| aeroengqa_sh_u015 | 1 | True | [1] | 1.0 | 0.0 | N/A | 1.0 | 1.0 |
| aeroengqa_sh_u016 | 1 | True | [1] | 1.0 | 0.0 | N/A | 1.0 | 1.0 |
| aeroengqa_sh_u017 | 1 | True | [1] | 1.0 | 0.0 | N/A | 1.0 | 1.0 |
| aeroengqa_sh_u018 | 1 | True | [1] | 1.0 | 0.0 | N/A | 1.0 | 1.0 |
| aeroengqa_sh_u019 | 1 | True | [1] | 1.0 | 0.0 | N/A | 1.0 | 1.0 |
| aeroengqa_sh_u020 | 1 | True | [1] | 1.0 | 0.0 | N/A | 1.0 | 1.0 |
