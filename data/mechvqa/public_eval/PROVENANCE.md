# MechVQA 公开评测集镜像溯源（PROVENANCE）

> assets_revision: `mechvqa@github-HEAD-2026-08-19`
> 镜像日期: 2026-08-19 · batch-2 会话（dev 终端）

## 镜像内容

| 内容 | 说明 |
| --- | --- |
| `benchmark_data/` | 1185 题公开评测集（vqa_benchmark/mechvqa_benchmark.jsonl + images/ 全部图纸）|
| `LICENSE.apache-2.0` | GitHub `xiaofengShi/MechVQA` LICENSE 原样拷贝 |
| `upstream_README.md.reference` | 官方 README |

## 许可（2026-08-19 核验）

GitHub 仓库 LICENSE = Apache-2.0（含 benchmark_data 评测集与图纸）→ confirmed-repo，镜像放行。

## 数据结构（镜像时核验）

- 1185 题：messages（user 中文题面 + assistant 参考解释）、images（相对路径）、
  metadata（capability: Recognition 642/Reasoning 289/Judging 254；subcategory 10 类；
  difficulty；explanation；language）、qualityscore；
- 图片：images/00..07 分片目录，含剖视图/装配图/标注图等工程制图。

## 接入 blocked（如实记录）

- **多模态输入通道缺失**：现 providers 层只有文本（mcq/free_text/code/json）——MechVQA 的
  被测对象需图文混合输入（图纸 + 问题），GLM-4.6 coding 端点不支持图片，M3 支持但 provider
  需扩展 content 多模态结构。qa_grounded 需新增 expect="vlm" 模式；
- 判分：官方用 `<answer>` 标签抽取 + 自由文本比对（LLM judge 评解释质量，registry 约束
  「客观题规则判分优先」——MechVQA 答案为自由解释文本，规则判分只可做关键词/F1 层，
  judge 分单列）。进待议：多模态 provider + 规则判分口径评审。

## 重取

```bash
git clone --depth 1 https://github.com/xiaofengShi/MechVQA && cp -r MechVQA/benchmark_data .
```

## 任务集派生（2026-08-21，runners/gen_tasks_mechvqa.py）

- 池：`vqa_benchmark/mechvqa_benchmark.jsonl` 中 qualityscore==1.0 的全部 **1117** 行
  （0-based 原始行号；1185 行中其余 68 行 qualityscore<1.0 剔除）；
- 分配：按 (capability × difficulty) 9 格比例分配共 **180** 题，最大余数法
  （余数并列时按格内样本数降序、格名升序定序，保证可复现）；
- 抽样：每格内对格内原始行号列表用 `numpy.random.default_rng(20260821)` 独立打乱
  （每格同种子重置，逐格互不影响）后取前 k 个；
- 编号：180 题按原始行号升序编号 mechvqa_q001..mechvqa_q180（行号范围 2..1177）；
- 产物：`tasks/mechvqa.public_eval/`（180 YAML + 180 题面 md）；每题恰 1 张图
  （input.assets role=image，sha256 逐图锁定，180 题共覆盖 148 张唯一图——
  少量图纸被多题共用）；`--check` 幂等校验通过（2026-08-21）。

| capability | difficulty | 池（qs==1.0） | 分配 |
| --- | --- | ---: | ---: |
| Judging | Easy | 82 | 13 |
| Judging | Hard | 48 | 8 |
| Judging | Medium | 116 | 19 |
| Reasoning | Easy | 63 | 10 |
| Reasoning | Hard | 96 | 15 |
| Reasoning | Medium | 106 | 17 |
| Recognition | Easy | 419 | 68 |
| Recognition | Hard | 21 | 3 |
| Recognition | Medium | 166 | 27 |
| **合计** | | **1117** | **180** |

选中 180 题的边际分布：capability Recognition 98 / Reasoning 42 / Judging 40；
difficulty Easy 91 / Medium 63 / Hard 26；语言 中文 125 / 英文 55。

冒烟（results/mechvqa.public_eval/2026-08-21/，seed=0）：
stub gate 180/180、均分 0.0692（地板；5 题因参考答案数字集 ⊆ stub 样板
「第 N/180 题」数字集而撞数值容差层满分——grader 既有语义，非生成器缺陷）；
oracle gate 180/180、均分 1.0000（判分管线自检通过）。
