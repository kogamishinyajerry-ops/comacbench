# CONTEXT.md — JerryDSH-COMACBench 词汇表

> 领域建模纪律：术语敲定的当场写在这里；本文件只收词汇，不收实现决策（决策见 ADR 与 `docs/wayfinder/` 地图）。

## 评测体系

- **registry**：`registry/registry.yaml`，全部基准的接入清单 SSOT；条目状态机 `proposed → staged → integrated → active`，任意状态可挂 `paused-env`。
- **adapter**：五类标准运行器接口（qa_grounded / code_exec / simulation_agent / field_prediction 等），任务差异只通过任务 YAML 表达，禁止 fork runner。
- **gate（ValidityGate）**：评分底线检查器，先于子分执行；gate 失败分布是结果分析的核心维度。
- **九维度**：结果报告的评分维度体系（见 `scoring/README.md`）。
- **run_manifest**：每次运行的可复现性档案（seed / environment_digest / assets sha256 / 重跑命令）。
- **litbench**（2026-08-28 定名）：论文摘要锚定的文献知识型基准——每题 evidence 必须是语料库摘要（sha256 锁定）的逐字子串，生成器强校验防幻觉；首例 `cfdagent.litbench`。
- **cfdb 镜像**（2026-08-28）：GLM-CFD-Benchmark（MIT，b26799e）三 case 域逐字镜像；evidence 模式 = 判分侧不跑求解器、由冻结 QoI 脚本降算证据包，内网商业 CFD 兼容。

## 工作台 UI（2026-08-22 wayfinder 地图命名）

- **工作台（workbench）**：规划中的 DSH GUI 内嵌只读分析界面；第一受众是评测运营，核心心智"结果说明什么"。
- **数据桥（data bridge）**：工作台页获取仓库数据（registry.yaml / results/ / reports/）的机制；T3 定案 = host 插件 `/comac/*` prefix 路由活读 + client fetch（loopback 守卫、全 GET、零写）。
- **ViewJSON**：工作台统一视图 schema——活读聚合与快照正文同构（header/registry/runs/tasks 四节），UI 对两种数据模式无感渲染。
- **里程碑快照（milestone snapshot）**：聚合视图层的冻结导出，与活读层并存的第二数据面。形态（T4 定案）：全库聚合单 JSON（<2MB，含每 run 内联可复现字段）落 `results/_snapshots/<tag>.json` 进 git；明细 SSOT 永在 results/（git 历史即冻结）；`--full` 全量自包含包仅评审外发、不进 git。
- **本地化硬规矩**：工作台一切依赖必须可完全本地化打包、禁止运行时外部请求——为 intranet 移植预留的不可妥协约束。

## 工程师评测与贡献（2026-09-06）

- **评测包（benchmark pack）**：可复制和版本化的任务目录，包含公开材料、独立判分材料、来源许可和检查范围；通过预检只表示可本地试跑。
- **受测 agent**：工程师明确指定、按任务契约生成答案或制品的程序；它与用于检查判分器的参考实现分别标注。
- **贡献质量反馈**：对缺失材料、形式矛盾及已知不合理判分规则的定位和修复建议；分为阻断运行与需审查，不构成自动批准发布。
- **判分校准**：用参考实现和故障负例验证检查器能接受正确产物、识别预期错误；成绩不计入模型或 agent 排名。
- **证据层次**：本次运行实际完成的验证方式，如真实求解、可执行规则检查、仅材料预检；声明层次不能代替实际执行证据。

## 环境（执行栈）

- **dev**：外网开发终端（当前活跃，OpenFOAM + FoamAgent）。
- **intranet**：内网商业栈目标环境（离线，ANSYS 系/StarCCM+/CATIA 等，Python 包按 env-matrix 分阶段手工导入）。
