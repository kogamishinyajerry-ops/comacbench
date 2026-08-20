# qa_grounded 结果汇总（provider=minimax, model=MiniMax-M3, seed=0）

## ValidityGate 分布（先看 gate，再看子分）

- 任务总数: 80
- gate 通过: 80
- gate 失败: 0（直接 0 分）
- 作废（不计分）: 0
- gate 失败原因分布: 无

## 拒答层（refusal）

- 应拒答 40 题: 正确拒答 35（拒答正确率 0.8750）
- 应回答 40 题: 误拒答 1（误拒率 0.0250）

## 证据层（evidence support / fabrication）

- evidence_support 均值: 0.9375
- 捏造引用题数: 0/80（fabrication_rate>0）

## 客观层（requirements，仅应回答题）

- 满分 10/40；含部分分的均值 0.5851（归一化精确/数值容差=1，其余 token F1 部分分）

## 区分层（distinction：BASIS 结构声明）

- 合法声明率: 1.0000（80 题）
- 口径：BASIS ∈ report/computed/inferred；数据集无参考 basis 标签，逐字核验仅作诊断不进分（见任务 YAML grader 注释）

## 每题明细

| task | gate | refused | cite | support | fab | req | dist | score |
| --- | --- | --- | --- | --- | --- | --- | --- | --- |
| aeroengqa_mh_a001 | 1 | False | [1, 2] | 1.0 | 0.0 | 0.1538 | 1.0 | 0.66152 |
| aeroengqa_mh_a002 | 1 | False | [1, 2] | 1.0 | 0.0 | 1.0 | 1.0 | 1.0 |
| aeroengqa_mh_a003 | 1 | False | [1] | 0.5 | 0.0 | 0.2609 | 1.0 | 0.61686 |
| aeroengqa_mh_a004 | 1 | False | [1] | 0.5 | 0.0 | 0.6667 | 1.0 | 0.77918 |
| aeroengqa_mh_a005 | 1 | False | [1, 2] | 1.0 | 0.0 | 1.0 | 1.0 | 1.0 |
| aeroengqa_mh_a006 | 1 | False | [1, 2] | 1.0 | 0.0 | 0.6897 | 1.0 | 0.87588 |
| aeroengqa_mh_a007 | 1 | False | [1, 2] | 1.0 | 0.0 | 1.0 | 1.0 | 1.0 |
| aeroengqa_mh_a008 | 1 | False | [1] | 0.5 | 0.0 | 1.0 | 1.0 | 0.9125 |
| aeroengqa_mh_a009 | 1 | False | [2] | 0.5 | 0.0 | 0.6111 | 1.0 | 0.75694 |
| aeroengqa_mh_a010 | 1 | False | [1, 2] | 1.0 | 0.0 | 0.36 | 1.0 | 0.744 |
| aeroengqa_mh_a011 | 1 | False | [2] | 0.5 | 0.0 | 1.0 | 1.0 | 0.9125 |
| aeroengqa_mh_a012 | 1 | False | [2] | 0.5 | 0.0 | 0.2609 | 1.0 | 0.61686 |
| aeroengqa_mh_a013 | 1 | False | [1, 2] | 1.0 | 0.0 | 0.35 | 1.0 | 0.74 |
| aeroengqa_mh_a014 | 1 | False | [1, 2] | 1.0 | 0.0 | 0.125 | 1.0 | 0.65 |
| aeroengqa_mh_a015 | 1 | False | [1, 2] | 1.0 | 0.0 | 0.4 | 1.0 | 0.76 |
| aeroengqa_mh_a016 | 1 | False | [1, 2] | 1.0 | 0.0 | 0.2857 | 1.0 | 0.71428 |
| aeroengqa_mh_a017 | 1 | False | [1, 2] | 1.0 | 0.0 | 0.4444 | 1.0 | 0.77776 |
| aeroengqa_mh_a018 | 1 | False | [1, 2] | 1.0 | 0.0 | 0.8 | 1.0 | 0.92 |
| aeroengqa_mh_a019 | 1 | False | [2] | 0.5 | 0.0 | 0.5333 | 1.0 | 0.72582 |
| aeroengqa_mh_a020 | 1 | False | [2] | 0.5 | 0.0 | 0.0 | 1.0 | 0.5125 |
| aeroengqa_mh_u001 | 1 | True | [1, 2] | 1.0 | 0.0 | N/A | 1.0 | 1.0 |
| aeroengqa_mh_u002 | 1 | True | [2] | 1.0 | 0.0 | N/A | 1.0 | 1.0 |
| aeroengqa_mh_u003 | 1 | True | [2] | 1.0 | 0.0 | N/A | 1.0 | 1.0 |
| aeroengqa_mh_u004 | 1 | True | [1, 2] | 1.0 | 0.0 | N/A | 1.0 | 1.0 |
| aeroengqa_mh_u005 | 1 | True | [1, 2] | 1.0 | 0.0 | N/A | 1.0 | 1.0 |
| aeroengqa_mh_u006 | 1 | True | [1, 2] | 1.0 | 0.0 | N/A | 1.0 | 1.0 |
| aeroengqa_mh_u007 | 1 | True | [1, 2] | 1.0 | 0.0 | N/A | 1.0 | 1.0 |
| aeroengqa_mh_u008 | 1 | False | [2] | 1.0 | 0.0 | N/A | 1.0 | 0.7 |
| aeroengqa_mh_u009 | 1 | True | [1, 2] | 1.0 | 0.0 | N/A | 1.0 | 1.0 |
| aeroengqa_mh_u010 | 1 | True | [1, 2] | 1.0 | 0.0 | N/A | 1.0 | 1.0 |
| aeroengqa_mh_u011 | 1 | True | [1, 2] | 1.0 | 0.0 | N/A | 1.0 | 1.0 |
| aeroengqa_mh_u012 | 1 | True | [1, 2] | 1.0 | 0.0 | N/A | 1.0 | 1.0 |
| aeroengqa_mh_u013 | 1 | False | [1] | 1.0 | 0.0 | N/A | 1.0 | 0.7 |
| aeroengqa_mh_u014 | 1 | True | [1, 2] | 1.0 | 0.0 | N/A | 1.0 | 1.0 |
| aeroengqa_mh_u015 | 1 | True | [1, 2] | 1.0 | 0.0 | N/A | 1.0 | 1.0 |
| aeroengqa_mh_u016 | 1 | True | [1, 2] | 1.0 | 0.0 | N/A | 1.0 | 1.0 |
| aeroengqa_mh_u017 | 1 | True | [1, 2] | 1.0 | 0.0 | N/A | 1.0 | 1.0 |
| aeroengqa_mh_u018 | 1 | True | [1, 2] | 1.0 | 0.0 | N/A | 1.0 | 1.0 |
| aeroengqa_mh_u019 | 1 | True | [1, 2] | 1.0 | 0.0 | N/A | 1.0 | 1.0 |
| aeroengqa_mh_u020 | 1 | True | [1, 2] | 1.0 | 0.0 | N/A | 1.0 | 1.0 |
| aeroengqa_sh_a001 | 1 | False | [1] | 1.0 | 0.0 | 1.0 | 1.0 | 1.0 |
| aeroengqa_sh_a002 | 1 | False | [1] | 1.0 | 0.0 | 0.72 | 1.0 | 0.888 |
| aeroengqa_sh_a003 | 1 | False | [1] | 1.0 | 0.0 | 1.0 | 1.0 | 1.0 |
| aeroengqa_sh_a004 | 1 | False | [1] | 1.0 | 0.0 | 1.0 | 1.0 | 1.0 |
| aeroengqa_sh_a005 | 1 | True | [1] | 0.0 | 0.0 | 0.0 | 1.0 | 0.25 |
| aeroengqa_sh_a006 | 1 | False | [1] | 1.0 | 0.0 | 1.0 | 1.0 | 1.0 |
| aeroengqa_sh_a007 | 1 | False | [1] | 1.0 | 0.0 | 0.5926 | 1.0 | 0.83704 |
| aeroengqa_sh_a008 | 1 | False | [1] | 1.0 | 0.0 | 0.5714 | 1.0 | 0.82856 |
| aeroengqa_sh_a009 | 1 | False | [1] | 1.0 | 0.0 | 0.08 | 1.0 | 0.632 |
| aeroengqa_sh_a010 | 1 | False | [1] | 1.0 | 0.0 | 0.9524 | 1.0 | 0.98096 |
| aeroengqa_sh_a011 | 1 | False | [1] | 1.0 | 0.0 | 0.5263 | 1.0 | 0.81052 |
| aeroengqa_sh_a012 | 1 | False | [1] | 1.0 | 0.0 | 0.75 | 1.0 | 0.9 |
| aeroengqa_sh_a013 | 1 | False | [1] | 1.0 | 0.0 | 1.0 | 1.0 | 1.0 |
| aeroengqa_sh_a014 | 1 | False | [1] | 1.0 | 0.0 | 0.7619 | 1.0 | 0.90476 |
| aeroengqa_sh_a015 | 1 | False | [1] | 1.0 | 0.0 | 0.6341 | 1.0 | 0.85364 |
| aeroengqa_sh_a016 | 1 | False | [1] | 1.0 | 0.0 | 0.5 | 1.0 | 0.8 |
| aeroengqa_sh_a017 | 1 | False | [1] | 1.0 | 0.0 | 0.45 | 1.0 | 0.78 |
| aeroengqa_sh_a018 | 1 | False | [1] | 1.0 | 0.0 | 0.4286 | 1.0 | 0.77144 |
| aeroengqa_sh_a019 | 1 | False | [1] | 1.0 | 0.0 | 0.1333 | 1.0 | 0.65332 |
| aeroengqa_sh_a020 | 1 | False | [1] | 1.0 | 0.0 | 0.3636 | 1.0 | 0.74544 |
| aeroengqa_sh_u001 | 1 | True | [1] | 1.0 | 0.0 | N/A | 1.0 | 1.0 |
| aeroengqa_sh_u002 | 1 | True | [1] | 1.0 | 0.0 | N/A | 1.0 | 1.0 |
| aeroengqa_sh_u003 | 1 | True | [1] | 1.0 | 0.0 | N/A | 1.0 | 1.0 |
| aeroengqa_sh_u004 | 1 | True | [1] | 1.0 | 0.0 | N/A | 1.0 | 1.0 |
| aeroengqa_sh_u005 | 1 | True | [1] | 1.0 | 0.0 | N/A | 1.0 | 1.0 |
| aeroengqa_sh_u006 | 1 | False | [1] | 1.0 | 0.0 | N/A | 1.0 | 0.7 |
| aeroengqa_sh_u007 | 1 | True | [1] | 1.0 | 0.0 | N/A | 1.0 | 1.0 |
| aeroengqa_sh_u008 | 1 | True | [1] | 1.0 | 0.0 | N/A | 1.0 | 1.0 |
| aeroengqa_sh_u009 | 1 | True | [1] | 1.0 | 0.0 | N/A | 1.0 | 1.0 |
| aeroengqa_sh_u010 | 1 | True | [1] | 1.0 | 0.0 | N/A | 1.0 | 1.0 |
| aeroengqa_sh_u011 | 1 | True | [1] | 1.0 | 0.0 | N/A | 1.0 | 1.0 |
| aeroengqa_sh_u012 | 1 | False | [1] | 1.0 | 0.0 | N/A | 1.0 | 0.7 |
| aeroengqa_sh_u013 | 1 | True | [1] | 1.0 | 0.0 | N/A | 1.0 | 1.0 |
| aeroengqa_sh_u014 | 1 | True | [1] | 1.0 | 0.0 | N/A | 1.0 | 1.0 |
| aeroengqa_sh_u015 | 1 | True | [1] | 1.0 | 0.0 | N/A | 1.0 | 1.0 |
| aeroengqa_sh_u016 | 1 | True | [1] | 1.0 | 0.0 | N/A | 1.0 | 1.0 |
| aeroengqa_sh_u017 | 1 | False | [1] | 1.0 | 0.0 | N/A | 1.0 | 0.7 |
| aeroengqa_sh_u018 | 1 | True | [1] | 1.0 | 0.0 | N/A | 1.0 | 1.0 |
| aeroengqa_sh_u019 | 1 | True | [1] | 1.0 | 0.0 | N/A | 1.0 | 1.0 |
| aeroengqa_sh_u020 | 1 | True | [1] | 1.0 | 0.0 | N/A | 1.0 | 1.0 |
