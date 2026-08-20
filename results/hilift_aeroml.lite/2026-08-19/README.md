# hilift_aeroml.lite 2026-08-19 运行索引（batch-2）

> 落点约定：`results/<registry_id>/<date>/<provider>/`。
> `assets_revision = hilift@hf-lite-2026-08-19`（系数层 1800 样本 + 180 构型几何参数）。
> 100 任务 = 几何外推 70（36 保留构型）+ 内插 30（144 训练构型）。

| 子目录 | provider/model | gate | 任务均分 | 关键观察 |
| --- | --- | --- | --- | --- |
| `stub/` | stub | 0/100 | 0 | non_physical ×100（stub 值超高升力包络）|
| `oracle/` | 真值 | **100/100** | **1.000** | 判分管线全验证（含 cm 正值包络修正）|
| `minimax-m3/` | MiniMax-M3 | 100/100 | 0.4855 | physics 内插 0.186 / 几何外推 0.124；CL err ~48-53%、CD ~40-48%、**CM ~218-353%**——与 superwing 同结论：LLM 无法直接系数回归（高升力 CM 尤差）|
| `glm-4.6/` | GLM-4.6 | 100/100 | 0.4885 | physics 内插 0.142 / 几何外推 **0.150**；**CM err 338-370%**（比 M3 更差）——高升力俯仰力矩对两家 LLM 同为难区，与 ML 正例（0.88/0.82）差 ~6×（2026-08-21 补齐）|
| `ml-hilift/` | RF 正例参照（ml_hilift） | 100/100 | 0.904 | physics 内插 **0.883** / 几何外推 **0.821**（CL 2-3%/CD 3-4%/CM 16-17%）；训练 1410 行=36 保留构型全剔除+30 内插测试行剔除，详见其 README |

- 分离涡标签/截面分布在体数据内，首批仅系数层（PROVENANCE 已注记）。

复现：
```bash
cd benchmarks && python3 -m runners.field_prediction \
  --tasks tasks/hilift_aeroml.lite --out results/hilift_aeroml.lite/2026-08-19/<provider> \
  --provider <p> [--model <m>] --seed 0
```
