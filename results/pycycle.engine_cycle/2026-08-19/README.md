# pycycle.engine_cycle 2026-08-19 运行索引（batch-2）

> 落点约定：`results/<registry_id>/<date>/<provider>/`。
> `assets_revision = pycycle-pack@selfbuilt-2026-08-19+ompycycle_src`（自建 7 任务，
> vendored 官方 turbojet 引擎，SL 设计点收敛域）。

| 子目录 | provider/model | gate | 任务均分 | 关键观察 |
| --- | --- | --- | --- | --- |
| `stub/` | stub | 0/7 | 0 | missing_output ×7 |
| `oracle/` | vendored 引擎 gold | **7/7** | **1.000** | 判分管线全验证（含修复题精确匹配、OPR 扫描键名对齐）|
| `minimax-m3/` | MiniMax-M3 | 0/7 | 0 | 7 code_not_executable（幻觉 pycycle API 如 `TabularThermo`/import 路径错）——真实能力边界；沙箱 add_subsystem 误封修正后重跑定稿 |

复现：
```bash
cd benchmarks && MPLCONFIGDIR=/tmp .venv/bin/python -m runners.simulation_agent \
  --tasks tasks/pycycle.engine_cycle --out results/pycycle.engine_cycle/2026-08-19/<provider> \
  --provider <p> [--model <m>] --seed 0
```
