# qa_grounded 结果汇总（provider=stub, model=n/a, seed=0）

## ValidityGate 分布（先看 gate，再看子分）

- 任务总数: 80
- gate 通过: 80
- gate 失败: 0（直接 0 分）
- 作废（不计分）: 0
- gate 失败原因分布: 无

## 拒答层（refusal）

- 应拒答 40 题: 正确拒答 0（拒答正确率 0.0000）
- 应回答 40 题: 误拒答 0（误拒率 0.0000）

## 证据层（evidence support / fabrication）

- evidence_support 均值: 0.8750
- 捏造引用题数: 0/80（fabrication_rate>0）

## 客观层（requirements，仅应回答题）

- 满分 0/40；含部分分的均值 0.0365（归一化精确/数值容差=1，其余 token F1 部分分）

## 区分层（distinction：BASIS 结构声明）

- 合法声明率: 1.0000（80 题）
- 口径：BASIS ∈ report/computed/inferred；数据集无参考 basis 标签，逐字核验仅作诊断不进分（见任务 YAML grader 注释）

## 每题明细

| task | gate | refused | cite | support | fab | req | dist | score |
| --- | --- | --- | --- | --- | --- | --- | --- | --- |
| aeroengqa_mh_a001 | 1 | False | [1] | 0.5 | 0.0 | 0.0 | 1.0 | 0.5125 |
| aeroengqa_mh_a002 | 1 | False | [1] | 0.5 | 0.0 | 0.0 | 1.0 | 0.5125 |
| aeroengqa_mh_a003 | 1 | False | [1] | 0.5 | 0.0 | 0.0 | 1.0 | 0.5125 |
| aeroengqa_mh_a004 | 1 | False | [1] | 0.5 | 0.0 | 0.0 | 1.0 | 0.5125 |
| aeroengqa_mh_a005 | 1 | False | [1] | 0.5 | 0.0 | 0.1429 | 1.0 | 0.56966 |
| aeroengqa_mh_a006 | 1 | False | [1] | 0.5 | 0.0 | 0.0 | 1.0 | 0.5125 |
| aeroengqa_mh_a007 | 1 | False | [1] | 0.5 | 0.0 | 0.0 | 1.0 | 0.5125 |
| aeroengqa_mh_a008 | 1 | False | [1] | 0.5 | 0.0 | 0.0 | 1.0 | 0.5125 |
| aeroengqa_mh_a009 | 1 | False | [1] | 0.5 | 0.0 | 0.0 | 1.0 | 0.5125 |
| aeroengqa_mh_a010 | 1 | False | [1] | 0.5 | 0.0 | 0.0 | 1.0 | 0.5125 |
| aeroengqa_mh_a011 | 1 | False | [1] | 0.5 | 0.0 | 0.0 | 1.0 | 0.5125 |
| aeroengqa_mh_a012 | 1 | False | [1] | 0.5 | 0.0 | 0.0 | 1.0 | 0.5125 |
| aeroengqa_mh_a013 | 1 | False | [1] | 0.5 | 0.0 | 0.0909 | 1.0 | 0.54886 |
| aeroengqa_mh_a014 | 1 | False | [1] | 0.5 | 0.0 | 0.5455 | 1.0 | 0.7307 |
| aeroengqa_mh_a015 | 1 | False | [1] | 0.5 | 0.0 | 0.5 | 1.0 | 0.7125 |
| aeroengqa_mh_a016 | 1 | False | [1] | 0.5 | 0.0 | 0.0 | 1.0 | 0.5125 |
| aeroengqa_mh_a017 | 1 | False | [1] | 0.5 | 0.0 | 0.0 | 1.0 | 0.5125 |
| aeroengqa_mh_a018 | 1 | False | [1] | 0.5 | 0.0 | 0.0 | 1.0 | 0.5125 |
| aeroengqa_mh_a019 | 1 | False | [1] | 0.5 | 0.0 | 0.0 | 1.0 | 0.5125 |
| aeroengqa_mh_a020 | 1 | False | [1] | 0.5 | 0.0 | 0.0 | 1.0 | 0.5125 |
| aeroengqa_mh_u001 | 1 | False | [1] | 1.0 | 0.0 | N/A | 1.0 | 0.7 |
| aeroengqa_mh_u002 | 1 | False | [1] | 1.0 | 0.0 | N/A | 1.0 | 0.7 |
| aeroengqa_mh_u003 | 1 | False | [1] | 1.0 | 0.0 | N/A | 1.0 | 0.7 |
| aeroengqa_mh_u004 | 1 | False | [1] | 1.0 | 0.0 | N/A | 1.0 | 0.7 |
| aeroengqa_mh_u005 | 1 | False | [1] | 1.0 | 0.0 | N/A | 1.0 | 0.7 |
| aeroengqa_mh_u006 | 1 | False | [1] | 1.0 | 0.0 | N/A | 1.0 | 0.7 |
| aeroengqa_mh_u007 | 1 | False | [1] | 1.0 | 0.0 | N/A | 1.0 | 0.7 |
| aeroengqa_mh_u008 | 1 | False | [1] | 1.0 | 0.0 | N/A | 1.0 | 0.7 |
| aeroengqa_mh_u009 | 1 | False | [1] | 1.0 | 0.0 | N/A | 1.0 | 0.7 |
| aeroengqa_mh_u010 | 1 | False | [1] | 1.0 | 0.0 | N/A | 1.0 | 0.7 |
| aeroengqa_mh_u011 | 1 | False | [1] | 1.0 | 0.0 | N/A | 1.0 | 0.7 |
| aeroengqa_mh_u012 | 1 | False | [1] | 1.0 | 0.0 | N/A | 1.0 | 0.7 |
| aeroengqa_mh_u013 | 1 | False | [1] | 1.0 | 0.0 | N/A | 1.0 | 0.7 |
| aeroengqa_mh_u014 | 1 | False | [1] | 1.0 | 0.0 | N/A | 1.0 | 0.7 |
| aeroengqa_mh_u015 | 1 | False | [1] | 1.0 | 0.0 | N/A | 1.0 | 0.7 |
| aeroengqa_mh_u016 | 1 | False | [1] | 1.0 | 0.0 | N/A | 1.0 | 0.7 |
| aeroengqa_mh_u017 | 1 | False | [1] | 1.0 | 0.0 | N/A | 1.0 | 0.7 |
| aeroengqa_mh_u018 | 1 | False | [1] | 1.0 | 0.0 | N/A | 1.0 | 0.7 |
| aeroengqa_mh_u019 | 1 | False | [1] | 1.0 | 0.0 | N/A | 1.0 | 0.7 |
| aeroengqa_mh_u020 | 1 | False | [1] | 1.0 | 0.0 | N/A | 1.0 | 0.7 |
| aeroengqa_sh_a001 | 1 | False | [1] | 1.0 | 0.0 | 0.0 | 1.0 | 0.6 |
| aeroengqa_sh_a002 | 1 | False | [1] | 1.0 | 0.0 | 0.0 | 1.0 | 0.6 |
| aeroengqa_sh_a003 | 1 | False | [1] | 1.0 | 0.0 | 0.0 | 1.0 | 0.6 |
| aeroengqa_sh_a004 | 1 | False | [1] | 1.0 | 0.0 | 0.0 | 1.0 | 0.6 |
| aeroengqa_sh_a005 | 1 | False | [1] | 1.0 | 0.0 | 0.0 | 1.0 | 0.6 |
| aeroengqa_sh_a006 | 1 | False | [1] | 1.0 | 0.0 | 0.0 | 1.0 | 0.6 |
| aeroengqa_sh_a007 | 1 | False | [1] | 1.0 | 0.0 | 0.0 | 1.0 | 0.6 |
| aeroengqa_sh_a008 | 1 | False | [1] | 1.0 | 0.0 | 0.0 | 1.0 | 0.6 |
| aeroengqa_sh_a009 | 1 | False | [1] | 1.0 | 0.0 | 0.0 | 1.0 | 0.6 |
| aeroengqa_sh_a010 | 1 | False | [1] | 1.0 | 0.0 | 0.0 | 1.0 | 0.6 |
| aeroengqa_sh_a011 | 1 | False | [1] | 1.0 | 0.0 | 0.0 | 1.0 | 0.6 |
| aeroengqa_sh_a012 | 1 | False | [1] | 1.0 | 0.0 | 0.0 | 1.0 | 0.6 |
| aeroengqa_sh_a013 | 1 | False | [1] | 1.0 | 0.0 | 0.0 | 1.0 | 0.6 |
| aeroengqa_sh_a014 | 1 | False | [1] | 1.0 | 0.0 | 0.0 | 1.0 | 0.6 |
| aeroengqa_sh_a015 | 1 | False | [1] | 1.0 | 0.0 | 0.0 | 1.0 | 0.6 |
| aeroengqa_sh_a016 | 1 | False | [1] | 1.0 | 0.0 | 0.0 | 1.0 | 0.6 |
| aeroengqa_sh_a017 | 1 | False | [1] | 1.0 | 0.0 | 0.0 | 1.0 | 0.6 |
| aeroengqa_sh_a018 | 1 | False | [1] | 1.0 | 0.0 | 0.1818 | 1.0 | 0.67272 |
| aeroengqa_sh_a019 | 1 | False | [1] | 1.0 | 0.0 | 0.0 | 1.0 | 0.6 |
| aeroengqa_sh_a020 | 1 | False | [1] | 1.0 | 0.0 | 0.0 | 1.0 | 0.6 |
| aeroengqa_sh_u001 | 1 | False | [1] | 1.0 | 0.0 | N/A | 1.0 | 0.7 |
| aeroengqa_sh_u002 | 1 | False | [1] | 1.0 | 0.0 | N/A | 1.0 | 0.7 |
| aeroengqa_sh_u003 | 1 | False | [1] | 1.0 | 0.0 | N/A | 1.0 | 0.7 |
| aeroengqa_sh_u004 | 1 | False | [1] | 1.0 | 0.0 | N/A | 1.0 | 0.7 |
| aeroengqa_sh_u005 | 1 | False | [1] | 1.0 | 0.0 | N/A | 1.0 | 0.7 |
| aeroengqa_sh_u006 | 1 | False | [1] | 1.0 | 0.0 | N/A | 1.0 | 0.7 |
| aeroengqa_sh_u007 | 1 | False | [1] | 1.0 | 0.0 | N/A | 1.0 | 0.7 |
| aeroengqa_sh_u008 | 1 | False | [1] | 1.0 | 0.0 | N/A | 1.0 | 0.7 |
| aeroengqa_sh_u009 | 1 | False | [1] | 1.0 | 0.0 | N/A | 1.0 | 0.7 |
| aeroengqa_sh_u010 | 1 | False | [1] | 1.0 | 0.0 | N/A | 1.0 | 0.7 |
| aeroengqa_sh_u011 | 1 | False | [1] | 1.0 | 0.0 | N/A | 1.0 | 0.7 |
| aeroengqa_sh_u012 | 1 | False | [1] | 1.0 | 0.0 | N/A | 1.0 | 0.7 |
| aeroengqa_sh_u013 | 1 | False | [1] | 1.0 | 0.0 | N/A | 1.0 | 0.7 |
| aeroengqa_sh_u014 | 1 | False | [1] | 1.0 | 0.0 | N/A | 1.0 | 0.7 |
| aeroengqa_sh_u015 | 1 | False | [1] | 1.0 | 0.0 | N/A | 1.0 | 0.7 |
| aeroengqa_sh_u016 | 1 | False | [1] | 1.0 | 0.0 | N/A | 1.0 | 0.7 |
| aeroengqa_sh_u017 | 1 | False | [1] | 1.0 | 0.0 | N/A | 1.0 | 0.7 |
| aeroengqa_sh_u018 | 1 | False | [1] | 1.0 | 0.0 | N/A | 1.0 | 0.7 |
| aeroengqa_sh_u019 | 1 | False | [1] | 1.0 | 0.0 | N/A | 1.0 | 0.7 |
| aeroengqa_sh_u020 | 1 | False | [1] | 1.0 | 0.0 | N/A | 1.0 | 0.7 |
