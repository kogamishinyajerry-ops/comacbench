# HumanEval+（EvalPlus）镜像溯源（PROVENANCE）

> assets_revision: `humanevalplus@release_v0.1.10-noextreme_20260821`
> 镜像日期: 2026-08-21 · 镜像执行: batch-3 第二波会话（dev 终端）
> **换源裁定**：HF `evalplus/humanevalplus` 卡片版 → 官方 GitHub release（见下）

## 镜像内容

| 文件 | 来源 | sha256 |
| --- | --- | --- |
| `HumanEvalPlus-NoExtreme.jsonl` | 官方 release `evalplus/humanevalplus_release` v0.1.10 NoExtreme 变体（GitHub Releases 直连，md5 413980104ee0339c147ac09653cee3db） | `3c5aa88735e442f327030f7097f9443ee173419e0db2a75b1c12730415398e88` |
| `LICENSE.Apache-2.0` | GitHub `evalplus/evalplus` master LICENSE 原样拷贝 | 见文件 |
| `hf_api_metadata.json` | HF API 元数据快照（历史核验证据，卡片版已弃用） | 见文件 |
| `oracle/humaneval_plus_<NNN>.py` | 原版 prompt + release canonical_solution（生成器产物，判分器自检源） | 逐文件 sha256 于任务 YAML |

## 两次数据源裁定（2026-08-21，如实记录）

1. **HF 卡片版弃用**：初镜 HF `evalplus/humanevalplus`（卡片 license=apache-2.0）存在
   转换缺陷——HumanEval/32 断言行 `_poly(*candidate(*inp), inp)` 对任何返回 float 的
   实现均 TypeError；官方 release 同题为 `math.fabs(poly(coeffs, solution)) < 1e-4`
   （语义正确）。两版结构整体不同（逐行对比 0/164 一致），HF 版为内联转换稿。
   官方工具链 `evalplus/data/utils.py` 指向 GitHub Releases 为权威数据源。
2. **NoExtreme 变体采用**：全量版极端输入题（如 /15 `string_sequence(1e6)` 单输出
   6.9M 字符、/83 百万位大整数）使冻结 gold 与任务 YAML 膨胀至 ~300MB 且执行超时；
   官方 NoExtreme 变体即为此类病态输入的裁剪版（plus_input 尺寸回落至 ≤194KB/题）。
   本 harness 口径 = **HumanEval+ NoExtreme**（registry/报告如实标注）。

## 数据校验（镜像时核验）

- 题数 = 164（与 HumanEval 原版 task_id 一一对应，entry_point 164/164 一致）；
- 字段 `base_input`/`plus_input`/`atol`/`canonical_solution`/`test`/`entry_point` 齐全；
- 每题输入数 12–1100（NoExtreme 后平均 ~758）；
- prompt 复用**原版 HumanEval**（163/164 逐字同，/115 仅 import 位置差异——统一取原版，
  使 plus 与原版分差纯粹来自测试加强）。

## 许可证据链（先许可证后镜像，2026-08-21 核验）

1. **官方 release 仓库** `evalplus/humanevalplus_release`（工具链 `evalplus/evalplus`
   `get_dataset_metadata` 指定）：Apache-2.0（GitHub `evalplus/evalplus` 根 LICENSE 随镜像保存）。
2. HF 数据集卡 `evalplus/humanevalplus` license=apache-2.0（快照留档）。
3. 复用的原版 prompt 为 MIT（openai/human-eval，第一波已核验）。
4. Apache-2.0 + MIT 均为宽松许可：再分发保留许可声明即满足（随镜像保存 LICENSE）。

结论：`license_status: confirmed-split`（数据 Apache-2.0 / prompt MIT）成立，镜像放行。

## 判分口径（官方 EvalPlus 语义复刻，活体 GT）

- 提示 = 原版 HumanEval prompt + 同款补全指令（与 humaneval.python 基准逐字一致）；
- case 1..N：release `test`（原版 check 断言）AST 拆分逐条（candidate 改名 entry_point）；
- case N+1：base_input + plus_input 全量输入**活体 GT** 比对——canonical（可信侧，
  源码内嵌仅数百字节）判分时现场执行计算期望，候选与 GT 双侧 `_nb` 归一
  （tuple/set 打标记保类型、numpy→内置）后 `==` 比对；不等且数值型则
  `np.allclose(rtol=1e-7, atol=官方逐题 atol)`；
- inf/nan 输入以 `float('inf')` 构造式安全嵌入（裸 inf 字面量是 NameError）；
- `sys.set_int_max_str_digits(0)`：/83 等大整数题（Python 3.12 默认 4300 位限制）；
- oracle 自检 = prompt+canonical 作被测代码：**164/164 pass@1，确定性 164/164**。

## 重取方式（离线重跑不需要网络，仅更新数据时用）

```bash
curl -L -o HumanEvalPlus-NoExtreme.jsonl.gz \
  https://github.com/evalplus/humanevalplus_release/releases/download/v0.1.10/HumanEvalPlus-NoExtreme.jsonl.gz
```
