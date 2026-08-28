# PROVENANCE — cfdagent.litbench

> 生成链路：arXiv Atom API 原文抓取 → 策展合并 → 题库 → 任务。全链路可重入，
> 生成器 `runners/gen_tasks_cfdagent.py`（`--check` 可校验漂移）。

## A. 语料来源（papers.json，36 篇）

- 抓取：`runners.arxiv_corpus.fetch`（export.arxiv.org/api/query），抓取日期 2026-08-28，
  User-Agent `comacbench-corpus/0.1`，遵守 3s 礼貌间隔与退避重试。
- 每篇记录 `abstract_sha256 = sha256(title + "\n" + abstract)`，任务 YAML 引用 papers.json
  整体 sha256 锁版本；摘要文本一字未改（仅抓取时折叠空白）。
- 元数据层（category/venue/code_url/license）来自三路独立调研（2026-08-28 会话）：
  1. arXiv API 全字段检索（本会话直连核验）；
  2. 子代理 A：agent-CDF 论文 GitHub LICENSE 核验（MetaOpenFOAM=GPL-3.0、Foam-Agent=MIT、
     AutoCFD=GPL-3.0、ChatCFD=声明 GNU、CFDLLMBench=BSD-3-Clause）；
  3. 子代理 B：ML-CFD 数据集许可核验（The Well 代码 BSD-3、PINNacle MIT、Transolver MIT、
     DrivAerNet++ 数据 CC BY-NC 4.0、FlowBench 数据 CC BY-NC 4.0、UniFoil CC BY-SA 4.0、
     BLASTNet 数据 CC BY 4.0）。核验明细见 `research/cfd_paper_code_licenses.json`、
     `research/cfd_bench_papers_2020plus.json`。

## B. 题库（questions.json，60 题）

- 题面为本仓库自建（confirmed-selfbuilt），每题 `evidence` 为对应 arXiv 摘要的**逐字子串**，
  生成器 `_norm` 归一空白后 substring 强校验，失败即退出非零（防幻觉纪律）。
- 干扰项取同类同型值（优先取语料内其他论文的同类数值），`answer` 为 0 起始下标；
  转 YAML 时 +1 对齐 qa_grounded 契约（correct_option_index 1 起始）。
- qtype 覆盖：single_numeric / single_arch / single_metric / single_ablation / single_bench /
  single_data / single_method / single_case / single_result / single_finding / single_stack /
  single_capability / single_task / cross_chronology / cross_case / cross_baseline /
  cross_capability / cross_data / cross_route / cross_domain。

## C. 使用与署名义务

- arXiv 摘要经公开 API 获取，用于研究性评测属允许用途；任何再分发须保留
  papers.json 中的 arXiv id / 作者 / 链接署名，不声称 arXiv 背书。
- 题面与判分逻辑为原创，不受上游论文许可证约束；若未来镜像论文全文（PDF 级），
  需按各论文自身许可另行清点（当前不做）。

## D. 已知边界

- 非 arXiv 的 V&V/研讨会论文（DPW-VII、HLPW-4/5、NASA Juncture Flow、SA-QCR2000 套件、
  TUDa-GLR-OpenStage 等，共 10 篇，Crossref/NTRS 核验）**不进入 litbench 题库**（无摘要级
  可核验文本），仅进入调研报告与 registry 转化条目；清单见
  `report/2026-08-28-cfd-agent-survey.md` §V&V。
- 摘要中的量化声明只反映论文自述，litbench 考"文献知识"，不背书其结论正确性。
