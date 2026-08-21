# MATH-500 数学推理镜像溯源（PROVENANCE）

> assets_revision: `math500@hf-h4_v1_20260821`
> 镜像日期: 2026-08-21 · 镜像执行: batch-3 第二波会话（dev 终端）

## 镜像内容

| 文件 | 来源 | sha256 |
| --- | --- | --- |
| `math500_test.jsonl` | HF `HuggingFaceH4/MATH-500`（datasets-server /rows 分页拉取，500 题） | `35dc41080a3680858b27fa7e0533d2d547825316fc5dafe5d316f4ccc5a06132` |
| `LICENSE.MIT` | GitHub `hendrycks/math` master LICENSE 原样拷贝（上游权威许可） | 见文件 |
| `hf_api_metadata.json` | HF API 元数据快照 | 见文件 |

## 数据校验（镜像时核验）

- 题数 = 500（test 全量）；字段 `problem` / `solution` / `answer` / `subject` / `level` / `unique_id` 齐全；
- level 1–5 均覆盖；`answer` 为官方 boxed 最终答案（含 318 纯数字 + 68 分数 + 表达式/区间/文本）；
- 任务全集 500/500（不抽样——500 题本身就是社区标准评测规模）。

## 许可证据链（先许可证后镜像，2026-08-21 核验）

1. **上游权威**：MATH 数据集（Hendrycks）GitHub `hendrycks/math` 根 LICENSE = **MIT License**
   （Copyright (c) 2021 Dan Hendrycks），随镜像保存为 `LICENSE.MIT`。
2. **MATH-500** 是 MATH test split 的 500 题标准子集（PRM800K/"Let's Verify Step by Step"
   评测选集，HuggingFaceH4 重建发布）；HF 卡片未填 license 字段（快照如实记录）——
   数据本体许可随上游 MATH（MIT）。此差异按 cfdquery 同款口径处理：
   上游 LICENSE 为权威来源，HF 卡片缺失如实记录不改变数据本体许可。
3. MIT 宽松许可：允许商用/再分发/修改，条件为保留版权与许可声明——随镜像保存 LICENSE 即满足。

结论：`license_status: confirmed-repo`（MIT，权威链经上游 hendrycks/math）成立，镜像放行。

## 判分口径声明

- 提示 = 官方 `problem` 原文 + 要求最终答案置于 `\boxed{...}`（标准 MATH 提示协议）；
- `solution`（官方 CoT）不进提示面、不进判分（防止模型抄写参考推导的 boxed 之外的中间量）；
- 判分 = `\boxed{}` 内容抽取（最后出现、花括号配平）→ 归一化（去 `\left/\right`/`$`/空白、
  `\dfrac→\frac`）→ 数值化优先（双方可解析为数则数值比；`a/b` 分数叉乘比），
  否则归一化字符串精确匹配（greedy exact match 口径，不做符号等价）；
- gate = boxed 可抽取（或退化为 #### 数值可解析且参考可数值化）。

## 已知上游数据特性（如实记录）

- 182/500 答案为非纯数字（表达式/区间/文本如 `\text{Evelyn}`）——归一化字符串匹配为主判路径；
- 与 gsm8k 同属「公共可比层」：MATH 已广泛入训练语料，仅作可比基线，不用于版本选型。

## 重取方式（离线重跑不需要网络，仅更新数据时用）

```bash
# datasets-server /rows 分页（dataset=HuggingFaceH4/MATH-500, split=test）
```
