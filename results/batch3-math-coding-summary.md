# Batch-3 数学与编程公共可比层结果（2026-08-21）

> 范围：GSM8K（数学 QA）/ HumanEval / MBPP（编程 code_exec）三基准接入与双模型基线。
> 运行环境：dev 终端（macOS, Python 3.12）；provider 密钥经 Keychain 注入不落盘。
> 全部结果可用各目录 run_manifest.json 内 rerun_command 离线复算（oracle/stub 无需网络）。

## 1. 接入概览

| registry_id | 任务数 | 判分 | oracle 自检 | stub 地板 |
| --- | --- | --- | --- | --- |
| gsm8k.math_reasoning | 250（1319 题 RNG seed=20260821 抽样） | math_answer 数值精确匹配 | 250/250 (1.0000) | accuracy 0.0000 |
| humaneval.python | 164（全量） | unit_tests 隐藏断言逐 case + pass@1 | 164/164 (1.0000) | pass@1 0 |
| mbpp.sanitized | 257（sanitized test 全量） | 同上 | 257/257 (1.0000) | pass@1 0 |

判分器自检口径：oracle 必须 100%——三基准均满足，判分管线（gate/抽取/AST 拆分/拼装执行/确定性双跑）验证通过。

## 2. 模型基线总表

| 基准 | 指标 | GLM-4.6 | MiniMax-M3 | 说明 |
| --- | --- | --- | --- | --- |
| gsm8k（250 题） | accuracy | **0.9600** (240/250) | **0.9720** (243/250) | gate 双满（数值全部可解析） |
| humaneval（164 题） | pass@1 | **0.9756** (160/164) | **0.9817** (161/164) | GLM 1 题 code_not_executable；其余确定性双满 |
| mbpp（257 题） | pass@1 | **0.9416** (242/257) | **0.9455** (243/257) | 各 1 题 code_not_executable（M3 为 mbpp_430：模型把断言写进解答且公式错） |

> 公共可比层结论边界（scoring/README.md §5）：三基准均为公开题，大概率已入两家训练语料；
> 分数只用于横向可比与能力画像，**不用于版本选型**。近满分的差距主要是题面泄漏后残余失误。

## 3. 与既有维度的画像拼图（v0.1 九维度对照）

| 维度 | 已有基准 | 今晚新增 | 对照结论 |
| --- | --- | --- | --- |
| knowledge | cfdquery GLM 0.8667 / M3 0.8111 | gsm8k GLM 0.9600 / M3 0.9720 | 通识数学 > 领域 CFD 知识，两家一致 |
| coding | scicode GLM 0.477 / M3（gate 42/52）；cfdcode GLM 0.586 / M3 0.937 | humaneval/mbpp 双双 ~0.95-0.98 | 公开基础编程题近饱和；科学代码（scicode）仍是分水岭——差距 ~2 倍，印证「入语料题 vs 真实工程编程」的层级 |
| 边界观察 | superwing/hilift LLM physics ~0.05-0.19 | — | 数值回归类 LLM 依旧不可行（与 ML 正例差一个数量级） |

## 4. 判分口径细节

- **gsm8k**：模型自由 CoT，抽取最终数（`####` 优先 → `answer is`/`答案` → 全文末数），
  与参考 `####` 数值比对（rel_tol=1e-6 等效精确，抗 `$`/千分位逗号/百分号字面差）；
  gate = 最终数可解析（抽不出数 = missing_output）。
- **humaneval**：官方 `check(candidate)` 块 AST 拆分为逐断言 case（157 题 split_pure + 4 题
  split 含 helper 前置 + 3 题 fallback 整块——32/38/50 循环断言无顶层 assert），
  `candidate` AST 改名为 entry_point 零字符串误伤；提示 = 官方 prompt 原文（docstring 含
  doctest 属公开提示面），隐藏层 = 拆分后全量断言；physics = case 通过率，另报 pass@1。
- **mbpp**：官方提示口径（题面 + test_list[0] 示例 + 参考实现函数名约定），隐藏层 =
  test_list 全量（含可见示例条）；13 题 test_imports 置顶拼装。
- **确定性**（两基准）：同代码两次独立执行，逐 case 通过模式一致 = 1.0。
- **沙箱**：静态 AST 审查 + `python -E -s` 隔离解释器 + 独立 cwd + 墙钟超时
  （dev 层强度，如实声明；非 OS 级隔离）。

## 5. 目录

```
results/gsm8k.math_reasoning/2026-08-21/{oracle,stub,glm-4.6,minimax-m3}/
results/humaneval.python/2026-08-21/{oracle,stub,glm-4.6,minimax-m3}/
results/mbpp.sanitized/2026-08-21/{oracle,stub,glm-4.6,minimax-m3}/
```

每目录含 result_<task_id>.json ×N + summary.md + run_manifest.json（含 rerun_command）。
