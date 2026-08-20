# scicode.physics 2026-08-19 运行索引（M2）

> 落点约定：`results/<registry_id>/<date>/<provider>/`。
> `assets_revision = scicode@e3158ea+hf_v1+test_data_h5_20240712`。
> **M2 收口：52 主问题**（test 40 + dev 12，209 步可判分 207 步）——子集划定见
> `data/scicode/physics/subject_map.md`（AI 辅助标注 + 论文计数校验 + 5 项偏差记录）。

| 子目录 | provider/model | gate | 任务均分 | 关键观察 |
| --- | --- | --- | --- | --- |
| `stub/` | stub（seed=0，输出 `pass`） | 52/52 | 0 | pipeline 完整跑通：所有步因无函数定义 → NameError（physics 0）|
| `oracle/` | dev gold 源码（12 dev 题） | 12/12 gate；**10/12 满分** | — | p078.3 机器计时依赖（gold 用 `time.time()` 选时间步）+ p070.8 case4 退化构型（s13=0）scipy 版本漂移——2 题环境依赖偏差已知不可修 |
| `minimax-m3/` | minimax / MiniMax-M3 | 42/52 | **0.674** | gate fail 10：sandbox_escape ×1, code_not_executable ×8, timeout ×1；gate 通过 42 题中 14 满分、28 部分分 |
| `glm-4.6/` | glm / glm-4.6 | **1/52**（API 429 限流） | — | 共享 coding API 端点与 M3 并发触发 429，重试仍限流；命令保留供后续单跑补齐 |

每子目录：`result_*.json`（52 个，含 `grade_details.per_step` 逐步逐 case 通过模式 + `grade_details.cases_pass/total` 汇总）+ `summary.md`（gate 类分布 + 子分桶 + 每题明细）+ `run_manifest.json`。

## 协议偏差（与官方 SciCode leaderboard **不可直接对比**）

- **整题一次生成**（官方为逐步骤多轮自回归，gold 答案逐步提交）。
  难度更高（无中间反馈、需自洽），分数作为本 harness 自有整题生成基线。
- **judge_explain 未实现**：区分层不进入 `score`（per adapters/README.md §1 边界），仅作结构合法性校验。
- **evidence 文档已与 SciCode 官方 assert 语义一致**（h5 期望值 + 数据集原始断言行），未见差异。

## 判分器正确性验证

- oracle self-test：dev 12 题中 10 满分（与 gold 自身机器/库漂移 2 题偏差对应）。
- stub 52/52 gate pass + 0 physics：判分器对「无函数定义」的容错正确。
- 复跑 stub 两次逐字节一致（stub/oracle 离线确定性）；真实 API 基线受推理模型非确定性影响。
