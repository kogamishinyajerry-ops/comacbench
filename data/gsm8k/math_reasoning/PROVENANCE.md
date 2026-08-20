# GSM8K 数学推理镜像溯源（PROVENANCE）

> assets_revision: `gsm8k@openai-master+test.jsonl_20260821`
> 镜像日期: 2026-08-21 · 镜像执行: 数学/编程扩充会话（dev 终端）

## 镜像内容

| 文件 | 来源 | sha256 |
| --- | --- | --- |
| `test.jsonl` | GitHub `openai/grade-school-math` master `grade_school_math/data/test.jsonl`（raw 直连） | `3730d312f6e3440559ace48831e51066acaca737f6eabec99bccb9e4b3c39d14` |
| `LICENSE.MIT` | 同仓库根 LICENSE 原样拷贝 | 见文件 |

## 数据校验（镜像时核验）

- 题数 = 1319（test split 全量）；
- 每题字段 `question` / `answer`（CoT 解答），`answer` 末行 `#### <数字>` 全部存在（1319/1319）；
- 参考答案均为有限数（整数或小数，无单位后缀残留——按官方抽取规则取 `####` 后首 token）；
- 任务子集：确定性 RNG（seed=20260821，见 gen_tasks_gsm8k.py）从 1319 题抽 250 题，选择逻辑落盘可复现。

## 许可证据链（先许可证后镜像，2026-08-21 核验）

1. **GitHub 仓库** `openai/grade-school-math`：根目录 `LICENSE` = **MIT License**（Copyright (c) OpenAI），随镜像保存为 `LICENSE.MIT`。
2. MIT 为 OSI 认可宽松许可：允许商用/再分发/修改，条件仅保留版权与许可声明——随镜像保存 LICENSE 即满足。
3. HF 官方镜像 `openai/gsm8k` 数据内容与本镜像同源（GitHub 为主源）。

结论：`license_status: confirmed-repo`（MIT）成立，镜像放行。

## 已知上游数据特性（如实记录）

- `question` 含 Unicode 弯引号（\u2019 等）；本 harness 题面读写一律 `newline=""` 忠实保留原始字节；
- `answer` 内 `<<..>>` 为官方计算器标注，判分只取 `####` 后参考数，不使用 CoT 文本；
- 与 cfdquery 同属「公共可比层」：题目大概率已入训练语料，仅作横向可比基线，不用于版本选型（registry risks 同步标注）。

## 重取方式（离线重跑不需要网络，仅更新数据时用）

```bash
curl -L -o test.jsonl \
  https://raw.githubusercontent.com/openai/grade-school-math/master/grade_school_math/data/test.jsonl
```
