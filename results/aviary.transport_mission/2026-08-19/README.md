# aviary.transport_mission 2026-08-19 运行索引（M3）

> 落点约定：`results/<registry_id>/<date>/<provider>/`。
> `assets_revision = aviary-mission@selfbuilt-2026-08-19+aviary1.0.1`（自建 8 任务，
> 参考预计算锁定，rel_tol 1%）。

| 子目录 | provider/model | gate | 任务均分 | 关键观察 |
| --- | --- | --- | --- | --- |
| `stub/` | stub | 0/8 | 0 | missing_output ×8（`pass` 不产 result.json）|
| `oracle/` | gold 脚本 | 8/8 | **1.000** | 判分管线全验证（数值/键完备/修复题精确匹配）|
| `minimax-m3/` | MiniMax-M3 | 2/8 | 0.250 | 通过题全满分（含模型修复题）；失败=幻觉 API（老模块名/虚构机型路径）|
| `glm-4.6/` | GLM-4.6 | **3/8** | **0.375** | 3 个单任务分析全满分；多任务/修复未成（脚本复杂度敏感）；1 sandbox_escape |

- 题面 API 提示边界：环境约束（无 pyoptsparse）/`mach_cruise` 键名/`mission:*` 输出变量
  属接口事实已披露；模型幻觉老 API 计为被测失败（PROVENANCE「题面 API 提示的边界」）；
- 复现：`.venv/bin/python -m runners.simulation_agent --tasks tasks/aviary.transport_mission
  --out results/aviary.transport_mission/2026-08-19/<provider> --provider <p> --seed 0`。
