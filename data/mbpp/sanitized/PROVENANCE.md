# MBPP (sanitized test) 编程镜像溯源（PROVENANCE）

> assets_revision: `mbpp@sanitized_test+hf_20260821`
> 镜像日期: 2026-08-21 · 镜像执行: 数学/编程扩充会话（dev 终端）

## 镜像内容

| 文件 | 来源 | sha256 |
| --- | --- | --- |
| `mbpp_sanitized_test.jsonl` | HF `google-research-datasets/mbpp`（config=sanitized, split=test，datasets-server /rows 分页拉取） | `ffdc47903bc8a2bcf733b2566090f1fb2324f4f1a139b1a38b4b3e3b767da8c0` |
| `hf_api_metadata.json` | HF API 数据集元数据快照（cardData.license 证据） | 见文件 |
| `hf_dataset_card.md` | HF 数据集卡 README 快照 | 见文件 |

## 数据校验（镜像时核验）

- 题数 = 257（sanitized 配置 test split 全量；task_id 11–479，原库清洗后保留集）；
- 每题字段 `prompt` / `code`（参考实现）/ `test_list`（3–5 条断言）/ `test_imports` 全部存在；
  `test_setup_code` 在 sanitized test 中无内容（0/257 非空）；
- `test_imports` 非空 13 题（math/functools 等），拼装判分脚本时置于顶部（oracle 自检覆盖）；
- 官方提示协议：题面 = `prompt` + `test_list[0]` 作示例（官方 MBPP 评测口径），判分层隐藏 `test_list` 全量。

## 许可证据链（先许可证后镜像，2026-08-21 核验）

1. **HF 数据集卡** `google-research-datasets/mbpp`：license 字段 = `cc-by-4.0`
   （快照 `hf_dataset_card.md` + `hf_api_metadata.json` cardData.license 双证）。
2. CC BY 4.0：允许商用/再分发/修改，条件为署名（BY）——本 PROVENANCE 与 registry/license-notes.md
   记录来源与作者（Google Research）即履行归属义务；再分发随附本溯源文件。
3. GitHub 镜像库 `google-research-datasets/mbpp` README 亦指向同一数据许可口径。

结论：`license_status: confirmed-dataset`（CC BY 4.0）成立，镜像放行。

## 隐藏测试与提示面（判分口径声明）

- 模型可见：`prompt`（任务描述原文）+ `test_list[0]`（官方口径的示例测试）+ 函数名约定
  （参考实现的顶层函数名——测试断言按官方代码调用该名，模型须同名交付）；
- 判分隐藏：`test_list` 全量断言（含可见示例条——通过可见示例是最低要求）；
- `code`（参考实现）仅作 oracle 判分器自检源（不进提示面）。

## 已知上游数据特性（如实记录）

- 参考实现风格不一（部分顶层代码直接执行 print）；oracle 自检以「隐藏测试全过」为准，
  参考实现不满足自家测试的任务会在 oracle 阶段暴露并如实处置（排除+记录原因）；
- 与 humaneval 同属「公共可比层」：大概率已入训练语料，仅作横向可比基线。

## 重取方式（离线重跑不需要网络，仅更新数据时用）

```bash
# datasets-server /rows 分页（dataset=google-research-datasets/mbpp, config=sanitized, split=test）
```
