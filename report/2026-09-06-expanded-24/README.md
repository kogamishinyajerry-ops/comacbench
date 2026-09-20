# 首次扩样协议：仅离线校准，未进入真实模型运行

此目录保留失败的离线校准证据，不算真实模型成绩。
任务上下文记录器错误地假定 provider 的首个参数是 TaskSpec，导致 18 道 QA 校准题 crash；
另有 ssb_341_40 在零容差下受 LibreOffice 浮点尾差影响，oracle 为 0.991。
本目录 requests=0。

已在独立的 [v2 实验目录](../2026-09-06-expanded-24-v2/)修正：
通过 runner 的 run_task 边界绑定上下文；仅 ssb_341_40 使用 1e-12 相对容差，
其他 5 道表格保持零容差。原始生产 runner、canonical 任务与 gold 未改变。
