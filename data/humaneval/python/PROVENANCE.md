# HumanEval 编程镜像溯源（PROVENANCE）

> assets_revision: `humaneval@openai-master+jsonl_20260821`
> 镜像日期: 2026-08-21 · 镜像执行: 数学/编程扩充会话（dev 终端）

## 镜像内容

| 文件 | 来源 | sha256 |
| --- | --- | --- |
| `HumanEval.jsonl` | HF `openai/openai_humaneval`（datasets-server /rows 分页拉取，与 GitHub `openai/human-eval` HumanEval.jsonl 同源） | `b2adeeae8b383b6f0c615746a397f25c8abe44da4afb29cd10e6c4bbf0463fd3` |
| `LICENSE.MIT` | GitHub `openai/human-eval` master LICENSE 原样拷贝（MIT, Copyright OpenAI） | 见文件 |
| `hf_dataset_card.md` | HF 数据集卡快照（license 徽标证据） | 见文件 |

## 数据校验（镜像时核验）

- 题数 = 164（HumanEval/0 – HumanEval/163 连续无缺，task_id 唯一）；
- 每题字段 `prompt`（签名+docstring，官方评测用原始提示）/ `canonical_solution` / `test`（官方测试块）/ `entry_point` 全部存在；
- prompt 中 docstring 自带 `>>>` doctest 示例（官方提示原样保留——doctest 属公开提示面，隐藏判分层为 `test` 块全量断言）；
- 任务全集 164/164（不做抽样，与社区 pass@1 直接可比）。

## 许可证据链（先许可证后镜像，2026-08-21 核验）

1. **GitHub 仓库** `openai/human-eval`：根目录 `LICENSE` = **MIT License**（Copyright (c) OpenAI (https://openai.com)），随镜像保存为 `LICENSE.MIT`。
2. **HF 数据集卡** `openai/openai_humaneval`：license 字段 = `mit`（快照 `hf_dataset_card.md`）。
3. MIT 宽松许可：商用/再分发/修改允许，条件为保留版权与许可声明——随镜像保存 LICENSE 即满足。

结论：`license_status: confirmed-repo`（MIT）成立，镜像放行。

## 隐藏测试与提示面（判分口径声明）

- 模型可见：`prompt`（含 docstring 与 doctest 示例，官方原文）+ 追加格式要求；
- 判分隐藏：`test` 块断言（平均 ~7.7 条/题）——从 `def check(candidate):` 中逐条抽出断言，
  与模型函数拼装执行（unit_tests_problem，见 code_exec.py）；
- `canonical_solution` 仅作 oracle 判分器自检源（不进提示面、不进报告）。

## 重取方式（离线重跑不需要网络，仅更新数据时用）

```bash
# GitHub 直连（master 布局变动时以 HF datasets-server 兜底，与本镜像同路径）
curl -L -o HumanEval.jsonl https://raw.githubusercontent.com/openai/human-eval/master/HumanEval.jsonl
# 兜底：datasets-server /rows 分页（dataset=openai/openai_humaneval, split=test）
```
