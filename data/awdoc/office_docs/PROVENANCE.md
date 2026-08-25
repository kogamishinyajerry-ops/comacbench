# PROVENANCE — 办公第二板（三基准，2026-08-26）

> A awdoc.office_docs（数据锚定文档）· B awext.clause_extract（条款结构化抽取）·
> C spreadsheetbench.verified_subset（SpreadsheetBench 精选）。
> 生成器 `runners/gen_tasks_office2.py`；判分：A/C = design_artifact 新模式，
> B = qa_grounded json_extract 层。

## A. awdoc.office_docs（18 题，自建）

- **协议**：模型读 cwd CSV（性能汇总/载荷实测风格），产 `report.docx`（6 题）或
  `report.pptx`（6 题）……实为 docx×9 + pptx×9（perf×6 + load×3 各双格式）。
- **判分**（doc_document 模式）：physics = 锚定数字命中（源数据派生统计
  min/max/mean/count，数值级 0.5% 容差——「所有数字来自数据」即得分锚）；
  requirements = 结构契约（表格数/图片数/段落数下限/页帧数精确）；
  gate 含双跑文本数字+结构一致性。
- **边界（如实）**：不评文风/措辞（LLM judge 违纪律）；锚定数字+结构是
  「数据一致性报告」的可客观判分核心；字符串锚（构型名）不判。

## B. awext.clause_extract（12 题，自建条款风格卡）

- **协议**：读条款风格卡（参数化合成——**非真实规章原文**，防误引），输出
  规定 9 字段 JSON；判分 = 字段级（数值 2% 容差；两列表字段排序 casefold 精确）。
- **KB 联动状态（如实）**：本会话 civair-kb 三端点（query/get/status）均不返回
  内容（仅 ok）——原计划「真实条款按 doc_id 锚定」不可行，降级为自建风格卡；
  KB 恢复后重锚（任务 YAML license_provenance 已标注）。
- oracle = reference_json 回显（providers 新增 json_extract oracle/stub 分支）。

## C. spreadsheetbench.verified_subset（25 题，外部 CC-BY-SA-4.0）

- **来源**：HF KAKA22/SpreadsheetBench `spreadsheetbench_verified_400.tar.gz`
  （sha256 随镜像落盘 `tar.sha256`）；SA 衍生同许可——superwing 先例口径。
- **筛选（程序化，全部如实）**：400 题中 Cell-Level 275 题**全部无 answer 定位**
  （上游判分依赖其 LLM validator，我们不引入）→ 出局；Sheet-Level 125 题中
  107 题通过「golden 可读 + answer 区域可解析 + 区域含静态值」；按配额取 25。
- **协议**：模型以 init.xlsx 为底产 `output.xlsx`（可写公式或值）；判分
  （formula_cell 模式）：LibreOffice headless（soffice --convert-to）重算落盘
  缓存值 → data_only 读 answer 区域 → 对 golden 同区域（golden 自身带 Excel
  缓存值，同口径）单元格比对（数值 0.5% / 字符串 casefold）。
- **oracle**：自包含 gold 脚本（golden 区域值 JSON 字面量内嵌，datetime 转
  `{"__date__"}` 结构）——25/25 满分自检含 soffice 链。
- **内网移植风险（如实）**：判分依赖 LibreOffice——内网需带 soffice 二进制
  或换 Microsoft headless 通道；已在 env-matrix 标注。

## 判分器修正记录（本板两条教训）

1. **answer 区域 extra 惩罚误杀**（SSB）：区域内 init 既有数据被当「多余单元格」
   扣分（455_35 一题 93401 个 extra）——修正为不罚区域内 init 保留值
   （golden 有值格命中 + mismatch 即失分，滥用防护由 sheet 结构保持承担）；
2. **oracle 脚本可执行性**：repr(datetime) 不可执行 + 巨长单行——改 JSON 字面量
   分行 + 日期结构化往返。

## 复现

```bash
.venv/bin/python -m runners.gen_tasks_office2          # 三线生成（幂等）
.venv/bin/python -m runners.design_artifact --tasks tasks/awdoc.office_docs ...
.venv/bin/python -m runners.qa_grounded --tasks tasks/awext.clause_extract ...
.venv/bin/python -m runners.design_artifact --tasks tasks/spreadsheetbench.verified_subset ...
```
