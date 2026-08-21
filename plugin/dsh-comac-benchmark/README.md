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

## 安装 / 更新

```bash
# 源码在仓库 plugin/dsh-comac-benchmark/（版本库内）；安装 = 拷两文件 + patch 条目
mkdir -p ~/.dsh/plugins/dsh-comac-benchmark
cp plugin/dsh-comac-benchmark/{index.js,package.json} ~/.dsh/plugins/dsh-comac-benchmark/
# ~/.dsh/profiles/web/cordis.patch.yml 追加：
#   - insert:
#       - id: dsh-comac-benchmark
#         name: /Users/Zhuanz/.dsh/plugins/dsh-comac-benchmark/index.js
# 新会话生效（当前会话不热载）
```

更新插件后重新 `cp` 两个文件即可；改判分逻辑请改仓库 `runners/`（无需动插件）。

## 验证

- `node smoke.mjs`（本目录）：mock ctx 逐工具冒烟——registry 38 项 / bench 详情 /
  stub 脱离起跑到 comac_results 端到端读数（曾跑通：stub 0/100 gate、
  non_physical ×100 与已知画像一致）
