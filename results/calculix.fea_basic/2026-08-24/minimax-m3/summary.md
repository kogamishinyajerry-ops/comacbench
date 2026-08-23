# simulation_agent 结果汇总（provider=minimax, model=MiniMax-M3, seed=0）

## ValidityGate 分布（先看 gate，再看子分）

- 任务总数: 21
- gate 通过: 7
- gate 失败: 14（直接 0 分）
- 作废: 0
- gate 失败原因分布: {'simulation_failed': 7, 'code_not_executable': 6, 'timeout': 1}

## physics（NMSE 阈值分）分布（n=21）

- 1.0: 3
- 0.5: 0
- 0.0: 18

## 每任务明细

| task | gate | nmse | nmse_score | score | 关键信息 |
| --- | --- | --- | --- | --- | --- |
| ccx_bk_01 | 0 | - | 0.0 | 0.0 | missing=exec_fail |
| ccx_bk_02 | 0 | - | 0.0 | 0.0 |  |
| ccx_bk_03 | 0 | - | 0.0 | 0.0 | missing=exec_fail |
| ccx_bk_04 | 0 | - | 0.0 | 0.0 | missing=exec_fail |
| ccx_cb_01 | 0 | - | 0.0 | 0.0 | missing=exec_fail |
| ccx_cb_02 | 0 | - | 0.0 | 0.0 | missing=exec_fail |
| ccx_cb_03 | 1 | - | 0.0 | 0.5 | missing=exec_fail |
| ccx_cb_04 | 0 | - | 0.0 | 0.0 | missing=exec_fail |
| ccx_cb_05 | 0 | - | 0.0 | 0.0 | missing=exec_fail |
| ccx_lb_01 | 0 | - | 0.0 | 0.0 |  |
| ccx_lb_02 | 0 | - | 0.0 | 0.0 | missing=exec_fail |
| ccx_lb_03 | 0 | - | 0.0 | 0.0 | missing=exec_fail |
| ccx_lb_04 | 1 | - | 0.0 | 0.5 | missing=exec_fail |
| ccx_md_01 | 1 | - | 1.0 | 1.0 | missing=exec_fail |
| ccx_md_02 | 1 | - | 1.0 | 1.0 | missing=exec_fail |
| ccx_md_03 | 0 | - | 0.0 | 0.0 |  |
| ccx_md_04 | 1 | - | 1.0 | 1.0 | missing=exec_fail |
| ccx_ssb_01 | 1 | - | 0.0 | 0.5 | missing=exec_fail |
| ccx_ssb_02 | 0 | - | 0.0 | 0.0 | missing=exec_fail |
| ccx_ssb_03 | 0 | - | 0.0 | 0.0 | missing=exec_fail |
| ccx_ssb_04 | 1 | - | 0.0 | 0.5 | missing=exec_fail |
