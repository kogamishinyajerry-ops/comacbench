# CFDQuery 数据镜像溯源（PROVENANCE）

> assets_revision: `cfdquery@3b46d30+kaggle_v4`（GitHub commit 短哈希 + Kaggle 数据集版本号）
> 镜像日期: 2026-08-19 · 镜像执行: M1 会话（dev 终端）

## 镜像内容

| 文件 | 来源 | sha256 |
| --- | --- | --- |
| `CFDQuery.json` | Kaggle `nithinsekhar/cfdquery` v4（经公开下载端点） | `cad5f941aa0affa77ad2873df40aac2de2a52a708d9a098294afbbb9b521137a` |
| `LICENSE.BSD-3` | GitHub `NREL-Theseus/cfdllmbench` @ `3b46d30` LICENSE 原样拷贝 | 见文件 |
| `upstream_llms.py.reference` | 同仓库 `CFDQuery/llms.py` 原样拷贝（仅作解析逻辑参考，不参与本 harness 运行） | 见文件 |

## 数据校验（镜像时核验）

- 题数 = 90（question_index 1–90 连续无缺）；
- 每题 4 选项（option_index 1–4）；
- correct_option_index 分布：{1: 30, 2: 27, 3: 19, 4: 14}（无答案缺失）；
- 文件 sha256 已锁定于上表，评测 run_manifest 会再校验。

## 已知上游数据缺陷（如实保留，不修复）

- q074 选项 LaTeX `$\rho$` 在源 JSON 中为单反斜杠，JSON 转义解析后成为
  「CR(0x0D) + "ho"」控制字符序列；13 道另含真实多行换行（JSON `\n`）。
  本 harness 忠实保留原始字节（题面读写一律 `newline=""` 禁止换行翻译），
  模型看到的题面与上游 llms.py 直接读 JSON 的行为一致。


## 许可证据链（先许可证后镜像，2026-08-19 核验）

1. **GitHub 仓库** `NREL-Theseus/cfdllmbench` @ commit `3b46d30629ae27588c3ddc8cf6e8c7d4494cb43f`（2026-06-09）：
   根目录 `LICENSE` = **BSD 3-Clause License**（Copyright 2025, Alliance for Sustainable Energy, LLC and Rensselaer Polytechnic Institute）。
2. **论文权威声明**（arXiv:2509.20374，JMLR DMLR 2026，OpenReview `kTcH1MnkjY`）原文：
   > "…problems in our benchmark were collected from open, publicly available sources or were authored specifically for this benchmark. Accordingly, CFDLLMBench is released under the terms of the BSD 3-Clause License, making it free to use, modify, and redistribute, including for commercial purposes, provided that the license conditions are met."
3. **Kaggle 托管副本** `nithinsekhar/cfdquery` v4：页面 license 徽标为 "Unknown"（上传者未选择），仓库 README 指定其为 CFDQuery 数据集官方托管位置。**裁定依据**：作者在 LICENSE 文件与论文中对 benchmark 全部内容（含题目数据）的 BSD-3 声明构成权威许可来源；Kaggle 徽标缺失不改变数据本体的许可。此差异已如实记录于 `registry/license-notes.md`。

结论：`license_status: confirmed-repo`（BSD-3-Clause）成立，镜像放行。BSD-3 归属条件（再分发保留版权声明）通过随镜像保存的 `LICENSE.BSD-3` 满足。

## 重取方式（离线重跑不需要网络，仅更新数据时用）

```bash
curl -sL "https://www.kaggle.com/api/v1/datasets/download/nithinsekhar/cfdquery" -o cfdquery.zip
unzip -o cfdquery.zip -d extracted   # -> CFDQuery.json
shasum -a 256 extracted/CFDQuery.json  # 应 == cad5f941…137a，不同则 assets_revision 变更 -> 新评测周期
```
