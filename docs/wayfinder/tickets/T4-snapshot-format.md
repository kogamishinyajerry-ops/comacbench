# T4 · 快照格式与归档纪律

- Label: `wayfinder:grilling`（HITL） · Status: **closed**（2026-08-23 grilling 拍板） · Blocked by: —

## Question

"一键导出里程碑快照"的具体形态：

1. 快照粒度：单个 JSON（全量 19 基准 ~80 组合，规模已查证装得下）还是按基准分片 + 索引？
2. 快照内容边界：result.json 全量保留还是只留视图聚合字段 + 单题下钻回源活读？
3. 落点与归档：路径约定（`results/_snapshots/`？`report/`？）、是否进 git、与里程碑报告（M1-summary 等）的引用关系。
4. 快照里要不要带 environment_digest / assets sha256（run_manifest 的可复现性字段）的直接拷贝？

背景：数据规模小（全量单 JSON 可行）；可复现性是本仓库的一等价值观（run_manifest、PROVENANCE、sha256 锁定）。

## Resolution

四项裁决（基于实测事实：results/ 42M、9728 个 result.json **中位仅 1.5KB**、88 个 run_manifest 字段现成、results/ 9866 文件**已在 git**）：

1. **粒度 = 聚合单 JSON**：全库一个文件（全部基准×日期×provider 聚合行），估算 <2MB；快照模式一次加载、git diff 友好、评审单文件可发。不按基准分片。
2. **内容边界 = 聚合 + git_commit 指针，`--full` 选装**：明细 SSOT 永在 results/——它已在 git，**git 历史即"那一刻"的冻结**，快照不复制明细；快照模式下钻读当前盘并标注时点差。导出器另提供 `--full`：打全量自包含包（含全部 result.json）供评审外发，**不进 git**。
3. **落点 = `results/_snapshots/<tag>.json`，进 git**（tag = 里程碑名或日期）；与 results/ 既有 git 纪律一致，M1–M4 summary 就在 results/ 根部，报告引用快照文件名最顺。
4. **可复现字段全带（内联拷贝）**：每 run 条目内联 environment_digest / assets sha256 / seed / rerun_command / git_commit；快照头记全库 git commit + 生成器版本——快照独立自明，不回链 88 个 manifest。

schema 细节（聚合行字段清单）归 T6 数据契约章，由本决议约束。
