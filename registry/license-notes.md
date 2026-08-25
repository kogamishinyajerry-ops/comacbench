# 许可证状态矩阵（license-notes）

> 规则：**status 不是 `confirmed-*` 的条目，其数据一律不得镜像进公司环境。**
> 每次镜像/更新源数据前，先更新本文件，再更新 `registry.yaml` 的 `license_status` 字段。两者必须一致。

| status 取值 | 含义 | 允许镜像? |
| --- | --- | --- |
| `confirmed-repo` | 仓库 LICENSE 文件已核实 | 是 |
| `confirmed-dataset` | 数据集发布页/记录许可证已核实 | 是 |
| `confirmed-split` | 代码与数据许可不同，已分别核实并拆分标注 | 是（按标注范围） |
| `needs-verification` | 许可证存在但条款/适用范围未核实 | 否 |
| `needs-per-task-audit` | 聚合仓库，组成数据许可不一，需逐任务清点 | 否（清点完成前） |
| `needs-legal-review` | 特殊许可（如 NOSA）需法务确认企业适用性 | 否（法务放行前） |
| `needs-version-lock` | 许可可接受但需锁定版本/revision 后才可信 | 否（锁定前） |
| `blocked-license-ambiguity` | 许可表述冲突或含 NC 等限制性条款待澄清 | 否 |
| `blocked-no-license` | 未见任何许可证声明 | 否 |

## 当前状态（2026-08-19）

> 注：`excluded.*` 条目（ALUE/Pre-Flight、RepoSpace、CFDBench、BlendedNet、HiLiftAeroML 全量体数据、运行常识类）已明确排除，永不镜像，故不进入本矩阵追踪。

| Registry ID | 许可证 | status | 镜像放行前必须完成的事 |
| --- | --- | --- | --- |
| cfdllm.cfdquery | BSD-3-Clause | confirmed-repo | —（2026-08-19 已镜像；核验记录：Kaggle 托管页 license 徽标为 "Unknown"，但仓库 LICENSE + 论文 arXiv:2509.20374 明确声明整个 benchmark 含题目数据为 BSD-3-Clause，证据链见 data/cfdllm/cfdquery/PROVENANCE.md） |
| cfdllm.cfdcode | BSD-3-Clause | confirmed-repo | — |
| cfdllm.foam_basic | BSD-3-Clause | confirmed-repo | — |
| aeroengqa.gold | CC BY 4.0（Zenodo 10.5281/zenodo.14215677 v1.0，license 字段已核实） | confirmed-dataset | —（2026-08-19 核验通过并完成镜像，md5 全核验，PROVENANCE 见 data/aeroengqa/gold/；BY 归属义务：再分发须署名 AIAA-2025 论文作者） |
| scicode.physics | Apache-2.0 | confirmed-repo | — |
| engdesign.open | 题库 JSON MIT（HF README）；逐任务软件依赖已清点（2026-08-19：101 任务中专有软件 20+HDL 10，收窄子集 28；官方评测脚本未发布，集成 blocked） | confirmed-split（仅题库 JSON 镜像；评测基础设施缺失） | 集成解阻：官方发布 eval 脚本或裁定自建判分口径；详见 data/engdesign/open/PROVENANCE.md |
| aviary.transport_mission | Apache-2.0（Aviary 本体） | confirmed-repo | 自建任务产物按本仓库规范另行标注 |
| superwing.coeff_lite | CC BY-SA 4.0 | confirmed-dataset | 注意 SA 传染性：派生评测子集需同许可发布策略 |
| openvsp.geometry_aero | NASA Open Source Agreement 1.3 | needs-legal-review | NOSA 企业镜像法务确认 |
| pycycle.engine_cycle | Apache-2.0 | confirmed-repo | — |
| cadgen.local_validity | 代码 Apache-2.0 / 输入 ODC-BY | confirmed-split | 私有 GT 部分不纳入，声明清楚本地分数边界 |
| simjeb.structure | ODC Attribution 类 | confirmed-dataset | 核对具体 ODC 变体条款 |
| gtm.transport_control | GTM 待核对 / JSBSim LGPL-2.1 | needs-verification | GTM 仓库许可核实；JSBSim 注意 LGPL 动态链接边界 |
| mechvqa.public_eval | Apache-2.0 | confirmed-repo | 固定公开评测版本 |
| nasa_tmr.verification | NASA 公开发布 | needs-verification | 逐案例核对发布条款 |
| crm_dpw_hlpw.coarse | NASA/AIAA Workshop 公开发布 | needs-version-lock | 锁定 Workshop 届次 + geometry revision，排除已归档旧几何 |
| hilift_aeroml.lite | CC BY 4.0 | confirmed-dataset | — |
| bscw.aeroelastic | NASA 公开发布 | needs-verification | 逐案例核对 |
| cadbench.cadquery | 代码 MIT / 数据各异 | needs-per-task-audit | 建立数据级许可证矩阵 |
| afbench.airfoil | MIT 与 Apache-2.0 表述冲突 | blocked-license-ambiguity | 向作者澄清 |
| designqa.fsae | 未见 LICENSE | blocked-no-license | 许可证出现前只借鉴任务设计，不镜像数据 |
| aircraftverse.selective | 待核对 | needs-verification | 核对发布许可 |
| openconcept.hybrid_electric | 待核对 | needs-verification | 核对 mdolab 许可 |
| pdebench.compressive_ns | 待核对 | needs-verification | 核对仓库许可 |
| camb.selective | 数据 CC BY-NC-SA 4.0（表述有差异） | blocked-license-ambiguity | 法务确认 NC 条款公司内部边界 + 澄清仓库表述差异 |
| airfrans.level1 | ODbL-1.0 | confirmed-dataset | 注意 ODbL 共享要求 |
| gsm8k.math_reasoning | MIT（GitHub openai/grade-school-math 根 LICENSE） | confirmed-repo | —（2026-08-21 已镜像；test.jsonl 1319 题全量 + LICENSE.MIT 随镜像，证据链见 data/gsm8k/math_reasoning/PROVENANCE.md） |
| humaneval.python | MIT（GitHub openai/human-eval 根 LICENSE + HF 数据集卡 license=mit 双证） | confirmed-repo | —（2026-08-21 已镜像；HumanEval.jsonl 164 题全量，PROVENANCE 见 data/humaneval/python/） |
| mbpp.sanitized | CC BY 4.0（HF google-research-datasets/mbpp 数据集卡 cardData.license=cc-by-4.0 + API 元数据双证） | confirmed-dataset | —（2026-08-21 已镜像；sanitized test 257 题全量；BY 归属义务：再分发须署名 Google Research，PROVENANCE 随附，见 data/mbpp/sanitized/） |
| math500.math_reasoning | MIT（权威链：上游 hendrycks/math 根 LICENSE；HF HuggingFaceH4/MATH-500 卡片未填 license 已如实记录，按 cfdquery 同款上游权威口径） | confirmed-repo | —（2026-08-21 已镜像；500 题全量 + LICENSE.MIT 随镜像，证据链见 data/math500/math_reasoning/PROVENANCE.md） |
| humaneval.python_plus | Apache-2.0（官方 GitHub release v0.1.10 NoExtreme，工具链权威源）/ MIT（复用的原版 prompt） | confirmed-split | —（2026-08-21 镜像；HF 卡片版实证有断言转换缺陷已弃用并留档；换源裁定见 data/humaneval/python_plus/PROVENANCE.md） |
| mbpp.sanitized_plus | Apache-2.0（官方 GitHub release v0.2.0 NoExtreme）/ CC BY 4.0（上游 MBPP 本体） | confirmed-dataset | —（2026-08-21 镜像；官方 release 权威源；2 题输入-GT 不兼容缺陷排除 + 1 题 GT 覆写原版，处置见 data/mbpp/sanitized_plus/PROVENANCE.md） |
| cadbench_seldon.hard | CC BY 4.0（HF Seldon-Technologies/CADBench-Hard 卡片明示：题面/元数据/Seldon 自建参考工件） | confirmed-dataset | —（2026-08-24 镜像公开子集 43 题 task.md+answer.f3d+manifest，answer sha256 与官方 manifest 43/43 逐字节一致；BY 归属义务：再分发须署名 Seldon Technologies；Fusion 商标归 Autodesk；verifier/沙箱/种子文档不随数据集发布，集成三重阻塞，PROVENANCE 见 data/cadbench-seldon/hard/） |
| cadbench_seldon.sketch_lite | 改编 5 题：CC BY 4.0（上游同上；BY 署名衍生，协议由 Fusion GUI 改为 cadquery 脚本制，改编边界在 PROVENANCE §1 如实标注）/ 自建 10 题：self-built | confirmed-adapted-ccby4 + confirmed-selfbuilt | —（2026-08-25 窄路 A 落地；GT 一手源=题面几何规格而非 answer.f3d；改编题 license_provenance 逐题标注来源 task_id） |

## 许可证巡检节奏

- 每次源库版本升级（registry 中 `assets_revision` 变更）时重新核对一次；
- 每季度全量巡检一次；
- 发现变更立即将对应条目降级为 `needs-verification` 并冻结该基准的新评测，直到重新确认。
