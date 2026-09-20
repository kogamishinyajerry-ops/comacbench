# 结构仿真工程输入检查 v2 · 2026-09-06

已把静力梁从“脚本和求解器能运行”推进到“声明的六项建模要求先检查，再实际求解”。所有新结果采用独立包及输出身份。原始 MiniMax/GLM 成绩和 v1 包不变。

[可视化总览](index.html) · [校准报告](calibration-final/report.html) · [GLM 冻结答案回放](glm-replay/report.html) · [MiniMax 冻结答案回放](minimax-replay/report.html) · [贡献反馈](contribution-feedback/report.html)

## 改动文件

- `runners/solvers/cantilever_contract.py`：有明确支持范围的 C3D20 静力梁解析与六项检查。
- `runners/simulation_agent.py`：可选契约接入现有 ccx 分支，失败时不启动求解；保存完整输入和求解证据；缺失/非有限输出不得通过。
- `runners/solvers/calculix.py`：按请求保留完整原生求解日志，默认旧调用行为保持兼容。
- `comacbench/pack.py`、`comacbench/__main__.py`、`comacbench/report.html`：贡献参数与参考平衡检查、指定负例诊断校准、六项可视化与离线回放标识。
- `packs/aviation-structures-v2/`：1 个静力梁任务、公开契约、原参考实现、8 个负例。保留原数值和 5% 容差。
- `tests/test_structural_contract.py`：10 项新增测试，涵盖历史失效、输入故障、合法语法变体、原生证据、贡献阻断和校准误判。
- `plugin/dsh-comac-benchmark/test-packs.mjs`、`plugin/dsh-comac-workbench/src/engineering.jsx` 及构建产物：新包发现检查和实际检查范围文案。
- `docs/specs/structural-contract-v2.md`、`docs/aviation-quickstart.md`、`docs/aviation-benchmark-roadmap.md`、根 README：契约、使用和下一步路线。

## 实现与结果

| 检查 | 实现范围 | 对应负例 |
| --- | --- | --- |
| 节点连接 | 节点参与单元、受载节点有连接、无多余未使用节点 | unconnected_load |
| 几何与网格 | C3D20 角点和边中点、正向轴对齐单元、共节点、完整分区、尺寸与最小划分 | coarse_mesh；附加测试覆盖未知单元类型、错误边中点、缺失节点 |
| 材料 | 每个单元恰有一个实体材料分配，E/nu/rho 一致 | wrong_material、missing_density |
| 根部边界 | 全部根面网格节点固定三个平移自由度，无额外固定或非零位移 | incomplete_clamp、extra_constraint |
| 载荷分配 | 仅在全部尖端网格节点均分 Y 力；同一步重复 CLOAD 累加 | wrong_load |
| 输出请求 | 单步内恰好输出 NTIP U 与 NROOT RF | missing_print |

最终原生校准：参考模型 1/1 全分，8/8 故障负例得 0 且命中指定诊断。外部 reference agent 接口探针 1/1 全分。参考实现是校准夹具，不构成模型能力证据。

MiniMax、GLM 原答案经标准外部 agent 接口离线回放，各检出 **8 个悬空受载节点**，输入门失败、总分 0、未启动求解器。v1 原始 gate=1/score=0.5 保持不变。这是不同检查版本对同一答案的诊断，不是模型能力变化。**本轮新增真实模型 API 调用为 0**。

原始 `result_*.json` 中 `artifacts.engineering_evidence` 是 JSON 字符串，含生成脚本、model.inp、真实 model.dat 和完整求解日志的文本、SHA-256 和来源。未求解时不产生求解证据。生成阶段伪造的 dat 会在真正求解前清除。

## 验证命令

在仓库根目录执行，使用同一 `.venv/bin/python`，不要解析该链接后改用基础 Python 环境：

```bash
.venv/bin/python -m unittest discover -s tests -v
node plugin/dsh-comac-benchmark/test-packs.mjs
node plugin/dsh-comac-workbench/build.mjs
.venv/bin/python report/2026-09-06-structures-v2/verify_evidence.py
git diff --check
```

**66/66 测试通过**；插件工具测试、工作台构建、factory 格式检查、浏览器展开检查与证据校验通过。构建仍有原项目的 inlineDynamicImports 弃用提示，不影响本次成功结果。

正式校准可按报告中的命令使用 `--resume` 复核已有身份，或建立新输出目录：

```bash
.venv/bin/python -m comacbench calibrate packs/aviation-structures-v2 --out ./structure-calibration-new
.venv/bin/python -m comacbench run packs/aviation-structures-v2 --agent ./agent.json --out ./structure-run-new
```

证据索引：

- [机械验收](verification.json) / [验收脚本](verify_evidence.py)
- [66 项测试](all-tests.log) / [插件测试](plugin-tests-final.log) / [构建](workbench-build.log) / [界面核对](ui-verification.json)
- [初始失效复现](connectivity-red.log) / [修复通过](connectivity-green-v2.log)
- [最终校准档案](calibration-final/run.json) / [参考接口](reference-interface/run.json)
- [原始回放来源和摘要](replay-agents/provenance.json) / [同身份续跑与拒绝验证](resume.json)
- [贡献阻断](contribution-feedback/validation.json)：缺失题面、缺少密度契约、容差 1.5；3 类根因连同失效的需求检查引用共 9 项阻断，agent 调用为 0。
- [历史摘要清单](prior-artifacts.json)：1,762 个既有报告文件逐字节不变；另外核对 v1 整包摘要不变。
- `calibration/` 是本轮首次校准；对应 `calibration-source/` 保留当时源码。随后只修正离线回放的报告标识，最终验收用 `calibration-final/` 与当前源码对账。失败日志和首轮校准均保留。

## 风险与未完成项

只支持题面公开的轴对齐结构化 C3D20、共节点、单步线弹性静力梁。其他关键字或选项标注不支持，不推断其物理正确性。参考真值、网格收敛、复杂几何、模态/屈曲和商业求解器接受仍需独立验证。

使用本地受信执行环境，尚未提供操作系统级的贡献代码隔离。尚未自动发布评测包，也未把更新挂载到正在使用的 DSH 实例。已验证标准 CLI/agent 接口、插件注册代理、离线报告与工作台构建；这些不等于企业用户接受。

## 下一步

优先贯通 **CFD 后向台阶**：审查现有任务和参考来源 → 网格/边界预检 → 真实求解及残差、质量守恒证据 → 固定 QoI 重算 → 缺边界、粗网格、伪造 QoI、未收敛四类负例 → 同一插件入口和报告。校准通过后再扩充参数变体；企业数据与知识本体随后接入这条仿真证据链。
