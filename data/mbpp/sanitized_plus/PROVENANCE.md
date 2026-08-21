# MBPP+（EvalPlus）镜像溯源（PROVENANCE）

> assets_revision: `mbppplus@release_v0.2.0-noextreme_20260821`
> 镜像日期: 2026-08-21 · 镜像执行: batch-3 第二波会话（dev 终端）
> **换源裁定**：HF `evalplus/mbppplus` 卡片版 → 官方 GitHub release（同 humanevalplus）

## 镜像内容

| 文件 | 来源 | sha256 |
| --- | --- | --- |
| `MbppPlus-NoExtreme.jsonl` | 官方 release `evalplus/mbppplus_release` v0.2.0 NoExtreme 变体（GitHub Releases 直连，md5 85d8d7a406c0686e80353e676189bfee） | `2682a29850fb17185106b2f40e72d1ebe7091b7393c576cff71b60e83c42ed33` |
| `LICENSE.Apache-2.0` | GitHub `evalplus/evalplus` master LICENSE 原样拷贝 | 见文件 |
| `hf_api_metadata.json` | HF API 元数据快照（历史核验证据，卡片版已弃用） | 见文件 |
| `oracle/mbpp_plus_<NNN>.py` | release canonical_solution（106 题覆写为原 sanitized code，见下） | 逐文件 sha256 于任务 YAML |

## 数据源裁定（2026-08-21）

同 humanevalplus：HF 卡片版结构差异 + humanevalplus 侧已实证转换缺陷，
统一以官方 GitHub Releases 为权威源；采用 NoExtreme 变体（plus_input ≤185KB/题）。

## 任务集与上游数据缺陷处置（如实记录）

- 任务集 = MBPP+（378）∩ 本仓库 mbpp.sanitized test（257）= **222 题**
  （另 33 题 sanitized 不在 MBPP+，跳过；2 题官方数据缺陷排除，见下）；
- entry_point 与原 sanitized 函数名 224/224 全匹配（排除前交集）；
- **GT 覆写（106 add_lists）**：release canonical `test_tup + tuple(test_list)` 对
  list 型第二参数 TypeError——官方重写版缺陷；原 sanitized code
  `tuple(list(test_tup) + test_list)` 全输入可用，覆写为原版（注释于生成器）；
- **排除（124 angle_complex / 252 convert）**：官方把复数输入字符串化（'0'/'1j'），
  canonical 与原版 code 均 `cmath.phase(str)`/`cmath.polar(str)` TypeError——
  上游系统性输入-GT 不兼容，排除并在生成器 EXCLUDED_WITH_REASON 记录；
- **math 前置（120 等）**：官方 assertion 使用 `math.isclose` 但断言块未声明 import
  （evalplus 官方 harness 全局可用 math）——本 harness 统一 test_imports 前置
  `import math`（官方 harness 语义对齐）。

## 许可证据链（先许可证后镜像，2026-08-21 核验）

1. 官方 release `evalplus/mbppplus_release`（Apache-2.0，LICENSE 随镜像保存）；
2. 上游 MBPP 本体 CC BY 4.0（本仓库 mbpp.sanitized PROVENANCE 已核验）；
3. 复用的原 sanitized 提示沿用其许可核验结论。
4. 双重归属义务随两份 PROVENANCE 履行。

结论：`license_status: confirmed-dataset`（Apache-2.0；上游 CC BY 4.0）成立，镜像放行。

## 判分口径（官方 EvalPlus 语义复刻，活体 GT，与 humanevalplus 同款）

- 提示 = 原 sanitized 题面（问题 + 原 test_list[0] 示例 + 函数名约定，与
  mbpp.sanitized 逐字一致——分差纯粹来自测试加强）；
- case 1..N：官方 assertion 断言逐条（assertion 块自带 import 行进 test_imports）；
- case N+1：base+plus 全量输入活体 GT 比对（双侧 _nb 归一 + allclose 容差）；
- oracle 自检：**222/222 pass@1，确定性 222/222**。

## 重取方式（离线重跑不需要网络，仅更新数据时用）

```bash
curl -L -o MbppPlus-NoExtreme.jsonl.gz \
  https://github.com/evalplus/mbppplus_release/releases/download/v0.2.0/MbppPlus-NoExtreme.jsonl.gz
```
