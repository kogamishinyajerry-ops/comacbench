# M1 总结报告（2026-08-19）

> **运行环境**：`dev` 终端（外网开发机：OpenFOAM + FoamAgent、Python 3.12.13、pip 直连；无 Fluent/StarCCM）。
> 本报告所有结论均在 dev 层产出；registry/env 层级标注见 env-matrix.md §0。

## 1. Registry 状态变化

| registry_id | 之前 | 之后 | 依据 |
| --- | --- | --- | --- |
| cfdllm.cfdquery | proposed | **integrated** | 数据镜像（BSD-3 核验）→ staged → qa_grounded adapter 跑通 + 三份基线落盘（stub / GLM-4.6 / MiniMax-M3，见 §2.4） |
| aeroengqa.gold | proposed（needs-verification） | **integrated**（M1 收尾会话） | Zenodo 许可核验（CC BY 4.0）→ 镜像（80 题权威 JSON + md5 全核验）→ staged → free_text 四层判分跑通 + 三份基线落盘（见 §3） |

## 2. cfdllm.cfdquery：管线与基线

### 2.1 数据镜像（先许可证后镜像）

- 源：GitHub `NREL-Theseus/cfdllmbench` @ `3b46d30`（LICENSE=BSD-3-Clause）+ Kaggle `nithinsekhar/cfdquery` v4（数据托管副本）；
- 许可证据链：仓库 LICENSE + 论文 arXiv:2509.20374 明确声明整个 benchmark（含题目）以 BSD-3-Clause 发布；Kaggle 页 license 徽标 "Unknown" 的差异已记录于 `data/cfdllm/cfdquery/PROVENANCE.md` 与 license-notes.md；
- `assets_revision = cfdquery@3b46d30+kaggle_v4`，数据 sha256 `cad5f941…137a` 锁定进每个任务 YAML，运行时逐题校验；
- 数据校验：90 题（index 1–90 连续）、每题 4 选项、答案分布 {1:30, 2:27, 3:19, 4:14}；已知上游缺陷如实保留（q074 的坏 `\rho` 转义、13 题多行题面），题面读写一律 `newline=""`。

### 2.2 Harness 落地物

- `runners/common.py`：任务 YAML 契约校验、environment_digest（python+平台+runner 源码+资产摘要）、标准 result.json 构造、run_manifest（seed/provider/摘要/重跑命令/git commit）、gate 类分布统计；
- `runners/providers.py`：模型调用层（stub / oracle / openai_compat 占位，环境变量 BM_API_BASE/BM_API_KEY/BM_MODEL）——adapter 不感知模型 CLI，API 到位只加 provider 不改判分；
- `runners/qa_grounded.py`：qa_grounded adapter（gate 先于子分：答案缺失/不可解析 = missing_output = gate 0；客观层选项精确匹配；解析规则与上游一致 strict→tolerant）；
- `runners/gen_tasks_cfdquery.py`：镜像 → 90 个任务 YAML + 题面 .md（幂等，--check 可离线校验）；
- `tasks/cfdllm.cfdquery/`：90 个任务 YAML（严格套 contracts/task.example.yaml）。

### 2.3 基线（内置固定答案冒烟，模型 API 未到位）

**判分器自检（oracle）**：90/90 = 100%（gate 90 通过、客观层全对）——判分管线正确性验证。

**stub 冒烟基线**（确定性伪答案，seed=0）：

| 指标 | 值 |
| --- | --- |
| ValidityGate 通过 | **90/90（失败率 0%）** |
| gate 失败原因分布 | 无 |
| 客观层正确 | 25/90（accuracy 0.2778，均匀随机期望 0.25，符合预期） |
| 子分适用性 | physics=N/A（无证据/拒答层）、objective=N/A（并入 requirements）、robustness=N/A（样本=1） |
| 计分 | score = gate × 1.0×requirements（权重经任务 YAML 覆写——契约机制，非静默改分） |

**可复现性验证**：同命令重跑 90 个 result.json 逐字节一致（0 差异文件）；seed、assets sha256、environment_digest、重跑命令全部落盘 `run_manifest.json`。

**一条可复制重跑命令**（出同样结果，离线、无 API）：

```bash
cd /Users/Zhuanz/projects/jerry-personal/JerryDSH/benchmarks && python3 -m runners.qa_grounded --tasks tasks/cfdllm.cfdquery --out results/cfdllm.cfdquery/2026-08-19/stub --provider stub --seed 0
```

### 2.4 真实模型基线（用户提供环境变量：GLM + MiniMax）

模型接入方式：`providers.py` 命名预设（glm / minimax，OpenAI 兼容 chat/completions），key 从环境变量注入（本机由 Keychain 提供，绝不落盘）。推理模型差异处理（2026-08-19 实测）：

- GLM-4.6：思考在 `reasoning_content`，答案在 `content`；个别题思考超长耗尽 completion 预算（`finish_reason=length`、content 空）→ 请求体带 `thinking.type=enabled` + `max_tokens=16384`，解析失败升级为 `thinking.type=disabled` 粘性重试；
- MiniMax-M3：思考内联在 `content` 的 `<think>…</think>`（解析前剥离）；思考可超 16k token → `max_tokens=32768`，同样支持 `thinking.type=disabled` 升级。

**MiniMax-M3 基线（results/cfdllm.cfdquery/2026-08-19/minimax-m3/）**：

| 指标 | 值 |
| --- | --- |
| ValidityGate | **90/90 通过（失败率 0%）** |
| 客观层正确 | **73/90 = 0.8111** |
| 升级重试（关思考） | 2/90 |
| 单题延迟 | median 9s / p90 101s / max 237s（API 总时长约 48 min） |
| 答错 17 题 | q002 q003 q005 q006 q012 q016 q028 q030 q046 q051 q054 q055 q062 q071 q081 q084 q085 |

**GLM-4.6 基线（results/cfdllm.cfdquery/2026-08-19/glm-4.6/）**：

| 指标 | 值 |
| --- | --- |
| ValidityGate | **90/90 通过（失败率 0%）** |
| 客观层正确 | **78/90 = 0.8667** |
| 升级重试（关思考） | 5/90 |
| 单题延迟 | median 52s / p90 248s / max 444s（API 总时长约 133 min） |
| 答错 12 题 | q003 q005 q007 q010 q016 q019 q020 q026 q028 q030 q084 q085 |

**双模型对比**（同一判分管线、同一 assets_revision、同 seed）：

| 模型 | gate 通过 | 客观层 | 中位延迟 | 升级重试 |
| --- | --- | --- | --- | --- |
| GLM-4.6 | 90/90 | **0.8667** | 52s | 5 |
| MiniMax-M3 | 90/90 | 0.8111 | 9s | 2 |
| stub（均匀随机） | 90/90 | 0.2778 | <1s | — |

- 两模型均答错 7 题（q003 q005 q016 q028 q030 q084 q085）——这批题是难题层候选，后续 aeroengqa 接入后可对比观察是否为系统性知识盲区；
- GLM-4.6 准确率领先 5.6pp，但中位延迟是 M3 的 5.8 倍（52s vs 9s）；M3 吞吐优势明显。

**复现性注意（如实声明）**：stub/oracle 基线可离线逐字节复现；真实 API 基线受推理模型非确定性影响（temperature=0 下思考型模型仍可能给出不同答案，实测 GLM q001 两次运行答案不同），重跑同命令可复现管线与判分，但不保证逐题答案一致——这正是 scoring/README.md §7「Agent 侧采样声明次数并报告方差」要求落在后续多采样轮的原因。

**真实模型基线重跑命令**（key 经 Keychain 注入进程环境）：

```bash
cd /Users/Zhuanz/projects/jerry-personal/JerryDSH/benchmarks
export MINIMAX_M3_API_KEY=$(security find-generic-password -a "$USER" -s "minimax-m3-api-key" -w)
python3 -m runners.qa_grounded --tasks tasks/cfdllm.cfdquery --out results/cfdllm.cfdquery/2026-08-19/minimax-m3 --provider minimax --model MiniMax-M3 --seed 0
# GLM 同理：export GLM_API_KEY=$(security find-generic-password -a "$USER" -s "glm-api-key" -w) && … --out results/cfdllm.cfdquery/2026-08-19/glm-4.6 --provider glm --model glm-4.6
```

## 3. aeroengqa.gold：镜像 + 四层判分 + 基线（M1 收尾，2026-08-19 下午完成）

### 3.1 镜像（先许可证后镜像）

- Zenodo `10.5281/zenodo.14215677` v1.0（CC BY 4.0，open）6 文件全部下载并 **md5 逐文件核验通过**；
- **权威口径裁定**：评测集 = 4 个 JSON 共 **80 题**（single/multi-hop × answerable/unanswerable 各 20，与 registry/论文口径一致）；xlsx 为同题超集（含 source-url 溯源列，多出行为重复题面），仅作溯源不用于出题——JSON 与 xlsx 题面已逐一核对；
- `assets_revision = aeroengqa@zenodo.14215677-v1.0`，BY 归属（AIAA-2025 doi:10.2514/6.2025-0700）随 PROVENANCE 落盘。

### 3.2 free_text 四层判分（qa_grounded 扩展，全部规则判、无 LLM judge）

任务输出契约 `ANSWER/BASIS/CITATION` 三行结构；判分顺序 gate → 四层：

| 层 | 子分 | 规则 |
| --- | --- | --- |
| gate | — | ANSWER 行缺失/空 = `missing_output` = 0 分 |
| 客观层 | requirements（可答题） | 归一化精确 → 数值集容差(±5% rel) → token F1 部分分 |
| 拒答层 | physics | 应拒答：答了=0/正确拒答=1；应回答：误拒=0 |
| 证据层 | physics | evidence_support = 引用对 needed 段的覆盖 × 无捏造；fabrication_rate = 引用不存在段落占比（单独报告） |
| 区分层 | objective | BASIS ∈ report/computed/inferred 结构合法（数据集无参考 basis 标签；实证 11/40 参考答案为转述，逐字核验不可判真伪，只作诊断不进分——口径如实写入任务 YAML） |

权重（YAML 覆写）：可答题 {req .40, phy .35, obj .25}；不可答题 {phy .60, obj .40}（requirements N/A）。

**判分器自检（oracle）**：80/80 满分——四层管线正确性验证（含 40 题规范拒答、引用、BASIS 全对）。

### 3.3 基线（同判分管线、同 assets_revision、同 seed=0）

| 指标 | GLM-4.6 | MiniMax-M3 | stub |
| --- | --- | --- | --- |
| ValidityGate | **80/80** | **80/80** | 80/80 |
| 拒答正确率（应拒答 40 题） | **0.9250** | 0.8750 | 0.0000 |
| 误拒率（应回答 40 题） | 0.0750 | **0.0250** | 0.0000 |
| evidence_support 均值 | 0.8938 | **0.9375** | 0.8750 |
| 捏造引用题数 | **0/80** | **0/80** | 0/80 |
| 客观层均值（可答题，含 F1 部分分） | **0.6304** | 0.5851 | 0.0365 |
| 区分层（BASIS 合法率） | 0.9750 | **1.0000** | 1.0000 |
| **任务均分** | 0.8797 | **0.8852** | 0.6354 |
| 中位延迟/题 | 18s | **3s** | <1s |

- 两模型均分接近但画像不同：**GLM 事实作答与拒答判断更强，M3 引用纪律/区分声明/误拒控制更好**——九维度报告里 knowledge 维度的子能力差异可直接读出（正合 scoring/README.md §1 的设计意图）；
- 捏造引用两家均为 0：引用段落全部真实存在（证据层规则判有效）；
- 明细与每题中间量（refused/citations/basis/layer_details）见 `results/aeroengqa.gold/2026-08-19/`（README + 各 provider 子目录）。

**重跑命令**：

```bash
cd /Users/Zhuanz/projects/jerry-personal/JerryDSH/benchmarks
export MINIMAX_M3_API_KEY=$(security find-generic-password -a "$USER" -s "minimax-m3-api-key" -w)
python3 -m runners.qa_grounded --tasks tasks/aeroengqa.gold --out results/aeroengqa.gold/2026-08-19/minimax-m3 --provider minimax --model MiniMax-M3 --seed 0
# GLM 同理：export GLM_API_KEY=$(security find-generic-password -a "$USER" -s "glm-api-key" -w) && … --out results/aeroengqa.gold/2026-08-19/glm-4.6 --provider glm --model glm-4.6
# stub 离线：… --out results/aeroengqa.gold/2026-08-19/stub --provider stub --seed 0
```

## 4. 偏差与待议清单（不静默扩 scope）

1. **模型 API 已到位并出真实基线**（GLM-4.6 / MiniMax-M3，§2.4 与 §3.3）；原「停在 stub 冒烟」的边界已解除，openai_compat 通用 provider 保留备用。
2. **qa_grounded 纯 MCQ 的子分口径**：adapters/README.md 定义 physics=证据层+拒答层，但对"无证据语料任务"该层如何处理未明确（objective 有"并入"条款，physics 没有）。cfdquery 用任务 YAML 权重覆写解决（requirements=1.0，不适层权重 0 且 result.json 标注 N/A）；建议规范侧补一句明文，仍待议。
3. **registry.yaml 头部注释陈旧**：第 12 行仍写"OpenFOAM 不引入: FoamBench 暂缓"，与 foam_basic 条目（openfoam_dev，已恢复）及 env-matrix.md §0（2026-08-19 二次决策）不一致。按"以 env-matrix.md 为准"执行并记录于此，未自行改写决策注释。
4. ~~aeroengqa 后续~~ **已收尾（本会话）**：镜像 + free_text 四层判分 + 三基线，见 §3。
5. **aeroengqa 区分层口径**：数据集无参考 basis 标签且 11/40 参考答案为转述（context 不含答案关键 token），逐字核验不可判真伪——区分层按 adapters/README.md 原文取"声明结构规则抽取"（结构合法性），逐字命中降为诊断信号不进分。若后续规范想升级为逐字核验，需数据集方提供 basis 标签，进待议。
6. **multi-hop needed_citations 假定**：多跳题按数据集构造（恒 2 段 context）假定两段都被需要（needed=[1,2]）；数据集未显式标注每题所需段落。若上游补充 per-hop 段落标注，evidence 层可更细，进待议。

## 5. 本会话产出文件（2026-08-19 目录统合后布局：results/<registry_id>/<date>/<provider>/）

```
benchmarks/
├── runners/{__init__,common,providers,qa_grounded}.py + gen_tasks_{cfdquery,aeroengqa}.py
├── tasks/cfdllm.cfdquery/     90 yaml + 90 md
├── tasks/aeroengqa.gold/      80 yaml + 80 md（free_text 四层判分契约）
├── data/cfdllm/cfdquery/      镜像 + PROVENANCE + LICENSE.BSD-3 + 上游参考脚本
├── data/aeroengqa/gold/       镜像 6 文件（md5 核验）+ PROVENANCE.md
├── results/cfdllm.cfdquery/2026-08-19/{README.md, stub/, glm-4.6/, minimax-m3/}
├── results/aeroengqa.gold/2026-08-19/{README.md, stub/, glm-4.6/, minimax-m3/}
├── results/M1-summary.md（本文件）
└── registry/{registry.yaml, license-notes.md}
```

> 迁移备注：cfdquery 三份基线最初散为 `2026-08-19{-glm-4.6,-minimax-m3}` 三个兄弟目录，统合为 `<date>/<provider>/`（细节见各 run_manifest 的 extra.note）。
