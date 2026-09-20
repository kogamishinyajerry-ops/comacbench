# 航空工程评测插件 v1：交付与验证

已完成一个可执行的工程师入口：**标准评测包 → 贡献材料检查 → 外部 agent 调用 → 既有 adapter 判分 → 离线可视化报告**。航空工业仿真为主线，企业数据处理和知识本体作为独立能力族；当前是三题入门包。

## 先看这几份文件

- [工程师快速使用指南](../../docs/aviation-quickstart.md)
- [后续工业仿真、企业数据与本体路线](../../docs/aviation-benchmark-roadmap.md)
- [本轮实现范围和验收标准](../../docs/specs/aviation-plugin-v1.md)
- [MiniMax 真实调用报告](minimax-live-v2/report.html)
- [GLM 真实调用报告](glm-live-v2/report.html)
- [不完整评测集的自动反馈示例](contribution-feedback/report.html)
- [最终正负例校准报告](calibration-final/report.html)
- [机器核验结果](verification.json)

## 当前可以做什么

`python -m comacbench` 提供 init / validate / run / calibrate / catalog。init 复制完整可运行首包；validate 不执行用户贡献的代码；run 用 JSON stdio 接入用户自己的受信 agent；calibrate 显式执行参考实现和故障负例。

DSH host 新增 4 个工具：comac_pack_catalog、comac_pack_validate、comac_agent_run、comac_agent_result。client 新增“工程师入口”，包含评测/贡献两个流程和质量反馈。GET 数据桥保持只读，POST 返回 405，非本机地址返回 403。**本轮验证了仓库插件构建、工具和路由；未修改正在使用的 DSH profile，也未宣称已挂载至该实例。**

预检会标出缺文件、摘要变化、答案误入公开材料、非法路径、重复 YAML 键、空/恒真断言、指标不对应、权重不合理、非有限真值、非法或过宽容差、未覆盖交付物及需求。每项带位置和修复建议。检查通过仅表示可本地试跑，`publishable=false`；没有自动批准发布。

## 真实模型结果

两个模型在相同的加长协议下均完成 3 题：

| 模型代码 agent | 结构仿真实跑 | 企业数据规则 | 本体关系规则 | 全部检查通过 |
| --- | --- | --- | --- | --- |
| MiniMax-M3 | 0.5 | 1.0，7/7 断言 | 1.0，7/7 断言 | 2/3 |
| GLM-5.3-flash | 0.5 | 1.0，7/7 断言 | 1.0，7/7 断言 | 2/3 |

结构题两者实际求解完成，但数值均未达到 5% 参考带：尖端位移 -3.130798 mm 对参考 -3.811745 mm；根部反力 822.2222 N 对参考约 1000 N。0.5 来自完成求解及输出项，物理对账为 0/2；它不表示工程任务合格。

对原始生成 deck 进行独立连接关系核验：两者均有 45 个受载节点，其中 8 个没有出现在单元连接中。声明总载荷约 -1000 N，连接到有效单元的载荷仅约 -822.2222 N，其余约 -177.7778 N 落在未连接节点上，与反力误差吻合。证据见 [连接关系诊断](structural-diagnosis/summary.json) 及该目录各模型的 model.inp / make_case.py。此次诊断没有模型调用，没有改写原分数。

这些结果属于两个模型代码 agent 的入门样本，不能作为总体排名、完整仿真 agent 能力或工程师用户接受的结论。数据/本体题当前是可执行规则构建，不是文件级 ETL 或自然语言知识抽取。

## 传输失败与修复

首轮 `minimax-live` 在结构题达到 16384 输出上限，标记为 interrupted；首轮 `glm-live` 保留一题结构执行失败，随后数据题发生 360 秒请求超时。它们没有被伪造成完整评测，也没有被后续成功结果覆盖。

`*-live-v2` 使用新的配置和输出目录：输出上限 32768、HTTP 超时 840 秒、agent 进程超时 900 秒、冻结的长上下文任务包 wall_clock_s=1200。题面、参考答案、评分和输入不变。原始 provider 响应保存在 workspace，协议摘要见 [transport-v2-change.json](transport-v2-change.json)。首轮与新协议不混排。

试验还发现外部 agent 的生成等待会扣减旧 CalculiX 分支的求解预算。新增测试用 400 秒生成等待复现求解预算变为 -100 秒；现只针对 external provider 分开计时，原有 provider 行为保持。示例模型 wrapper 的上限、超时和原始响应保留也已修复。

真实模型结果对应修复前的冻结引擎，完整 57 个源码文件保存在 frozen-source/；最终实现对这 6 份原始答案做了 **零模型调用的离线回放**，分数和有效性门全部一致，见 [replay-final/summary.json](replay-final/summary.json)。最终参考接口及校准另用新输出目录验证，未在旧身份目录上强行续写。

## 验收证据

| 检查 | 结果 | 证据 |
| --- | --- | --- |
| Python 回归 | 56/56 通过 | final-tests.log |
| 贡献材料与 agent 负向输入 | 包含于上述测试；先红后绿 | contract-red.log、solver-budget-red.log、solver-budget-green.log |
| 当前参考实现 | 3/3 全分 | calibration-final/run.json |
| 无产物 + 错误内容负例 | 6/6 被识别 | calibration-final/run.json controls |
| 当前外部参考 agent 接口 | 3/3 全分，明确是带答案的接口自检 | reference-final/run.json |
| 同身份续跑 | 无新增 agent 调用，结果字节不变 | final-resume.json |
| 错误 seed | 拒绝；状态字节不变 | final-resume.json |
| 不完整投稿 | 阻断，0 次 agent 调用，未创建运行目录 | invalid-run.log、contribution-feedback/validation.json |
| DSH 工具及路由 | 10 个总工具；非法包零启动；GET/loopback 守卫通过 | plugin-final-tests.log |
| 工作台构建 | bundle 成功，factory 格式断言通过 | workbench-build.log |
| 浏览器检查 | 真实报告显示、工业仿真筛选、证据下钻、缺失材料反馈通过 | 本轮浏览器操作；不是 DSH 实例挂载验收 |
| 历史证据 | 1104 个文件摘要不变 | prior-artifacts.json、verification.json |

校准错误内容负例具体表现：半载荷结构题 0.5；错误米→毫米换算 0.89997；错误本体关系类型 0.80001。它们能执行，仍未得到满分。

## 复核命令

在仓库根目录：

```bash
.venv/bin/python -m unittest discover -s tests
node plugin/dsh-comac-benchmark/test-packs.mjs
node plugin/dsh-comac-workbench/build.mjs
.venv/bin/python report/2026-09-06-aviation-plugin-v1/verify_evidence.py
```

verify_evidence.py 只读已有证据并打印结果，不调用模型。若源代码随后变化，它会明确指出当前源码与本轮最终校准的身份不一致。

## 改动与下一步

核心新增 comacbench/、packs/aviation-core-v1/、examples/agents/；现有 providers/run_state 接入 external 身份；code_exec/simulation_agent CLI 接入 external；结构分支修复 external 求解预算；插件、工程师 UI、指南及三组测试同步更新。历史 B03/B05 报告、原始任务与本轮无关的改动未覆盖。未 commit、push 或部署。

下一步优先做 **载荷与网格连接检查、材料/边界检查、原始求解证据完整留存**，再扩 CFD 基础算例。当前结构题的全部建模约束尚未独立核验；商业求解器 evidence 接口、受控投稿隔离、文件级企业数据、RDF/SHACL 互操作、专家审核发布和新工程师首次接入均是明确的后续门槛。路线参考的 TMR、PROV-O 与 SHACL 官方来源已在开发路线中逐项链接。
