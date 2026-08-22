# T4 · 快照格式与归档纪律

- Label: `wayfinder:grilling`（HITL） · Status: open · Blocked by: —

## Question

"一键导出里程碑快照"的具体形态：

1. 快照粒度：单个 JSON（全量 19 基准 ~80 组合，规模已查证装得下）还是按基准分片 + 索引？
2. 快照内容边界：result.json 全量保留还是只留视图聚合字段 + 单题下钻回源活读？
3. 落点与归档：路径约定（`results/_snapshots/`？`report/`？）、是否进 git、与里程碑报告（M1-summary 等）的引用关系。
4. 快照里要不要带 environment_digest / assets sha256（run_manifest 的可复现性字段）的直接拷贝？

背景：数据规模小（全量单 JSON 可行）；可复现性是本仓库的一等价值观（run_manifest、PROVENANCE、sha256 锁定）。

## Resolution

（待解）
