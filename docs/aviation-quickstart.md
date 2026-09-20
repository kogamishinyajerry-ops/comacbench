# 工程师快速使用 COMACBench

你可以评测自己的 agent，也可以贡献新的评测包。当前首包包含 **1 个实际 CalculiX 结构求解任务、1 个企业数据规则任务、1 个知识本体规则任务**。它用于验证接入与判分流程，暂不覆盖飞机级设计验收、文件级 ETL 或完整商业仿真 agent 生命周期。

## 评测自己的 agent

在仓库根目录使用现有评测环境：

```bash
source .venv/bin/activate
python -m comacbench validate packs/aviation-core-v1
python -m comacbench run packs/aviation-core-v1 --agent ./agent.json --out ./my-evaluation-01
```

打开 `my-evaluation-01/report.html`：先看哪个任务有缺口，再展开数值、检查范围、问题原因和证据路径。报告可以离线打开，无 CDN、字体或遥测请求。完整结果在 `run.json`，请求/回复在 `agent-audit/`，现有 adapter 的结果及复跑档案在 `runs/`。

环境要求：Python 评测环境中的 PyYAML / numpy / scipy / scikit-learn；结构任务需要已安装的 CalculiX，可用 `CCX_BIN` 指定。预检执行环境失败时不会调用 agent。`limits` 是防止挂起的运行限额，与 API 费用预算不同。

外部 agent 的生成时限由配置 `timeout_s` 控制；`limits.wall_clock_s` 用于制品执行与求解阶段，生成等待不会扣减 CalculiX 的求解时间。模型示例已采用 32768 输出上限和 900 秒进程超时，并在 workspace 保留原始 provider 响应；截断或传输失败仍会中断且保留证据。

`examples/agents/reference.json` 是带有参考答案的接口验证程序，可立即用来走通上面的命令。它**不能作为受测 agent 成绩**。`examples/agents/model.json` 是可运行的模型代码 agent 示例，通过以下环境变量接入兼容接口：

- `COMAC_MODEL_BASE`：API 根地址，不含 `/chat/completions`。
- `COMAC_MODEL_NAME`：明确的模型版本。
- `COMAC_MODEL_KEY`：密钥；只在本地环境设置，不写入配置或提交到仓库。

这个示例只处理纯文本任务；有公开文件输入时会明确拒绝，需由工程师自己的 wrapper 处理。MiniMax 和 GLM 的本轮配置也在 `examples/agents/`。企业材料应由工程师选择合适的本地/内网 agent 执行端。

## agent 输入输出协议

一个任务对应一个受信本地进程，不经过 shell 拼接。命令收到 stdin JSON；stdout 只写一份 JSON，日志写 stderr。

配置示例：

```json
{
  "protocol": "comacbench.agent.v1",
  "name": "my-simulation-agent",
  "revision": "2026-09-06-r1",
  "command": ["{python}", "./my_agent_wrapper.py"],
  "revision_files": ["my_agent_wrapper.py"],
  "timeout_s": 420,
  "env": [],
  "identity_env": []
}
```

`./` 相对于配置文件目录，`{python}` 使用当前评测解释器。`revision_files` 列出影响 agent 行为的本地源码/配置；环境变量只能声明名字。影响模型、端点、采样策略的非密钥变量应列入 `identity_env`，其摘要参与复跑身份。API 密钥不进入身份或档案。

请求字段：`protocol`、`task_id`、`seed`、`prompt`、`assets`、`output_contract`、`allowed_tools`、`limits`、`answer_format`。公开资产复制到进程 cwd 的 `inputs/`，路径和摘要随请求提供。参考答案、oracle、隐藏断言、判分器不在请求里。

响应示例（`answer` 为最终源码或答案文本）：

```json
{"protocol":"comacbench.agent.v1","task_id":"beam_static_01","answer":"...完整 Python 源码..."}
```

你的 wrapper 将公开任务交给已有 agent，再把它的最终交付物转换为上面的响应。结构首包要求返回生成 `model.inp` 的脚本，由判分 harness 实际执行 CalculiX。直接导入 Fluent/StarCCM/ANSYS 的既有求解证据包属于下一阶段接口，当前不会把自报 QoI 当成求解证明。

临时 cwd 和公开输入过滤用于协议隔离，**不构成 OS 级权限隔离**。本地 wrapper 是用户信任的程序；来源不明的贡献代码校准应放在独立受控执行环境。

## 贡献新的评测集

```bash
python -m comacbench init ./my-benchmark-pack
python -m comacbench validate ./my-benchmark-pack --out ./feedback-01
python -m comacbench calibrate ./my-benchmark-pack --out ./calibration-01
```

`init` 复制完整可运行示例，不是占位目录。编辑后要核对题面摘要、参考版本、材料许可与边界；不要把改名本身当成新题。当前接入入口支持 `simulation_agent/ccx_fea`、受限的 `simulation_agent/cfd_step` 和 `code_exec/unit_tests_problem`；未知类型会拒绝试跑。其他原有 adapter 仍走既有 CLI，后续逐个补齐贡献检查规则后加入。

| 材料 | 放在哪里 | 检查与反馈 |
| --- | --- | --- |
| 包信息、能力族、任务清单、来源许可 | pack.yaml | 缺字段、任务漏列、ID 冲突、非法路径 |
| 完整题面及公开资产 | tasks/&lt;suite&gt;/、input.assets | 缺文件、摘要变化、参考答案误暴露 |
| 参考答案、版本、来源、误差依据 | reference / private/ | 非有限真值、指标不对应、非法或过宽容差 |
| 独立判分逻辑 | grader | 空断言、恒真断言、未知检查器、关闭 gate |
| 检查权重与交付物 | scoring / output_contract | 未实现项赋权、忽略正确性、声明未检查的产物 |
| 需求到检查的对应 | evaluation.requirements | 缺少对应检查、引用不存在的断言；not_covered 单列待审 |
| 无产物及错误内容负例 | evaluation.negative_controls | 校准验证预期错误确实被识别；不能只验证参考答案全分 |

贡献流程：**材料预检 → 修复阻断项 → 显式正负例校准 → 工程专家审查 → 版本冻结与发布**。当前实现前三步并输出待审信息，始终 `publishable=false`，不会自动修改 registry 或发布数据。

静态规则能发现形式矛盾和已知坏模式，不能自动裁决所有自然语言歧义、不合理工况或错误真值。题意、参考答案、工程标准和代码判分的一致性仍需专家审查。v1 包会明确提示其结构 grader 尚未独立检查全部材料、边界和网格要求；新增 v2 的范围见下文。

退出码：0=预检可本地试跑 / 执行完成；2=材料、身份或运行错误；3=校准失败。`run` 的退出 0 表示完成评测，agent 是否合格仍看每题分项和 `full_pass`。

## 可信复跑

```bash
python -m comacbench run packs/aviation-core-v1 --agent ./agent.json --out ./my-evaluation-01 --resume
```

同一输出目录必须保持评测包、agent 配置/源码、非密钥运行参数、判分源码、求解器二进制、Python 依赖和 seed 一致。变更时使用新 `--out`，旧证据保留。协议失败不自动重试或伪造零分；可核对 `agent-audit/*/status.json` 和 stderr，修复后按规则复跑。

## DSH 插件

工作台新增“工程师入口”，可查看范围、切换评测/贡献指南和材料反馈；操作留在 agent 工具和 CLI。

- `comac_pack_catalog`：发现包及质量状态。
- `comac_pack_validate pack=...`：检查贡献材料。
- `comac_agent_run mode=run pack=... agent=... out=...`：脱离起跑。
- `comac_agent_run mode=calibrate pack=... out=...`：显式正负例校准。
- `comac_agent_result out=...`：状态、结果、报告路径。

host 插件更新时需要带上新增 `packs.js`；client 需要重新 bundle。具体挂载见插件 README。仓库构建成功和工具测试通过，与安装进正在使用的 DSH 实例是两项独立状态。


## 结构输入契约 v2（2026-09-06）

结构仿真优先使用 `packs/aviation-structures-v2`。它包含一题 C3D20 静力梁，新增节点连接、几何与网格、材料、固定端、载荷、输出六项检查。`aviation-core-v1` 的三能力包继续保留，结构题仍按旧版范围解释。

```bash
.venv/bin/python -m comacbench validate packs/aviation-structures-v2
.venv/bin/python -m comacbench run packs/aviation-structures-v2 --agent ./agent.json --out ./structure-run-01
.venv/bin/python -m comacbench calibrate packs/aviation-structures-v2 --out ./structure-calibration-01
```

参考接口探针可以使用 `--agent examples/agents/reference.json`。这是带参考答案的接口测试，不是模型能力测评。

贡献结构题可复制完整目录：`cp -R packs/aviation-structures-v2 ./my-structure-pack`，更新包版本、公开题面与摘要、`grader.deck_contract` 和独立参考值。合载荷须与根部参考反力一致；材料字段缺失、未知检查项和矛盾单位会阻断。每个故障负例声明 `expected_issue`，必须实际命中对应诊断，零分本身不算校准通过。

在 `report.html` 展开任务即可查看六项状态、错误节点和载荷行号。原始结果 JSON 的 `artifacts.engineering_evidence` 保留完整生成脚本、输入 deck、实际求解 dat 和日志及 SHA-256；`origin` 区分生成材料和求解器输出。输入检查失败时没有求解证据。过大、非正规文件或非 UTF-8 的证据不能作为完整通过结果。

当前支持范围见题面的 `ccx.cantilever.v1` 段和 [结构契约规格](specs/structural-contract-v2.md)。超出该范围的关键字会明确标注不支持，不能当作一般有限元模型错误。工程专家审查、网格收敛研究和商业求解器接受仍是后续工作。


## CFD 原生证据包

`packs/aviation-cfd-step-v1` 是一个可直接运行的二维 Re=100 后向台阶基础题。先验证求解环境和接口，再连接自己的 agent：

```bash
.venv/bin/python -m comacbench validate packs/aviation-cfd-step-v1
.venv/bin/python -m comacbench run packs/aviation-cfd-step-v1 --agent examples/agents/cfd-reference.json --out ./cfd-interface-01
.venv/bin/python -m comacbench run packs/aviation-cfd-step-v1 --agent ./agent.json --out ./cfd-agent-01
.venv/bin/python -m comacbench calibrate packs/aviation-cfd-step-v1 --out ./cfd-calibration-01
```

`cfd-reference.json` 有参考源码，只验证接口，不是模型成绩。受测 wrapper 会收到 `inputs/templates/` 八份公开原生输入及摘要；现有纯文本 `model.json` 示例不能直接处理这些文件。让自己的 wrapper 把材料传给仿真 agent，并返回生成 `case/` 的 Python 脚本。平台仅执行一次脚本，随后独立运行 blockMesh、checkMesh 和 simpleFoam。没有候选脚本二次组装证据的阶段。

环境：Docker 和本地 `openfoam/openfoam10-paraview510` 镜像 ID `sha256:d6ff1f9a2e7bc3c9177f373bebbdeb542fd8b49144afc24d5e3a3cd9bfae253d`。后端固定到该不可变镜像，不自动拉取。容器禁网络，限 2 CPU、4 GiB、128 PID，计算阶段共享 600 秒总预算；超时清理只针对本次容器，清理与环境检查有额外限时。生成脚本仍是本地受信执行，不构成 OS 级隔离。

报告展开后可看六阶段状态、459 次等实际迭代数、残差曲线、质量净通量、底壁剪切过零曲线和参考偏差。`cfd-evidence/<run>/` 保留 `submitted/` 原始输入、平台注入后的 `case/`、原生 polyMesh/U/p/phi/wallShearStress、求解日志、完整生成源码、`evidence.json` 文件摘要。平台从原生场重算，拒绝自报 QoI 和预制求解输出。

贡献 CFD 材料可复制整个包：`cp -R packs/aviation-cfd-step-v1 ./my-cfd-pack`。本版仅支持公开方言和固定物理问题；模板、参考来源、单位、阈值、六项需求追踪或六类故障负例缺失，预检会返回具体字段与修复建议。新工况、求解器或宽松阈值需要独立版本的判分器与校准，不能只改 YAML 绕过检查。校准要求负例命中 `expected_issue`，正常退出但未收敛也会零分。

已完成三档网格、四种域组合的 [敏感性研究](../report/2026-09-06-cfd-sensitivity/README.md)，12 个算例在包括两次独立续跑后全部收敛；fine GCI 约 0.884%，仍未通过 0.5% 研究门。原 10% 容差继承上游演示口径，本轮没有取得足够依据发布新阈值或扩展工况。结果不代表完整论文复现、真实模型排名、商业 CFD 软件闭环或飞机工程接受。

## 已验证 CFD 研究的最新入口

Re=100/200/300 的研究证据现通过现有插件自动接入。新贡献和评测使用 `python -m comacbench.admission validate|run|calibrate`，参数与原 CLI 相同；历史 `python -m comacbench` 保留供冻结协议使用。详见 [证据准入与边界](specs/cfd-evidence-admission-v1.md)。Re=200/300 是研究依据，尚不是可评分任务；候选带不替代 10% 公开容差。
