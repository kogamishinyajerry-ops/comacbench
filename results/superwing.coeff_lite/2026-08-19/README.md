# superwing.coeff_lite 2026-08-19 运行索引（M4）

> 落点约定：`results/<registry_id>/<date>/<provider>/`。
> `assets_revision = superwing@hf-coeff-lite-2026-08-19`（系数层镜像 ~10MB，无体数据）。
> 100 任务 = 几何外推 70（test 424 构型零交集）+ 内插 30（train 构型，泄漏风险层）。

| 子目录 | provider/model | gate | 任务均分 | 关键观察 |
| --- | --- | --- | --- | --- |
| `stub/` | stub（固定 cl=0.3/cd=0.03/cm=0） | 100/100 | 0.4 | 全部在物理包络内（gate 过）但数值错 → physics 0 |
| `oracle/` | 真值 | 100/100 | **1.000** | 判分管线全验证 |
| `minimax-m3/` | MiniMax-M3 | 100/100 | 0.4415 | physics 均值：几何外推 0.080 / 内插 0.044；CL 相对误差 ~240%、CD ~94%、CM ~168% |
| `glm-4.6/` | GLM-4.6 | 100/100 | 0.4135 | physics 几何外推 **0.025** / 内插 **0.017**；CL 相对误差 300-479%——gate 全过但数值比 M3 更离谱，跨声速系数回归对 GLM 更难（2026-08-21 补齐）|

**能力边界 + ML 正例参照（2026-08-19）**：LLM（M3）physics 内插 0.044/外推 0.080——无法直接做
系数回归（gate 全过但数值远超容差）；**ML 基线（RandomForest 100 trees，sklearn）physics
内插 0.828 / 几何外推 0.485**（`ml-superwing/`）——同一判分管线下 ML 与 LLM 差一个数量级，
正例参照成立。后续可接 AeroTransformer 级深度模型（torch 可选）刷新上限。

- 划分纪律：ge（几何外推）与 it（内插）分组独立报告（summary 首表）；本批条件外推 N/A
  （每构型固定 8 点工况网格）；
- CRMpert 跨家族迁移测试：待议（独立数据集，需单独获取+许可核对，PROVENANCE 已注记）。

复现：
```bash
cd benchmarks && python3 -m runners.field_prediction \
  --tasks tasks/superwing.coeff_lite --out results/superwing.coeff_lite/2026-08-19/<provider> \
  --provider <p> [--model <m>] --seed 0
```
