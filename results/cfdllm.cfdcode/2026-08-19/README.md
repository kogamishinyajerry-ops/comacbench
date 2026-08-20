# cfdllm.cfdcode 2026-08-19 运行索引（M2）

> 落点约定：`results/<registry_id>/<date>/<provider>/`。
> `assets_revision = cfdcode@3b46d30+kaggle_v1`。
> **M2 收口：15 任务**（24-9 不可用，9 排除原因见 `data/cfdllm/cfdcode/PROVENANCE.md`）。

| 子目录 | provider/model | gate | 任务均分 | 关键观察 |
| --- | --- | --- | --- | --- |
| `stub/` | stub（seed=0，输出 `pass`） | 0/15 | — | gate 失败 = missing_output（`pass` 不产出 npy）；与设计语义一致 |
| `oracle/` | 锁定 gold npy 注入 | 15/15 | **1.000** | gate/插值/余弦/R²/确定性 全验证通过（仅 1 题因 `v` 全零场 cosine 退化，加零范数守卫后满分）|
| `minimax-m3/` | minimax / MiniMax-M3 | 8/15 | 0.881（gate 通过子集） | gate pass 8 题物理层均值 0.937；fail 7 题中 code_not_executable ×4, non_physical ×2, missing_output ×1 |
| `glm-4.6/` | glm / glm-4.6 | **3/15**（API 429 限流） | — | 共享 coding API 端点与 M3 并发触发 429，重试仍限流；命令保留供后续单跑补齐 |

每子目录：`result_*.json`（15 个标准 result.json，含 `grade_details` 字段中的 MSE/MAE/RMSE/Cosine/R²/NMSE 逐变量指标 + 零范数守卫说明）+ `summary.md`（gate 类分布 + 子分桶 + 每题明细）+ `run_manifest.json`（seed/digest/重跑命令）。

## 协议偏差（与官方榜单不可直接对比）

- **判分口径**：gate 必先于子分；physics = 逐变量 mean(clamp01(Cosine), clamp01(R²)) 按变量均值——官方只报指标不折分（report 原文，arXiv:2509.20374 / 仓库 `utils.py:compute_losses`），本 harness 折分以匹配 code_exec 子分映射（adapters/README.md §2）。
- **金标准注入**：oracle 路径注入预计算 npy 不执行 gold 源码（gold 执行路径在 `PROVENANCE.md` 预计算阶段验证）。
- **CFDCodeBench 官方 journal/macro runner 不在 dev 终端跑**——本 harness 只走 Python 数值解端；内网线换 Fluent/StarCCM+ 时需重接 solver_runner。
