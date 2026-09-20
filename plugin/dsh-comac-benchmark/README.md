# dsh-comac-benchmark — 民机设计 Benchmark Harness 的 DSH 插件

把 [JerryDSH-COMACBench](../../README.md) 评测系统接入 DSH：agent 可在会话里直接
发现基准、起跑基线（脱离长跑）、轮询状态、读结果与报告。

**设计原则：薄代理。** 判分管线 / 沙箱 / provider 层的 SSOT 永远在仓库 `runners/`，
本插件零依赖、只做发现-起跑-读取三件事，仓库演进插件自动跟随，永不复制判分逻辑。

## 工具（前缀 `comac_`）

| 工具 | 用途 |
| --- | --- |
| `comac_registry` | registry.yaml 全量：id / status / adapter / env_class / license |
| `comac_bench` | 单基准详情：任务数 / runner 模块 / 解释器 / 环境要求 / 结果矩阵（date×provider×计数）|
| `comac_run` | **脱离起跑**：detached + 日志落盘 + 恒 `--resume`（幂等，断点续跑）；oracle 自检 / stub 冒烟 / glm / minimax（key 起跑时从 Keychain 注入，不落盘）|
| `comac_run_status` | 运行状态：log 尾 + 结果计数 + 进程存活 |
| `comac_results` | summary.md 头部 + 从 result JSON **独立重算** gate/失败模式分布/均分（防半截 summary 误导）|
| `comac_report` | 读报告：九维度基线 / batch 总结 / M1-M4 里程碑 |

## 典型工作流

```
comac_registry status=integrated        # 看有哪些可跑
comac_bench   registry_id=hilift_aeroml.lite   # 确认任务数/环境/既有结果
comac_run     registry_id=hilift_aeroml.lite provider=oracle   # 先判分管线自检（必须满分）
comac_run     registry_id=hilift_aeroml.lite provider=glm      # LLM 基线（小时级，脱离）
comac_run_status registry_id=hilift_aeroml.lite                # 轮询
comac_results registry_id=hilift_aeroml.lite                   # 读数
comac_report  name=nine-dim                                    # 回到全景
```

## 环境契约

- `COMAC_BENCH_HOME`：仓库根（默认 `/Users/Zhuanz/projects/jerry-personal/JerryDSH-COMACBench`）
- `cfdllm.foam_basic`：判分需 docker OpenFOAM（起跑前预检）
- `pycycle.engine_cycle`：用仓库 `.venv`（om-pycycle 钉子栈，见其 PROVENANCE——
  `om-pycycle==4.4.0 + openmdao==3.34.2 + numpy==1.26.4 + scipy==1.13.1`，勿盲目升级）
- `glm` / `minimax`：起跑时 `security find-generic-password` 注入
  `GLM_API_KEY` / `MINIMAX_M3_API_KEY`，密钥只进子进程 env
- 长跑事实（2026-08 实测）：LLM 基线单题 3-44 min、全量 100+ 题 = 小时级——
  `comac_run` 一律脱离返回，重复调用幂等（resume 跳过已有结果）

## 工作台数据面（v1 已实现，规格书 docs/specs/workbench-ui-v1.md）

host 半新增 `/comac/*` prefix 路由（只读 GET · loopback 守卫 · 与 comac_* 工具共享数据层）：

| 端点 | 用途 |
| --- | --- |
| `/comac/overview` | 家底计数 + 九维雷达 + 最近运行 + 快照清单 |
| `/comac/registry` `/comac/runs` `/comac/runstatus` | registry 全字段 / run 索引(含 manifest 内联) / 在跑批监控 |
| `/comac/matrix?date=` | date×provider×基准 聚合矩阵 |
| `/comac/bench/<rid>[?date&provider]` | 基准详情 + 任务行（只给 date 时自动选最新 provider） |
| `/comac/task/<rid>/<date>/<prov>/<task_id>` | 单题完整信封 |
| `/comac/snapshots` `/comac/snapshot/<tag>` | 快照清单 / 快照 ViewJSON |

配套：`snapshot.mjs --tag <t> [--full]` 生成里程碑快照（聚合 ViewJSON 进 git；`--full` 外发包不进 git）。

UI 在 `plugin/dsh-comac-workbench/`（client plugin，注册进 conversation.view ViewMap「工作台」tab）。

## 安装 / 更新

```bash
# 1) host 半（本插件）：拷三文件 + patch 条目
mkdir -p ~/.dsh/plugins/dsh-comac-benchmark
cp plugin/dsh-comac-benchmark/{index.js,packs.js,package.json,snapshot.mjs} ~/.dsh/plugins/dsh-comac-benchmark/
# ~/.dsh/profiles/web/cordis.patch.yml 追加（若已有 dsh-comac-benchmark 条目则把 inject 改为 [tools, webServer]）：
#   - insert:
#       - id: dsh-comac-benchmark
#         name: /Users/Zhuanz/.dsh/plugins/dsh-comac-benchmark/index.js

# 2) client 半（工作台 UI）：包名形态挂载（T9 定论：双面孔件不能绝对路径）
mkdir -p ~/.dsh/profiles/web/node_modules
ln -sfn /Users/Zhuanz/projects/jerry-personal/JerryDSH-COMACBench/plugin/dsh-comac-workbench \
  ~/.dsh/profiles/web/node_modules/dsh-comac-workbench
# ~/.dsh/profiles/web/cordis.patch.yml 追加：
#   - insert:
#       - id: dsh-comac-workbench
#         name: dsh-comac-workbench

# 3) 首次安装需重启 dsh web（此后 bundle 变更 HMR 自动热替换）
# 4) UI 改动后：cd plugin/dsh-comac-workbench && node build.mjs（fail-loud，格式断言内置）
```

更新 host 插件需同时复制 `index.js` 和 `packs.js`；改判分逻辑请改仓库 `runners/`。

## 工程师评测与贡献入口（2026-09-06）

新增 `comac_pack_catalog`、`comac_pack_validate`、`comac_agent_run`、`comac_agent_result`。
使用方法见 [工程师指南](../../docs/aviation-quickstart.md)。`/comac/packs` 是只读 GET，复用同一 Python 预检结果；工作台“工程师入口”提供可复制命令和贡献反馈。

新入口优先用仓库 `.venv/bin/python`，可通过 `COMAC_BENCH_PYTHON` 指定解释器。
`comac_agent_run` 仅提交脱离启动请求，完成状态以 `run.json` 为准；不会把 PID 返回当作运行成功。
新评测包不自动登记进既有 registry；静态检查和校准通过后仍需工程审查。

`node plugin/dsh-comac-benchmark/test-packs.mjs` 验证新增工具、非法包零起跑和只读路由守卫；不启动原有全量 stub 测试。

## 验证

- `node smoke.mjs`（本目录）：mock ctx 逐工具冒烟——registry 38 项 / bench 详情 /
  stub 脱离起跑到 comac_results 端到端读数（曾跑通：stub 0/100 gate、
  non_physical ×100 与已知画像一致）

### CFD 研究证据准入

现有四个 pack/agent 工具及 `/comac/packs` 已转接 `comacbench.admission`，参数不变。CFD 包自动展示 Re=100/200/300 共 48 组研究；缺失、未知或摘要异常的研究附件阻断启动。CLI 改用 `python -m comacbench.admission`，完整原生文件校验用 `python -m comacbench.evidence --full`。研究候选带不替代公开 10% 容差，Re=200/300 尚不能调用评分。协议及便携依赖见 `docs/specs/cfd-evidence-admission-v1.md`。
