# cfdllm.foam_basic 2026-08-19 运行索引（M3）

> 落点约定：`results/<registry_id>/<date>/<provider>/`。
> `assets_revision = foambasic@3b46d30+kaggle_v1+gt_runs_2026-08-19`（110 任务全量，
> GT 预计算 110/110 全过，0 排除）。

| 子目录 | provider/model | gate | 任务均分 | 说明 |
| --- | --- | --- | --- | --- |
| `stub/` | stub | 0/110 | 0 | missing_output ×110（`pass` 不产算例）——gate 语义正确 |
| `oracle/` | GT 逐字写出器 | **110/110** | **1.000** | GT→docker 重跑→NMSE=0 自洽（判分器全量验证）|
| `minimax-m3/` | MiniMax-M3 | 0/110 | 0 | **87 code_not_executable + 23 simulation_failed**（脚本崩溃 / Allrun 用 `source` 而非 POSIX `.`）——LLM 写不出可运行 OpenFOAM 算例 |
| `glm-4.6/` | GLM-4.6 | 待跑 | — | 共享端点 429 限流（M2 遗留），配额恢复后单跑补齐 |

判分口径（官方语义映射，详见 `data/cfdllm/foam_basic/PROVENANCE.md`）：
- gate = 脚本跑通 → 算例结构契约（system 四件套+constant+0+Allrun）→ docker Allrun 跑完
  （官方判据 log.*Foam 倒数第二行 == "End"）；
- physics = NMSE（pyvista 末时刻场 [U,p,rho,T]，官方插值对齐 + 官方阈值
  <0.1→1.0 / <0.3→0.5 / else 0）；
- 官方 Tree/ROUGE 不纳入（结构以 gate 契约守）——M3-summary 待议 5。

复现：
```bash
cd benchmarks && MPLCONFIGDIR=/tmp .venv/bin/python -m runners.simulation_agent \
  --tasks tasks/cfdllm.foam_basic --out results/cfdllm.foam_basic/2026-08-19/<provider> \
  --provider <p> [--model <m>] --seed 0
```
