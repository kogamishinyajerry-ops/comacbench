# 固定预算真实模型验证：协议通过，发现两处输入契约问题

2026-09-05；使用 MiniMax-M3，8 题 H0 单轮。原计划 DeepSeek-V4-Flash 的首次请求返回 402，余额接口确认不可用；失败原件独立保留，未重试或充值。随后在原总预算内切换已有 MiniMax 通道完成验证，不构成模型对比。

## 结果

| 组别 | 题数 | Gate 通过 | 满分题数 | 逐题原始分数 |
| --- | ---: | ---: | ---: | --- |
| 公开条款抽取 | 2 | 2 | 1 | 0.8889，1.0000 |
| 公开符合性/修订 | 2 | 2 | 1 | 1.0000，0.7143 |
| 隐藏符合性/修订 | 2 | 2 | 1 | 1.0000，0.7143 |
| 表格脚本 | 2 | 0 | 0 | 0，0 |

共 8 个真实模型结果、4 个 v1 manifest；6 题 Gate 通过，3 题满分。样本针对修复路径选择，且存在已发现的任务契约问题，不据此估计整体模型能力或发布排名。

**B02/B04 验收通过**：4 组相同配置重放均复用 2/2 缓存；8 个结果文件逐字节不变；重放阶段禁止 HTTP，新增生成请求为 0；4 组改变 seed 均被拒绝，产物不变。隐藏题 manifest 计数为 2，所选 IDs 有记录，结果不包含题面、答案正文或 ref/got 值。

**B03 的真实模型覆盖边界**：两份候选脚本都在打开输入文件时退出，尚未进入工作表契约与 LibreOffice 重算阶段。因此本轮证明失败能落盘并被安全复用，不能声称用真实模型验证了 B03 判分核心。B03 的 7 个集成用例和官方 oracle 25/25 证据仍见上一轮修复报告。

## 预算与用量

- 原预算：8 题、最多 12 次生成请求、累计最多 50,000 输出 token。
- 实际：MiniMax 成功调用 8 次，无解析重试；加 DeepSeek 失败 1 次，共 **9/12 次**。缓存检查没有付费调用。
- MiniMax usage：输入 **4,251** token（其中缓存 384）、输出 **14,236** token，合计 **18,487** token。输出包含推理；reasoning 明细由 API 返回，不额外加到 completion。
- DeepSeek 失败未返回 usage，完整保留 16,384 预留；已知输出加未知预留共 **30,620/50,000**，没有释放该未知额度去扩大样本。
- MiniMax 估算成本 **¥0.12786438，约 ¥0.13**。使用 [官方标准按量价格](https://platform.minimaxi.com/docs/guides/pricing-paygo)：输入/缓存读取/输出为每百万 token ¥2.10/¥0.42/¥8.40；请求未启用 priority。仅为公开单价估算，未对账，DeepSeek 失败不据此声称零费用。
- MiniMax 执行与缓存检查耗时 152.557 秒；准备、负例测试及 DeepSeek 通道检查不包含在此耗时内。

## 诊断与后续最小修复

1. **修订题参数名契约不一致**。`awc_rev_01.md` 明确要求 changed_params 使用题面打印的参数名；模型返回 `flap limit speed`，参考却要求 `flap_limit_speed_ktas`，因此 old/new 两字段未命中，得分 5/7。不能直接将这两项解释为模型算错。隐藏修订也为 5/7，需连同生成器统一审查，暂不披露隐藏答案或替它重判。
2. **表格缺少可执行的输入文件说明**。题面未列出实际暂存文件 `ssb_17_35_init.xlsx`、`ssb_22_47_init.xlsx`。模型分别尝试打开 `output.xlsx` 和 `input.xlsx`，触发 FileNotFoundError；两题原始结果为 `code_not_executable`、Gate=0。下一步应提供明确文件名/文件清单，并用原始数据核验任务上下文，而不是放宽判分或把缺文件算成部分通过。
3. `awx_ce_01` 的 8/9 来自输出条款号省略 `§`；题面要求逐字复制，当前严格判分保留。这与上述参考键名矛盾分别记录。

本轮没有更改任务、gold、grader 或分数，也没有依据结果追加模型请求。推荐先做 B05 的上述两处输入契约修复，再在新身份、新输出目录复跑相同样本。

## 文件与复核命令

- `experiment-protocol.md`、`protocol.json`：运行前登记、固定样本、源码/数据摘要、替代通道的剩余预算。
- `provider-preflight.json`：DeepSeek 402/不可用状态和 MiniMax 模型列表检查摘要。
- `requests.json`：每次请求的持久预留、实际 usage、响应 ID/模型和正文摘要，不存密钥或正文。
- `runs/`：8 个标准结果、4 个 manifest 和原生 summary。
- `summary.json`、`verification.json`：逐题分数、缓存检查、预算和成本。
- `budget_guard.py`、`run_experiment.py`、`test_budget_guard.py`：本次实验专用脚本。未修改 `runners/`，上一轮 runner 与测试源码 SHA256 均核对一致。

```sh
# 不联网：复核冻结摘要、结果、预算和缓存验收记录
.venv/bin/python report/2026-09-05-live-smoke-minimax/verify_artifacts.py

# 只联系本地虚构 HTTP 服务：预算负例测试，2 项通过
.venv/bin/python -m unittest discover -s report/2026-09-05-live-smoke-minimax -p 'test_budget_guard.py' -v

# 本次真实调用实际使用的入口；已有结果按身份续跑，保留累计预算
.venv/bin/python report/2026-09-05-live-smoke-minimax/run_experiment.py --execute
```

本次仅新增两处实验报告目录；既有源码改动、SciCode 资产删除、CFDB YAML 修改和历史结果均保留。没有提交或推送。
