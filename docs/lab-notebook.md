# 民机设计 Benchmark Harness（JerryDSH / v0.1）

目标：把 Harness 从"答题器"建成**民航设计 Agent 评测系统**。分三层：

- **公共可比层**：与论文/其他模型横向对比（明知公开题可能已入训练语料）；
- **工程可执行层**：Agent 真正生成代码、模型、网格、算例并运行；
- **受控隐藏层**：用开源工具动态生成未公开参数组合，防记忆，用于版本选型。

## 目录

```
benchmarks/
├── README.md                 # 本文件：路线图与使用入口
├── env-matrix.md             # 内网评测环境矩阵（env_class SSOT + 分阶段 Python 导入清单 + 商业工具批处理要求）
├── registry/
│   ├── registry.yaml         # 接入清单 SSOT（机器可读，status 流转含 paused-env）
│   └── license-notes.md      # 许可证状态矩阵（非 confirmed-* 一律不得镜像）
├── adapters/
│   └── README.md             # 五类标准 adapter 规范
├── contracts/
│   └── task.example.yaml     # 任务 YAML 契约参考实现（逐字段注释）
├── scoring/
│   └── README.md             # 评分体系：九维度、ValidityGate、judge 边界、划分纪律
├── runners/                  # 五类标准 adapter 运行器 + 模型 provider 层（禁止 fork runner）
├── tasks/<registry_id>/      # 任务 YAML + 题面（由镜像数据生成，文件名 = task_id）
├── data/<来源族>/<基准>/      # 镜像数据 + PROVENANCE.md（先许可证后镜像，sha256 锁定）
├── report/
│   └── 2026-08-19-benchmark-survey.md   # 调研报告归档（决策证据基线，冻结）
├── plugin/
│   └── dsh-comac-benchmark/  # DSH 插件（comac_* 六工具，薄代理 runners/；安装法见其 README）
└── results/                  # 基线报告落点 results/<registry_id>/<date>/<provider>/
    └── M1-summary.md         # 里程碑总结（M1 起每里程碑一份）
```

## 内网环境策略（2026-08-19 二次决策后，详见 env-matrix.md §0）

- **两层目标环境**：`dev`（外网开发终端，当前活跃——装有 **OpenFOAM + FoamAgent**，无 Fluent/StarCCM，一切开发与评测先在此跑）；`intranet`（内网商业栈 ANSYS 系/StarCCM+/CATIA/Amesim/FENSAP/MATLAB，最终移植目标）。
- **求解器无关原则**：grader 只认 result.json + 残差/守恒/目标量；OpenFOAM（dev）与 Fluent/StarCCM（intranet）是同一 simulation_agent 下的可替换执行后端。
- 仍处 `paused-env` 的只有 openvsp（无原生二进制）与 bscw（无气弹链）；foam_basic 已随开发终端 OpenFOAM 恢复进核心。
- Python 包：开发终端 pip 直连可用；内网仍按 env-matrix.md 分阶段清单手工导入。

## v0.1 核心八件套（首批排期）

| # | registry_id | adapter | 验证目标 |
| - | --- | --- | --- |
| 1 | cfdllm.cfdquery | qa_grounded | 数据格式、模型调用、客观判分 |
| 2 | aeroengqa.gold | qa_grounded | RAG、引用、拒答、长文档（许可核验后放行镜像） |
| 3 | scicode.physics | code_exec | Python 沙箱、隐藏测试、数值容差 |
| 4 | cfdllm.cfdcode | code_exec | 科学代码生成与稳定性 |
| 5 | engdesign.open | code_exec | 工程设计、仿真反馈、多轮改进（仅纯 Python 容器可运行任务；逐任务许可清点后放行） |
| 6 | cfdllm.foam_basic | simulation_agent | OpenFOAM+FoamAgent 端到端执行 + gate 检查器（dev 终端） |
| 7 | aviary.transport_mission | simulation_agent | 总体设计、任务分析、约束优化 + 隐藏动态题 |
| 8 | superwing.coeff_lite | field_prediction | 跨声速机翼泛化 + 按几何构型划分 |

这七项已能区分：只会航空问答的模型 / 会写代码不会工程的模型 / 会调工具不会判断结果的 Agent / 能完成多步可验证设计任务的 Agent。

## 里程碑

- **M0（当前）**：规范落盘（本目录）+ 内网环境策略定版（env-matrix.md）。registry 全部 `status: proposed`，3 项 `paused-env`。
- **M1**：cfdllm.cfdquery + aeroengqa.gold 达到 `integrated`——打通统一 registry、数据版本、模型接口、报告结构。放行条件：AeroEngQA Zenodo 许可核验通过 + Phase-A wheel 导入。
- **M2**：scicode.physics + cfdllm.cfdcode 达到 `integrated`——建立代码沙箱与隐藏测试框架。
- **M3**：cfdllm.foam_basic（dev 终端 OpenFOAM+FoamAgent）+ aviary.transport_mission 达到 `integrated`——仿真 Agent 判分管线（validity gate 全检查器）+ 首批隐藏动态题生成器。Phase-B wheel 导入（内网线）。
- **M4**：engdesign.open（收窄子集）+ superwing.coeff_lite 收尾 v0.1，产出首份九维度基线报告（至少一个基线模型，含 gate 失败率分布）。
- 批次 2（pycycle/cadgen/simjeb/gtm/mechvqa/nasa_tmr/crm/hilift；openvsp 与 bscw 已 paused-env）在 v0.1 报告评审后启动。

## status 流转与门槛

```
proposed -> staged       数据镜像完成 + 环境可复现（license-status 必须 confirmed-*；env_class 内网可启动）
staged   -> integrated   adapter 跑通 + 基线报告落盘
integrated -> active     进入常规评测轮换
任意状态 -> paused-env   内网无启动评测环境（恢复条件见 env-matrix.md 第 4 节）
```

任何许可证状态回退（见 license-notes.md 巡检节奏）→ 冻结该基准新评测，registry 同步降级。

## 使用规则（给后续实现者）

1. 新基准先在 registry.yaml 建条目并填 license_status 与 env_class，禁止先镜像后补手续；
2. 任务必须套用五类 adapter 之一，禁止 fork runner；差异通过任务 YAML 表达；
3. 每个任务一个 YAML，字段以 contracts/task.example.yaml 为准；
4. 评分实现必须先落 gate 检查器再落子分——gate 是本体系的底线；
5. 隐藏动态题的生成器、采样策略、参考答案隔离方案随 M3 一并评审；
6. env_class 为 `missing` 的条目自动进入 `paused-env`，不得出现在任何里程碑排期里；环境依赖变化只改 env-matrix.md，再同步 registry。
# 航空工程 Agent 评测入口（2026-09-06）

现可通过统一评测包连接本地 agent，完成工业仿真/企业数据/知识本体的入门评测，并自动检查新贡献材料。参阅 [工程师快速使用指南](docs/aviation-quickstart.md) 与 [开发路线和验收范围](docs/specs/aviation-plugin-v1.md)。

```bash
source .venv/bin/activate
python -m comacbench validate packs/aviation-core-v1
python -m comacbench run packs/aviation-core-v1 --agent examples/agents/reference.json --out ./reference-demo-01
```

上述 reference 是带答案的接口自检程序；评测自己的 agent 时替换配置。当前 3 题首包包含实际 CalculiX 求解及虚构企业数据/本体规则，不代表飞机级验收。运行后打开输出目录 `report.html`；贡献者使用 `init → validate → calibrate`，材料缺失或判分问题会生成定位与修复建议。


### 结构仿真输入检查 v2（2026-09-06）

`packs/aviation-structures-v2` 已提供一个可直接连接 agent 的静力梁包：节点连接、网格、材料、边界、载荷、输出六项检查，随后原生 CalculiX 求解与数值对账。配套 8 个可定位故障负例、完整 deck/dat/日志证据和可视化反馈；旧 v1 包保持原版本。

```bash
.venv/bin/python -m comacbench run packs/aviation-structures-v2 --agent ./agent.json --out ./structure-run-01
```

[使用与贡献指南](docs/aviation-quickstart.md) · [本轮校准及回放证据](report/2026-09-06-structures-v2/README.md) · [后续工程路线](docs/aviation-benchmark-roadmap.md)。


CFD 后向台阶包 `packs/aviation-cfd-step-v1` 已可通过同一 CLI/plugin 入口调用：平台执行 OpenFOAM 10，检查实际网格、原生残差和质量守恒，从底壁剪切重算再附着长度，并保留原始场、日志与摘要。配套 6 个故障负例和离线曲线报告。

```bash
.venv/bin/python -m comacbench run packs/aviation-cfd-step-v1 --agent ./agent.json --out ./cfd-run-01
```

[CFD 使用说明](docs/aviation-quickstart.md#cfd-原生证据包) · [CFD 校准及接口证据](report/2026-09-06-cfd-step-v1/README.md) · [三网格/四域敏感性研究](report/2026-09-06-cfd-sensitivity/README.md)。12 个算例已收敛，fine GCI 约 0.884% 未过研究门，原 10% 带保持未校准状态；先继续核验网格误差，再扩展工况与工程接受。
