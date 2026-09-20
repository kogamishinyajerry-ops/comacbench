> **后续状态：2026-09-08 已按用户要求删除原始场和过程文件。下文是清理前的历史交付记录；当前仅可核验保留摘要。完整核验命令现明确拒绝。**

# Re=100/200/300 研究证据接入交付

已接通现有插件目录、贡献预检、启动前置门、运行档案、续跑命令和工作台研究表格。CFD 包修订为 1.1.0，仍只有 1 个 Re=100 可评分任务。研究附件共 48 组，不能当作新增模型成绩或自动发布依据。

## 改动文件

- 新增 `comacbench/evidence.py`：固定目录摘要、研究矩阵检查、快速锚点校验及完整原生文件校验。
- 新增 `comacbench/admission.py`：复用冻结内核的准入、运行及报告；新运行的续跑命令保留证据入口。
- 新增 `evidence/cfd-validation-v1.json`：三份接受研究的路径和 SHA-256 绑定。
- 更新 `packs/aviation-cfd-step-v1/pack.yaml`：研究用途与三个已接受 ID。
- 更新 `plugin/dsh-comac-benchmark/packs.js`、`test-packs.mjs`、`README.md`：原工具参数不变，改走新准入模块。
- 更新 `plugin/dsh-comac-workbench/src/engineering.jsx` 及 `lib/client.js`：显示矩阵、候选带、评分边界及新命令。
- 新增 `tests/test_cfd_evidence_admission.py`、`docs/specs/cfd-evidence-admission-v1.md`；更新 `docs/aviation-quickstart.md`。

## 验证结果

| 验证 | 命令 / 证据 | 结果 |
|---|---|---|
| 原生文件完整性 | `python -m comacbench.evidence --full` / native-integrity.json | 44,284 文件通过；Re=100: 18,023；Re=200: 25,197；Re=300: 1,064 |
| 全量本地回归 | `.venv/bin/python -m unittest discover -s tests` / tests.log | 139 项通过，88.423 秒；随后增加续跑用例及修复由下项覆盖 |
| 新准入及续跑 | `python -m unittest discover -s tests -p test_cfd_evidence_admission.py` / admission-tests.log | 9 项通过；含企业数据参考实现校准及同身份续跑，无模型调用 |
| 插件实际注册调用 | `node plugin/dsh-comac-benchmark/test-packs.mjs` / plugin-tests.json | 10 工具；三研究、48 例；错误研究声明未启动 agent |
| 工作台构建 | `cd plugin/dsh-comac-workbench && npm run bundle` | exit 0，factory 格式断言通过；现有 inlineDynamicImports 弃用提示 |
| 冻结来源 | frozen-source-preservation.json | 102 个源码摘要不变 |
| 已封存交付 | delivery-preservation.json | Re=300 的 1,431 项全部覆盖且不变；1,064 原生项由完整校验覆盖，额外读取 367 项 |
| 展示 | presentation-check.json、feedback/report.html | 浏览器可见三行矩阵、非评分候选带、0 阻断 / 2 待审查；反馈页及三研究报告 HTTP 200 |

测试先以不存在准入模块的失败用例建立边界，再实现未知研究拒绝。后续覆盖缺失附件、摘要损坏、工况错配、研究用途越权和擅自收紧容差。原求解器、冻结研究内核、历史报告和公开判分数值没有改写。

## 使用

```sh
.venv/bin/python -m comacbench.admission validate packs/aviation-cfd-step-v1 --out ./feedback-02
.venv/bin/python -m comacbench.admission run packs/aviation-cfd-step-v1 --agent ./agent.json --out ./evaluation-02
```

插件仍用 `comac_pack_catalog`、`comac_pack_validate`、`comac_agent_run`、`comac_agent_result`。本地反馈页：[打开](feedback/report.html)。

## 风险与后续

- 快速预检只验证分析、回执及清单摘要；完整文件校验不重新求解或降算物理量。本轮没有新的 CFD 求解或模型调用。
- 本地企业数据校准仅检验执行与续跑路径；不是工程师真实 agent 验收。工作台已构建，未声称当前 DSH 宿主已重新挂载并完成用户验收。
- 证据附件依赖仓库 report 树；单独复制 pack 不含全部证据，缺失会阻断。
- 历史 `python -m comacbench` 为冻结兼容入口，没有新证据门。新运行须使用 `.admission` 或现有插件。
- 候选相对带 2.5% / 2% / 2% 不替代 10% 公开评分，Re=200/300 尚未成为评分任务。
- 下一步：在新版本中明确 Re=200/300 运行契约，并补齐对应正例、错误物理/边界/近壁与临界容差负例，校准后提交工程审查。
