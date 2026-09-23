# PR #5 合并验收与下一阶段

核查基线：默认分支 `codex/trusted-resume-and-formula`，提交 `8247b25824868da27aa8928755480fa39cc92717`。

## 已确认的状态

PR #5 已合并（merge commit `c0afe75d3b16faab097536ccd0608b8b0a247d94`）。当前 campaign、integrity、completion 与上一份 PR 的最终源码一致，本轮独立重跑 120 项专项测试通过。

维护者在 `8247b25` 记录了 Windows 完整仓库测试：120 专项通过；全量 380 passed、17 skipped、1 failed，仍将失败定位为既存 superwing LFS 漂移；真实校准原始负例与 v2 历史归档迁移也有补充验证。这里引用维护者记录，不将其冒充为本轮独立 Windows 实测。

首轮 CI run `35742848952` 的真实状态是 **Linux 两组成功、Windows 两组失败**。Windows job `106796775603` 的日志显示错误发生在 checkout，测试尚未执行：

```text
error: invalid path 'data/cfdllm/foam_basic/gt_runs/Cylinder/1/0.05/strainRateViscosityModel:nu'
```

原工作流已设置 sparse-checkout，但 Git 仍在检出时校验到范围外的非法 Windows 路径。不能将这次 CI 解释为测试逻辑失败，也不能称为四矩阵通过。

## CI 的针对性修复

使用 setup-python 后，以匿名只读方式抓取精确的事件 SHA 到裸 Git 仓库；通过 `git archive` 只导出 comacbench、tests、.github/workflows。无需建立包含研究数据的工作区索引，也不关闭 `core.protectNTFS`。

导出前验证 SHA，导出后拒绝越界路径、链接和特殊文件，限制快照规模。只使用标准库；不会下载模型、求解器或 LFS 数据。工作流测试改为 `test_campaign*.py`，包括新配对报告及检出回归测试。

本地使用 Git 对象构造含冒号路径的微型仓库，执行**同一段工作流 Python 脚本**，检查指定快照、非法链接拒绝、不存在 SHA 不回退及非 SHA 输入拒绝。该实验不是 Windows 原生 Git 的完整替代，最终四矩阵状态仍以新 PR 的实际 CI 为准。

Git archive 的路径选择语义参考官方文档：https://git-scm.com/docs/git-archive 。工作流 shell 语义参考：https://docs.github.com/en/actions/reference/workflows-and-actions/workflow-syntax 。

## 下一阶段功能

新增逐任务配对结果：新增通过、新增退步、保持通过、仍未全过、待核验。按 case/seed/suite/task 对齐，不按数组顺序；保留原始诊断、分数、证据类别、结果摘要和归档内位置。净提升不再掩盖任务回退。

新增一份已有 workload 包的 Skill A/B 配方与操作指南，详见 `workload-skill-ab.md`。未新增工程题、未改物理评分、未安装 HydroGym，也没有凭空提交真实模型成绩。

## 本轮本地验证

环境：Linux、Python 3.13.5。容器 DNS 无法解析 github.com，完整 clone 失败；本轮根据已有补丁重建专项源码，并逐一核对 Git blob 摘要与基线，不是全仓库 checkout。

- 基线：120 tests，OK（10.256s）。
- 新版本：149 tests，OK（25.799s）；原 120 + 配对报告 25 + 精确源码导出 4，0 failure/error/skip。
- compileall、git diff --check 通过。
- Chromium 内容渲染：完整/缺项 × 1440/390 宽度，共四组；真实点击展开对照，0 页面错误、0 外网请求，无整体横向溢出。file:// 导航被环境限制，采用新页面 set_content；不声称 Windows 双击已验收。
- 测试包括合成归档通过真实 campaign CLI 的子进程往返；不将这称为真实模型或真实产品包评测。

仍未执行：目标内网断网安装、wheel 验收、完整仓库物理求解回归、真实模型 Skill 对照。现有 LFS 摘要问题未更改，不能靠放宽期望摘要掩盖。

## 验收结论

PR #5 已实现的五项修复与专项测试可以保留；Windows CI 需本次修复。接下来应从继续堆叠审核字段转向一场可检查的工程 Skill 对照实验。新报告不授予工程放行、隔离迁移或全产物重验资格。
