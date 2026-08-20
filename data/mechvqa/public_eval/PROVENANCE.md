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
