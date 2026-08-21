# Batch-3 第二波结果：MATH-500 + HumanEval+/MBPP+（2026-08-21）

> 范围：竞赛数学（更硬一档）+ EvalPlus 加强测试编程（同提示纯测试升级）。
> 判分口径与数据源裁定详见各 PROVENANCE.md；所有结果可离线复算（run_manifest.rerun_command）。

## 1. 接入概览

| registry_id | 任务数 | 判分 | oracle 自检 | stub 地板 |
| --- | --- | --- | --- | --- |
| math500.math_reasoning | 500（全量） | \boxed{} 抽取 → 归一化（\text 解包/度数标记/分数宏）→ 数值化优先/字符串精确；#### 文本通道回退 | 500/500 (1.0000) | acc ~0（368/500 gate——非数值参考题 stub 无 boxed） |
| humaneval.python_plus | 164（官方 release NoExtreme） | 断言拆分 + base/plus 全量输入活体 GT（双侧 _nb 归一 + allclose） | 164/164 (1.0000) | pass@1 0 |
| mbpp.sanitized_plus | 222（∩sanitized，2 题官方缺陷排除） | 官方 assertion 逐条 + 活体 GT 批量 | 222/222 (1.0000) | pass@1 0 |

## 2. 数据源裁定记录（今晚两次，均有实证）

1. **EvalPlus HF 卡片版弃用**：HF `evalplus/humanevalplus` 的 HumanEval/32 断言行
   `_poly(*candidate(*inp), inp)` 对任何 float 返回实现均 TypeError；官方 release 同题
   语义正确（`math.fabs(poly(coeffs, solution)) < 1e-4`）；两版 0/164 一致（结构不同）。
   → 换官方 GitHub Releases（工具链权威源）。
2. **NoExtreme 变体**：全量版极端输入（/15 单输出 6.9M 字符、/83 百万位整数）使冻结
   gold/YAML 膨胀 ~300MB 且超时 → 官方 NoExtreme（plus_input ≤194KB/题），口径如实标注。
3. **MBPP+ 上游缺陷处置**：124/252 官方把复数输入字符串化与数字 GT 系统性不兼容
   （排除，生成器记录）；106 canonical 对 list 参数 TypeError（GT 覆写原版 code）；
   120 等 assertion 用 math.isclose 未声明 import（test_imports 前置对齐官方 harness）。
4. **活体 GT 判分架构**：canonical（可信侧，数百字节）判分时现场执行计算期望，
   双侧 `_nb` 归一（tuple/set 打标记保类型、numpy→内置、inf/nan 构造式嵌入）——
   与官方运行时比对同构，天然规避巨输出存储。

## 3. 模型基线总表

| 基准 | 指标 | GLM-4.6 | MiniMax-M3 | 对照（第一波） |
| --- | --- | --- | --- | --- |
| math500（500 题） | accuracy | 进行中 | **0.9020**（451/500，gate 497/500） | gsm8k 0.9600 / 0.9720（-7pp 难度梯度） |
| humaneval_plus（164 题） | pass@1 | 进行中 | **0.9268**（152/164，gate 164/164） | humaneval 0.9817（**-5.5pp 测试敏感度**） |
| mbpp_plus（222 题） | pass@1 | 进行中 | **0.8198**（182/222，gate 222/222） | mbpp 0.9455（**-12.6pp 测试敏感度**） |

> 同提示纯测试升级：plus 与原版分差 = 模型对隐藏测试强化的敏感度（方向性指标不受
> 语料泄漏影响）；math500 与 gsm8k 分差 = 难度梯度区分度。

## 4. 判分器工程记录（本次会话修复）

- gold 预计算 stdout 截断（20000 字符上限）→ 改写文件回传；
- Python 3.12 大整数 4300 位限制（HE+/83）三处解除；
- tuple/set JSON 摊平导致 `tuple == list` 恒 False → 标记保类型 + 双侧同款归一；
- MATH-500 通道容错：#### 文本回退（p-q/Evelyn/90° 类正确答案不再误判 gate 0）；
- inf/nan 输入裸字面量 NameError → `float('inf')` 构造式。

## 5. 目录

```
results/math500.math_reasoning/2026-08-21/{oracle,stub,glm-4.6,minimax-m3}/
results/humaneval.python_plus/2026-08-21/{oracle,stub,glm-4.6,minimax-m3}/
results/mbpp.sanitized_plus/2026-08-21/{oracle,stub,glm-4.6,minimax-m3}/
```
