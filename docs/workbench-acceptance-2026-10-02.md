# 变更工作包与产品收口：专项验收记录

基线：默认分支 `codex/trusted-resume-and-formula`，提交 `8f949436da4f7323a986b6f003d9c7ac89a8946f`。本轮不合并默认分支、不修改既有评分协议或研究任务。

## 与 PR #6 的关系

PR #6 尚未合并。其逐任务配对功能、Campaign 报告代码与实验配方保持独立。本轮仅复用其中已实际验证的源码导出修复及四项测试，字节保持一致：

- `.github/workflows/campaign-audit.yml`：Git blob `7af6379602c35bf49080363884d7e66a1c690e05`。
- `tests/test_campaign_checkout.py`：Git blob `6ba05e8f7c8f305e64b608121dbf761025b81916`。

原因：默认分支的 sparse checkout 仍可能因研究数据中的 Windows 非法路径失败。新 workbench 工作流沿用相同的精确 tree 导出方式，补充自己的源数据目录及本地 Git 对象夹具测试，不关闭 `core.protectNTFS`。

## 本地实际执行

环境：Linux / Python 3.13.5。容器不能 DNS 解析 GitHub，完整 clone 和归档下载没有成功；通过 GitHub 连接器读取必要源文件，并按 Git blob 核对后建立源码子集。原始 README、包初始化文件、原工作流与复用文件均核对了实际 blob。不能将此工作区称为全仓库检出。

| 验证 | 实际结果 |
| --- | --- |
| `unittest discover -s tests -p 'test_workbench*.py'` | 66 tests，全部通过；覆盖内容规则、状态变化、负例、恢复、行动预算、CLI、目录及精确源码导出 |
| PR #6 原源码导出四项测试 | 4 tests，全部通过；不是重新运行其全部 149 项测试 |
| `compileall` | 新增模块、示例与专项测试通过 |
| 参考策略完整 CLI | `complete=true`，25/48 次行动；5 个交付节点当前均验证；最终声明 `needs_review` |
| 陈旧结果负例 | `complete=false`，`unverified_targets`；原失败保留 |
| 虚报全部可执行负例 | `complete=false`，`false_completion_claim`；要求 `needs_review` |
| HTML 检查 | 参考／陈旧／虚报三种状态 × 1440/390 宽度，共六组；展开原生 details，零页面错误、零外网请求、无整体横向溢出 |

浏览器使用系统 Chromium。默认 Playwright 下载版浏览器不在环境中；`file://` 访问受环境限制，最后采用 `set_content` 检查实际 HTML 内容，未声称完成 Windows 双击报告验收。报告强调“工作包处理正确”和“仍有输入需澄清”的区别。

Catalog 的本地 material 测试使用明确标注的合成路径／registry 夹具。实际仓库路径与全部引用 ID 的检查由新 CI 的 `python -m comacbench.catalog --check` 执行；提交工作流不代表该检查已经通过。最新线上执行结果与提交 SHA 请看本 PR 的 checks 和说明。

## CI 范围

两个工作流均为 Linux/Windows × Python 3.11/3.13。Campaign 工作流只跑原有 Campaign 专项及源码导出测试；WorkBench 工作流跑新增专项、实际目录校验、参考流程与两个负例。只读取指定源码 tree，不下载研究 LFS 资产或求解器，不使用模型凭据。没有把避开研究数据的专项 CI 说成完整检出或完整离线发布。

## 未宣称完成的内容

本轮没有真实模型性能实验、具体 DSH 适配验收、原生工程求解器试验、独立隐藏实例、跨求解器等价性、wheel 安装或内网断网部署验收。现有历史实机记录与本轮结果分开保留。

工作环境只强制执行受理行动的次数。主体身份是声明信息；摘要链没有签名，不能抵抗掌控整个归档的操作者，也不能证明不存在会话外重试或人工介入。场景公开，`publishable=false`、`isolated_transfer_verified=false`；workbench 记录不会被冒充为既有 `comacbench.run.v1` 或 Campaign 成绩。

新增 Python 源码会改变既有 pack 全局引擎摘要；新实验应使用新输出目录。旧记录保持原样，不修改其摘要来强行恢复。
