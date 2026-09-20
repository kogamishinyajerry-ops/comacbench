# 真实模型固定预算小样本：运行前登记

登记时间：2026-09-05。目标是验证 B02/B04 的真实调用、结果身份与缓存重放，以及 B03 在模型表格脚本上的实际判分。任务选择不随得分调整。

| 固定项 | 值 |
| --- | --- |
| 模型 / 端点 | `deepseek-v4-flash` / `https://api.deepseek.com`；启动前 `/models` 确认存在 |
| provider / 温度 / seed | `openai_compat` / 0 / 20260905；seed 用于本地抽样，现有请求体不发送远端采样 seed |
| 推理模式 | provider 默认启用；本次不改变现有 runner 请求内容 |
| Harness | H0 单轮，无 scaffold、无判分反馈、无看分追加调用 |
| 请求上限 | 12 次生成请求，包含 provider 解析重试；模型列表查询不生成 token |
| 输出上限 | 累计 50,000 completion tokens（含推理）。每次请求先预留原请求的 16,384 上限，余额不足则停止，不缩短请求或更换模型 |
| 其他限额 | 单次请求体 32,000 bytes；首个账本建立后 1,200 秒内允许发起请求；单次网络等待最多 180 秒 |
| 异常策略 | 传输或 usage 不明确即停止，完整预留保留，不自动重试；保留部分结果，不补写为通过 |
| 输出目录 | 本报告下 `runs/{extract,compliance,hidden,formula}`，与历史成绩分离 |

样本固定为 8 题：

- `awext.clause_extract`：`awx_ce_01`、`awx_ce_02`，公开条款抽取。
- `awcom.compliance`：`awc_acam_01`、`awc_rev_01`，公开符合性方法与修订影响。
- `awcom.compliance --hidden 2`：由既有分层抽样按 seed=20260905 选择 2 题，参考答案与动态题面不额外落盘。
- `spreadsheetbench.verified_subset`：`ssb_17_35`、`ssb_22_47`，筛选表格和排序；后者覆盖 LibreOffice 工作表改名兼容。

这是针对修复路径的便利样本，不能据此估计完整基准能力、宣称泛化或比较模型排名。ACX 条款来自仓库的虚构合成数据，不是适航业务验收。

`protocol.json` 冻结任务、源代码和执行配置。原 YAML/题面逐字复制进 `workspace/tasks`；`workspace/data` 引用现有数据，原件不修改。表格候选沿用现有隔离解释器，子进程环境不含 API 密钥。

`budget_guard.py` 仅在实验进程内拦截实际 HTTP 边界：写预留账本、透传原始请求、记录响应 usage/id/model/hash，然后把未修改响应交给原 runner。账本不含凭据、提示词、答案或推理正文；隐藏结果继续通过原脱敏流程。预算身份与 runner 身份分别记录，不替换既有协议。

安全复跑入口：

```sh
.venv/bin/python report/2026-09-05-live-smoke/run_experiment.py --execute
```

该命令检查冻结摘要和既有预算账本，沿用 `--resume`。底层各 manifest 的标准 CLI 记录用于检查参数；需继续消耗预算时使用上述入口，不绕开账本直接启动底层命令。最终自动检查相同身份缓存逐字节不变、改变 seed 被拒绝，检查阶段禁止 HTTP，因此不能产生额外账单。

机械验收：8 个标准 result、4 个含 v1 身份的 manifest；每组最终题数和缓存计数一致；相同身份重放新增请求为 0；错 seed 不修改任何既有产物；账本请求不超过 12、输出已用加未决预留不超过 50,000。模型低分本身不是协议失败，必须逐题如实报告。

成本按响应 usage 单独估算，不拿估算代替账户账单。2026-09-05 实时读取的 [DeepSeek 官方价格表](https://api-docs.deepseek.com/quick_start/pricing/)：Flash 非高峰输入未缓存/缓存/输出分别为每百万 token $0.22/$0.007/$0.66，高峰为其两倍。周一至周五 UTC 01–04、06–10 为高峰；本次日期为周六。生成和 usage 字段见 [官方 Chat Completions 文档](https://api-docs.deepseek.com/api/create-chat-completion/)。
