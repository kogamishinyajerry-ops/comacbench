# aeroengqa.gold 2026-08-19 运行索引（M1 收尾）

> 落点约定：`results/<registry_id>/<date>/<provider>/`。
> `assets_revision = aeroengqa@zenodo.14215677-v1.0`（全部运行一致）。
> 80 题 = single/multi-hop × answerable/unanswerable 各 20；qa_grounded free_text
> 四层判分（gate / 客观 / 拒答+证据 / 区分），全部规则判，无 LLM judge。

| 子目录 | provider/model | gate | 拒答正确率(40题) | 误拒率(40题) | 证据支持 | 捏造引用 | 客观层均值* | 区分层 | 任务均分 |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| `stub/` | stub（seed=0） | 80/80 | 0.0000 | 0.0000 | 0.8750 | 0 | 0.0365 | 1.0000 | 0.6354 |
| `glm-4.6/` | glm / glm-4.6 | 80/80 | **0.9250** | 0.0750 | 0.8938 | 0 | **0.6304** | 0.9750 | 0.8797 |
| `minimax-m3/` | minimax / MiniMax-M3 | 80/80 | 0.8750 | **0.0250** | **0.9375** | 0 | 0.5851 | **1.0000** | **0.8852** |

*客观层仅应回答 40 题计分（归一化精确/数值容差=满分，token F1 部分分）；oracle 判分器自检 80/80 满分（未落盘，属判分器验证步骤）。

要点：
- 两模型任务均分接近（0.880 vs 0.885），但能力画像不同：GLM 拒答/客观更强，M3 引用纪律与区分声明更好、误拒更少；
- 捏造引用（fabrication_rate>0）两家均为 0——引用段落全部真实存在；
- 区分层口径为 BASIS 结构合法性（数据集无参考 basis 标签，逐字核验不进分，见任务 YAML 注释）；
- M3 中位延迟 3s/题 vs GLM 18s/题。

每子目录：`result_*.json`（80 个，含 layer_details 中间量）+ `summary.md`（gate 类分布 + 四层指标 + 每题明细）+ `run_manifest.json`（seed/digest/重跑命令）。
