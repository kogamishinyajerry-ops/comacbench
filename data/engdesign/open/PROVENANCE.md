# EngDesign-Open 逐任务许可清点与收窄子集（PROVENANCE，M4）

> assets_revision: `engdesign@hf-mit+audit_2026-08-19`
> 清点日期: 2026-08-19 · M4 会话（dev 终端）
> **性质：许可清点交付物（license-notes 门禁项）。adapter 集成 blocked，见下。**

## 数据源与许可证据链

| 项 | 事实 |
| --- | --- |
| 题库 JSON | HF `opt1zer/EngDesign`（sha256 `0bade2fa…35addb2a`，101 任务：task_id/domain/prompt/contributor/token 数） |
| 题库许可 | HF README YAML `license: mit`（prompt 集合层；已镜像 `EngDesign.json`） |
| 官网/仓库 | `agi4engineering.github.io/Eng-Design`（GitHub 仓库=网站壳，CC BY-SA 4.0 仅网站） |
| 论文 | arXiv:2509.16204：**48 任务依赖专有软件（MATLAB/Cadence 等）评测，53 任务为 EngDesign-Open（手工评测脚本）** |
| 本地审计 | 逐任务关键词扫描（18 个专有软件名）+ HDL 流程识别 + 附件自包含性核查 → `task_audit.csv` |

## 逐任务审计结果（101 任务全量）

- **专有软件命中 20**（MATLAB 12、Cadence 5、Vivado 2、Simulink 1）——与论文 48 的差集
  为 EDA/HDL/仿真流程任务（本审计单列 hdl_flow 10）及隐性依赖（论文按评测所需软件归类，
  prompt 文本不一定显式提及）；
- **附件引用 3**（RS_01/02/03，均数据内联在 prompt 中——自包含确认）；
- **收窄子集 = 28 任务**（registry 口径：目标域 机械/结构/控制 × 无专有软件 × 自包含）：
  Mechanical 7 + Structure 7 + Control 14（`subset_ids.json`）。

## adapter 集成 blocked（如实记录，进 M4 待议）

1. **官方评测基础设施未发布**：论文称 53 开源任务配有 "manually authored evaluation
   scripts" 与参考设计，但 HF（仅 3 文件：JSON/README/.gitattributes）与 GitHub（网站壳）
   均未发布评测脚本/参考设计——判分不可本地复现；
2. 自建 FEA/控制系统复算判分器 = 重大 scope 扩张（且无法保证与官方 473 评分项口径一致，
   违反公共可比层语义），按工程规则不静默扩；
3. 结论：**许可门禁完成（本文件），registry 保持 proposed + audit_done 注记**；
   恢复条件：官方发布评测脚本（或法务/验收人裁定自建判分口径）后进入 staged。

## 重取方式

```bash
curl -sL "https://huggingface.co/datasets/opt1zer/EngDesign/resolve/main/EngDesign.json" -o EngDesign.json
shasum -a 256 EngDesign.json   # 应 == 0bade2fa…35addb2a
```
