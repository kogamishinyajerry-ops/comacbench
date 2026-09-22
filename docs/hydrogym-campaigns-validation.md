# Campaign auditor 专项验证记录（2026-09-22）

## 基线与修改范围

- 仓库：`kogamishinyajerry-ops/comacbench`。
- 基线提交：`5e2664b393c188681ca1b7b8576c1a3ace5631d9`。
- 目标分支：`codex/trusted-resume-and-formula`。
- 新增 `comacbench/campaign.py`、专项测试、使用说明和一个复用现有 starter 的计划示例；README 仅增加入口。
- 未改动任何 grader、物理真值、容差、评分权重、现有 run 协议或执行命令。

## 已执行

环境为 Linux、Python 3.13.5。因本地无法通过 git 下载完整仓库，验证在按上述提交重建的最小源码工作区进行，**不是全量 checkout 的集成验收**。依赖的原有 `comacbench/__init__.py` 与 `comacbench/completion.py` 均按 Git blob 摘要核对与基线一致。

```text
python -m unittest discover -s tests -p test_campaign.py -v
Ran 80 tests in 2.001s
OK
```

80 个专项用例，0 failure、0 error、0 skip。测试夹具均为合成记录，未调用模型、求解器或现有产品 pack。

覆盖：固定矩阵、合法零分、伪造 full_pass、缺失运行、参考实现排除、Agent/pack/engine/environment 身份漂移、suite manifest 的 provider/seed/n_tasks 核验、原始结果与清单的 adapter/environment 一致性、摘要和原始分数不一致、重复任务／case、非法 scope、证据等级、超大／非有限／重复键 JSON、路径和符号链接、未登记重试、离线 HTML 转义、CLI 退出码和禁止覆盖。

`python -m compileall -q comacbench tests` 已通过。

Chromium/Playwright 对最终 HTML 使用 `set_content` 渲染合成报告，检查了 1440px 桌面与 390px 窄屏：均 0 page error、0 network request，页面无整体水平溢出；窄屏表格单独水平滚动。直接 `file://` 导航被验证环境策略阻止，因此这里**不声称已验收 Windows 双击打开**。

## 尚未执行，合并前应补充

1. 在完整仓库依赖环境运行既有测试集合，排除导入、打包和测试发现冲突。
2. 先解决当前 starter pack 的所有独立阻断，再按指南用真实 `comacbench run` 输出执行 freeze/report 闭环；不得用合成夹具代替。
3. Windows 路径、离线打开、源码／wheel 安装行为与目标内网环境验收。
4. 至少一组真实 Agent 配对回归。参考实现不属于模型成绩；没有新增真实迁移任务。

## 不被本测试覆盖的结论

本工具核验 run.json、suite run_manifest.json 与原始 result JSON，复用原有结果有效性判定并重算满分状态；**不重新执行独立物理验收，不核对全部工程产物字节**。不能据此宣称既有证据归档／可信恢复问题修复、真实模型成绩提升、隐藏任务隔离通过、CFD 数值正确或内网首发批准。

新增 Python 模块会改变既有 `engine_identity()` 摘要。新锚点与新实验使用新输出目录；旧记录不得改写身份绕过 resume 保护。
