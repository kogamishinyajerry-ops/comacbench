# cfdllm.cfdquery 2026-08-19 运行索引（M1）

> 落点约定：`results/<registry_id>/<date>/<provider>/`。本目录为当日全部评测轮；
> `assets_revision = cfdquery@3b46d30+kaggle_v4`（三份运行一致）。

| 子目录 | provider/model | gate 通过 | 客观层 | 说明 |
| --- | --- | --- | --- | --- |
| `stub/` | stub（确定性伪答案，seed=0） | 90/90 | 25/90 = 0.2778 | 离线管线冒烟基线，可逐字节复现 |
| `glm-4.6/` | glm / glm-4.6（thinking enabled，失败升级 disabled） | 90/90 | 78/90 = 0.8667 | 真实 API 基线 |
| `minimax-m3/` | minimax / MiniMax-M3（<think> 剥离 + 32k 思考预算） | 90/90 | 73/90 = 0.8111 | 真实 API 基线 |

- 每子目录：`result_*.json`（90 个标准 result.json）+ `summary.md`（gate 类分布 + 每题明细）+ `run_manifest.json`（seed / environment_digest / assets sha256 / 重跑命令）；
- 结论汇总与重跑命令见 `../../M1-summary.md` §2.3–2.4；
- oracle 判分器自检（90/90=100%）未落盘本目录，属判分器验证步骤，记录于 M1-summary §2.3。
