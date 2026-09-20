# MiniMax 通道：运行前补充登记

DeepSeek 的首个生成请求返回 HTTP 402，随后只读余额接口确认 `is_available=false`。该次尝试没有结果，也没有自动重试。原协议、manifest 和失败账本保留在 `../2026-09-05-live-smoke`。

为完成已授权的真实模型验证，改用本机已有的 `MINIMAX_M3_API_KEY` 和 `/models` 列表确认存在的 `MiniMax-M3`。这是替代通道验证，不做 DeepSeek/MiniMax 能力对比。

- 端点：`https://api.minimaxi.com/v1/chat/completions`，使用现有 `openai_compat`，原请求 `max_tokens=16384`、temperature=0；不修改 runner 或提示词。
- 固定样本、seed=20260905、H0、缓存/错 seed 验收均沿用 [首轮预登记](../2026-09-05-live-smoke/experiment-protocol.md)。本目录另建任务快照、4 组输出和预算账本，避免跨模型混用。
- 本轮总预算仍为 12 次请求、50,000 输出 token。先前失败的 1 次请求和 16,384 token 未知预留完整扣除，本通道最多 **11 次请求、33,616 输出 token**。失败账本摘要同时冻结；读取它发生变化时本入口拒绝执行。
- 仍先预留每次请求的最大输出，余额不足停止；不追加预算、不为追求高分改题或反馈修复。
- 只记录 token 用量和可核验的价格估算；API 余额不会充值或自动购买额度。

启动及受预算约束的续跑：

```sh
.venv/bin/python report/2026-09-05-live-smoke-minimax/run_experiment.py --execute
```

已通过 2 个本地 HTTP 负例测试：请求上限在联网前生效，重启仍保留额度；输出预留不足时不联网，未知用量继续占用完整预留。脚本不保存 API 密钥，不改请求与响应正文。

来源：[MiniMax Chat Completions](https://platform.minimaxi.com/docs/api-reference/text-chat-openai.md)、[模型列表接口](https://platform.minimaxi.com/docs/api-reference/models/openai/list-models)、[按量价格](https://platform.minimaxi.com/docs/guides/pricing-paygo.md)。
