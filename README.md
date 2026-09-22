# COMACBench

**用可复查的任务，检查工程 Agent 交付的东西是否可靠。**

An engineering-agent benchmark harness with native solver evidence.

Agent 提交脚本或算例输入；平台执行检查或真实求解器，从原始产物复算指标，说明哪里通过、哪里失败、哪些能力没有被测到。

## 第一次来，先选一个目的

| 你的目的 | 从哪里开始 | 能说明什么 |
| --- | --- | --- |
| 先看懂一次评测怎样完成 | [初次接入指南](docs/first-run.zh-CN.md)；`aviation-data-starter-v1` | 理解材料检查、校准、接口自检和真实 Agent 评测的区别 |
| 检查结构建模脚本 | `aviation-structures-v2`；先准备 CalculiX | 一个静力梁任务的输入契约、实际求解和数值核对 |
| 研究 CFD 原生证据检查 | `aviation-cfd-step-v1`；需固定 OpenFOAM 10 Docker 环境 | 受限 Re=100 后向台阶；当前不能代表飞机 CFD 能力 |
| 接入自己的任务或研究模型差异 | [开发者协议](docs/aviation-quickstart.md)、[研究目录](registry/registry.yaml) | 按任务契约和既有评测边界扩展 |

**当前用于受控开发与试测，不是飞机设计放行工具。** 示例满分不证明真实工程迁移；参考程序满分不属于模型成绩；材料检查通过不代表这台机器已经能运行。

## 先完成一个不需要工程求解器的例子

前提：维护者已准备完整源码工作区及其 Python 依赖，并且当前目录为仓库根目录。以下命令使用该环境的 Python。这里没有提供已验收的独立离线安装包；不要把源码运行与 wheel 安装等同。

```bash
# 1. 材料检查：不调用 Agent，不执行贡献脚本。
python -m comacbench validate packs/aviation-data-starter-v1

# 2. 校准检查器：参考实现应通过，错误负例应被拦截。
python -m comacbench calibrate packs/aviation-data-starter-v1 --out ./starter-calibration-01

# 3. 接口自检：内置程序直接提供已知答案，不调用模型。
python -m comacbench run packs/aviation-data-starter-v1 --agent examples/agents/reference.json --out ./starter-interface-01
```

打开 `starter-interface-01/report.html`，查看两项任务、每项检查和证据。此步骤只证明接口与检查流程在当前环境中工作。

```bash
# 4. 换成你自己的 Agent 配置，才开始评它的能力。
python -m comacbench run packs/aviation-data-starter-v1 --agent ./my-agent.json --out ./starter-agent-01
```

配置方法、Windows 操作、成功标准和故障处理见[初次接入指南](docs/first-run.zh-CN.md)。每次新实验使用新输出目录；只有身份完全一致的中断实验才使用 `--resume`。

轻量包没有 CalculiX/OpenFOAM/Docker 运行要求，**仍需要仓库的 Python 依赖及运行器源码**。它原样复用 core-v1 的数据与本体两题，不增加两项独立能力或两个真实工程场景。

## 为什么保留这套判分基础

- **平台核验产物。** 仿真任务提交输入，不接受 Agent 自报的最终 QoI 代替原生求解证据。
- **先判断结果是否有效。** 单位、建模、网格、收敛、守恒等适用检查通过后才计算对应分数；未覆盖的检查必须明示。
- **检查器也要接受检查。** 参考实现通过，故障负例命中已声明诊断；判分系统故障不属于成功识别错误。
- **证据随版本保留。** pack、运行器、Agent 与环境身份共同约束可信复跑。专家审查与批准发布仍是独立步骤，`publishable=false` 不会因为校准成功自动改变。

## 产品评测包与研究资产分开理解

| 评测包 | 任务条目 | 用途与限制 |
| --- | ---: | --- |
| `aviation-data-starter-v1` | 2 | 首次接入；复用 core-v1 两个函数级规则任务，无工程求解器 |
| `aviation-structures-v2` | 1 | C3D20 静力梁；六项输入契约检查、CalculiX 求解及反力／位移核对 |
| `aviation-core-v1` | 3 | 混合冒烟包，包含结构求解，因此整包仍需 CalculiX |
| `aviation-cfd-step-v1` | 1 | Re=100 后向台阶；原生证据链，10% 演示容差尚不能充当工程验收依据 |

这些包共用部分任务，不能把条目相加当作独立场景覆盖。Re=100/200/300 的 48 组研究组合经 `comacbench.admission` 接入，为研究证据，不是 48 个新增计分任务；部分历史原始场已清理，复核边界见报告。

研究目录声明 31 项 integrated benchmark、约 2.7k 个任务，涉及知识、代码、CAD、CFD、结构、动力、飞控、总体设计、办公与适航等方向。这一层用于研究、基线和判分资产积累，不等于全部已成为可直接交给工程师使用的产品包。

事实清单：[registry/registry.yaml](registry/registry.yaml)；许可记录：[registry/license-notes.md](registry/license-notes.md)；历史架构与数量说明：[2026-09-11 评估](report/2026-09-11-dev-status-and-beta-readiness.md)。

## 当前版本与部署边界

Python 包版本为 0.3.1。较新的落地记录见 [2026-09-20 Windows 报告](report/2026-09-20-windows-handoff-landing.md)：142 项测试的记录为 **8 errors、17 skipped、0 failures**，不能概括为完整通过；CalculiX 已有实机验证记录，StarCCM+ 安装在位不等于商业 CFD benchmark 闭环已通过。

首发范围、工程任务迁移和后续 PR 建议见[内网首发审查](docs/intranet-launch-review-2026-09-21.md)。源码及资料已提交不等于离线交付依赖齐全；应另行核对 Windows 文件名、LFS 资产、目标平台依赖、许可证和干净机器上的断网运行。

## 开发与接入

外网开发机可按以下方式准备源码环境；内网使用经过审核的导入介质与本地依赖，不应在内网照抄联网安装步骤。

```bash
git clone https://github.com/kogamishinyajerry-ops/comacbench
cd comacbench
python -m venv .venv
# POSIX: source .venv/bin/activate
# Windows PowerShell: .\.venv\Scripts\Activate.ps1
python -m pip install -e .
```

Agent 协议是每题一个受信任本地进程：stdin 接收一个 JSON 请求，stdout 返回 `{"protocol":"comacbench.agent.v1","task_id":"...","answer":"<source code>"}`，日志写 stderr。配置通过 `revision_files` / `identity_env` 参与复跑身份。密钥通过环境变量提供，不写入配置文件；运行日志仍应纳入敏感信息审查。本地受信任进程不等于安全隔离沙箱。

报告是离线 HTML，不依赖 CDN、外部字体或遥测。CLI 退出码：`0` 表示对应操作正常完成，**不保证真实 Agent 满分**；`2` 表示材料、身份或运行错误；`3` 表示校准失败。

```text
comacbench/       pack CLI、预检、运行、校准、证据和离线报告
packs/            可移植评测包与轻量首跑视图
runners/          研究运行器、solver 后端与判分基础
registry/         研究目录和许可记录
tasks/ data/      研究任务与镜像资产
plugin/           DSH host/client 插件和工作台
docs/             使用说明、协议、路线与交接
report/ results/  按日期保存的记录与实验产物
```

贡献入口仍为 `comacbench init ./my-pack` → `validate` → 显式 `calibrate` → 工程专家审查 → 冻结版本。`init` 当前复制的是三任务 core-v1，包含结构求解；首次学习请先使用上面的轻量包。

更多资料：[航空评测协议](docs/aviation-quickstart.md) · [路线图](docs/aviation-benchmark-roadmap.md) · [Windows 交接](docs/windows-handoff.md) · [实验笔记](docs/lab-notebook.md)。

## License

项目整体许可尚待维护者明确，不能由仓库公开可见推断为可任意再分发。第三方数据遵循各自许可记录；轻量包只复用 task metadata 已标明为 CC0-1.0 的自建数据／本体示例，不改变仓库其他材料的权利状态。导入和再分发前逐项审核 [license notes](registry/license-notes.md)。
