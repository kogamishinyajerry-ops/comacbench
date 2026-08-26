# PROVENANCE — spreadsheetbench.verified_subset（2026-08-26 深审后重写，替代 6 行简版）

> 镜像：2026-08-26。来源 https://huggingface.co/datasets/KAKA22/SpreadsheetBench
> （`spreadsheetbench_verified_400.tar.gz`，14,958,255 B，tar.sha256 随镜像落盘）。
> 合订背景见 data/awdoc/office_docs/PROVENANCE.md §C（三基准同板）。

## 1. 许可核验（证据链）

- **CC BY-SA 4.0**：HF 数据集卡片 `license: cc-by-sa-4.0`（2026-08-26 经 datasets API
  核验，字段 `cardData.license`）；gated=False 公开可取。
- **BY 义务**：再分发/派生须署名 SpreadsheetBench 作者（论文 *SpreadsheetBench:
  Towards Challenging Real World Spreadsheet Manipulation*，HF 卡片指向论文/主页）。
- **SA 义务**：派生评测集（本目录 25 个任务 YAML + init/golden 副本）按同许可
  （CC BY-SA 4.0）发布——与 superwing（CC BY-SA 4.0）同口径。
- 早期简版 PROVENANCE 仅一句许可声明（2026-08-26 深审 minor 发现），本文件为补全。

## 2. 镜像物清单

- `tar.sha256`（原始 tar 摘要）+ 解包 `spreadsheetbench_verified_400/`（dataset.json
  400 条 + spreadsheet/*/ 各含 `1_<id>_init.xlsx`/`1_<id>_golden.xlsx`/prompt.txt）；
- `inputs/ssb_<id>_init.xlsx` 与 `gold/ssb_<id>_golden.xlsx`：入选 25 题的工作副本
  （任务 YAML assets.digest 逐文件 sha256 锁定）；
- `gold_scripts/ssb_<id>.py`：oracle 自包含脚本（golden answer 区域值 JSON 字面量
  内嵌，datetime 结构化往返——2026-08-26 工程记录）。

## 3. 筛选口径（2026-08-26，程序化+如实）

- Cell-Level 275 题卡片**全部无 answer_sheet/answer_position 定位**（上游判分依赖
  其 LLM validator，违反本仓库 scoring §3/§4 判分纪律）→ 全部出局；
- Sheet-Level 125 题中 107 题通过「golden 可读 + 区域可解析 + 区域含静态值」筛；
  按类型配额取 25（另 6 题缺文件/13 题区域格式异常出局）。

## 4. 判分链环境依赖（内网移植红线）

公式语义经 **LibreOffice headless**（`soffice --headless --convert-to`）重算落盘缓存值
后 data_only 读 answer 区域比对 golden（golden 自带 Excel 缓存值同口径）。
dev 实测 `/opt/homebrew/bin/soffice`（LibreOffice 26.2.3.2）。**内网移植必须携带
soffice 二进制**（env-matrix.md §2 Phase-E，2026-08-26 补记）。

## 5. 已知判分边界（2026-08-26 深审在案，待修复项见审计报告）

- answer_sheet 缺失时回退首表 + requirements 恒 1.0（声明契约未检验，0.5 分地板）
  ——深审 major，修复需伴随基线重跑；
- 区域内 init 既有值不罚 extra（2026-08-26 实测教训，注释在
  runners/design_artifact.py:1031-1035）。

## 6. 复现

```bash
curl -sL <HF>/resolve/main/spreadsheetbench_verified_400.tar.gz   # 对照 tar.sha256
.venv/bin/python -m runners.design_artifact \
    --tasks tasks/spreadsheetbench.verified_subset \
    --out results/spreadsheetbench.verified_subset/<date>/<provider> --provider <p> --seed 0
```
