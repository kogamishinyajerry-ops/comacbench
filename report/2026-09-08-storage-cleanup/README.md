# CFD 过程文件清理

按用户要求删除 49,993 个文件/链接：逻辑大小 95,951,505,924 bytes（约 96 GB）。清理覆盖 CFD 研究报告目录中的原始场、网格、求解日志、MPI 分区与重建文件、重复源码副本、失败及中间尝试。代码、任务、公开模板及非 CFD 数据不在删除范围。

保留 188 个摘要、索引、回执、最终图表和少量集成报告文件，约 72 MiB。保留的 127 个摘要锚点逐项核验通过。逐文件删除清单压缩为 removed-files.jsonl.gz；completion.json 显示删除目标残留为 0。

系统 df 实测可用空间由约 47 GiB 增至 54 GiB（约增加 7 GiB）。逻辑文件大小与物理释放空间并不等同；未确证差额原因，没有据此删除系统快照、其他项目或 Docker 公共资源。

变更 evidence/cfd-validation-v1.json、comacbench/evidence.py、comacbench/admission.py、工作台 engineering.jsx 和构建文件，新增 tests/test_cfd_retention.py。保留页面增加清理声明。历史完整交付清单和复核记录仅作历史信息，原始场现在不存在。

验证：

- `python -m unittest discover -s tests -p test_cfd_retention.py`：2 项通过，清理状态下完整核验明确拒绝。
- `python -m unittest discover -s tests -p test_cfd_evidence_admission.py`：9 项通过。
- `node plugin/dsh-comac-benchmark/test-packs.mjs`：通过。
- 工作台 `npm run bundle`：通过，保留既有构建弃用提示。
- `python -m comacbench.admission validate packs/aviation-cfd-step-v1`：可本地运行，三份研究均标记 retained_analysis_and_receipts / native_evidence_available=false。
- `python -m comacbench.evidence --full`：预期退出 2，native_evidence_deleted。

限制：删除未放入废纸篓，也未创建原始场备份。需要物理复核时须重新求解。当前测试覆盖准入与清理行为，没有重跑依赖已删除历史材料的研究测试。

建议后续 Benchmark 默认交付摘要、必要图表和复现配置，原始场仅按需短期保存或导出；不自动积累全部时间步和重复工况。
