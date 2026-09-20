# CFD 研究证据接入与准入 v1

本版把 Re=100/200/300 的 48 组已接受研究接入现有插件目录、材料预检、运行前置门和离线反馈。研究对象为二维稳态层流后向台阶，四档网格 × 四种域。当前可评分任务仍只有 Re=100，公开相对带仍为 10%，不自动发布或扩展工况。

## 调用

```sh
.venv/bin/python -m comacbench.admission catalog
.venv/bin/python -m comacbench.admission validate packs/aviation-cfd-step-v1 --out ./evidence-feedback-01
.venv/bin/python -m comacbench.admission run packs/aviation-cfd-step-v1 --agent ./agent.json --out ./evaluation-01
.venv/bin/python -m comacbench.evidence --full
```

DSH 原有 `comac_pack_catalog`、`comac_pack_validate`、`comac_agent_run` 及 GET `/comac/packs` 直接使用新准入层，工具参数不变。工作台显示研究矩阵与候选带，反馈报告仍为离线 HTML。

原 `python -m comacbench` 内核被历史研究协议冻结，因此保留为历史兼容入口；它没有新增研究证据检查。新贡献、运行及续跑应使用 `.admission` 入口或现有插件。这是本地可信执行路径，不是防止用户绕过的安全沙箱。

## 贡献契约

在原有 `pack.yaml` 中加入：

```yaml
validation_evidence:
  protocol: comacbench.research-links.v1
  purpose: research_support
  studies:
  - bfs-re100-validated-v1
  - bfs-re200-validated-v1
  - bfs-re300-validated-v1
```

CFD 包必须提供至少对应 Re=100 的已接受依据。缺失、重复、未知研究 ID、用途改成评分授权、额外未知声明、文件缺失或摘要改变都阻断运行；输出包含 `code / field / message / suggested_fix`。旧有单位、边界、参考值、容差、负例与权重检查继续执行。企业数据与本体包未声明研究附件时保持原流程。

新评测集可以引用已接受 ID；新的研究材料不能自报“通过”后进入目录。维护者须核验工况、完整矩阵、原始文件清单、独立复核回执、版本与来源，再建立新的目录版本及绑定摘要。当前仅支持这三份已核验研究的引用，不声称实现任意新求解器或任意 Re 的自动科学审查。

## 证据边界

| 工况 | 接受的分析 | 研究候选带 | 可评分 |
|---|---|---|---|
| Re=100 | 2026-09-06-cfd-fourth-grid-final | 2.5% | 现有任务，10% |
| Re=200 | 2026-09-08-cfd-primary-v2，32 保存场重降算 | 2% | 尚未接入 |
| Re=300 | 2026-09-08-cfd-re300-v3，15 新求解 + 1 保存算例复用 | 2% | 尚未接入 |

候选带是保守误差筛查之和，不是统计置信区间。`calibrated_tolerance` 始终为空。Re=200 旧失败分析、Re=300 v1/v2 失败或不完整尝试不在可接受 ID 中。

`evidence/cfd-validation-v1.json` 记录仓库相对路径及原始分析、协议、回执、每例结果和原生证据清单的 SHA-256，其自身摘要固定在新模块中。快速准入每次读取并校验这些锚点，检查 16 个唯一网格/域组合、工况、有效门和容差边界；明确标为 `analysis_and_receipt_hashes`。它不重读全部原始场，不能宣称本次已完成原生复核。

`--full` 在锚点通过后流式核验 48 组算例的原生证据清单内全部文件，标为 `native_file_hashes`。此操作不求解、不调用模型，也不重算物理量。重新进行物理降算仍使用各冻结研究中的原验证命令。本轮新报告记录文件核验结果。

附件依赖当前仓库的 `report/` 证据树。单独复制 pack 到缺少该证据树的安装环境会拒绝通过，需要一并分发许可范围内的证据及目录；没有网络下载或未知路径解析。原报告、冻结代码和旧评分均不改写。

## 验收

- `python -m unittest discover -s tests -p test_cfd_evidence_admission.py`：缺失/未知/损坏/工况错配/容差越权拒绝，三矩阵通过但不增加评分任务。
- `node plugin/dsh-comac-benchmark/test-packs.mjs`：实际注册工具、目录和 GET 路由成功；无效研究附件不会启动 agent。
- `python -m comacbench.evidence --full`：输出 `passed=true`，三档各 16 例，所有列入原生清单的文件匹配。
- 工作台 `npm run bundle` 及全量本地测试通过。

## 2026-09-08 清理后的现行保留策略

按用户要求，删除原始场、网格、并行分区、重建产物、中间过程、重复源码副本和失败尝试。保留 127 个分析/回执/索引锚点及最终图表，相关目录约 72 MiB。目录中的 `native_evidence_state: deleted_by_user` 明确声明清理状态；`verify_study` 返回 `retained_analysis_and_receipts` 及 `native_evidence_available: false`，`--full` 返回退出码 2 和 `native_evidence_deleted`。

准入保留一条人工审查反馈，新的 agent 评测仍可使用原有公开契约；历史研究只能查看结果与摘要，不能复核原始场，也不能据此扩大评分范围。旧报告中的成功回执是历史记录，完整交付清单不再全部可用。清理数量与范围见 `report/2026-09-08-storage-cleanup/completion.json`。
