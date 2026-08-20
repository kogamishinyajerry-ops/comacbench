# hilift_aeroml.lite ML 正例基线（ml_hilift，2026-08-20 运行，批次日期 2026-08-19）

> 与 `superwing.coeff_lite/2026-08-19/ml-superwing/` 同款：RandomForest(100 trees,
> sklearn, seed=0)，作 field_prediction 的**正例参照**（证明判分管线对好答案是通的），
> 非被测 LLM。

## 训练设置（划分纪律与生成器同口径）

- 特征 = 8 高升力几何参数（geo_values_all.csv）+ AoA；目标 = cl / cd / cm；
- 训练集 = force_mom_all.csv 1800 行中剔除：
  - 36 个保留构型全部 360 行（生成器 RNG seed 20260819 抽取；70 道 ge 题实际
    只覆盖其中 32 个构型，其余 4 个虽未入题同样保留，双保险校验见
    `providers.py::_train_hilift_ml`——任务 YAML 反推 ge 集 ⊆ RNG 保留集）；
  - 30 个内插测试行 (构型, 迎角)；
  - 即 **1410 行 / 144 训练构型**，与任务划分文档口径一致；
- 基线结论口径：内插（it）= 训练构型保留迎角；几何外推（ge）= 保留构型全迎角。

## 结果

| 组 | n | gate | physics 均值 | CL rel_err | CD rel_err | CM rel_err |
| --- | --- | --- | --- | --- | --- | --- |
| 内插 it | 30 | 30/30 | **0.8833** | 1.9% | 2.9% | 15.9% |
| 几何外推 ge | 70 | 70/70 | **0.8214** | 2.6% | 3.5% | 17.3% |

对照（同一判分管线）：

| 组 | MiniMax-M3（LLM） | ML (RF) | 差距 |
| --- | --- | --- | --- |
| 内插 physics | 0.186 | **0.883** | ~4.7× |
| 几何外推 physics | 0.124 | **0.821** | ~6.6× |

## 观察

1. **结论与 superwing 互相印证**：同一管线下 ML 与 LLM 差近一个数量级——
   field_prediction 维度的「LLM 不会」在高升力构型上再次成立；
2. **hilift 的几何外推衰减远小于 superwing**（0.82 vs 0.49）：8 维高升力几何空间
   + 每构型全迎角覆盖，RF 近邻内插裕度更大；superwing 38 维参数空间稀疏更甚；
3. **CM 对 RF 同样最难**（15-17% vs CL 2-3%）：方向上呼应 LLM 的 CM 218-353%
   相对误差（CM 最难），但幅度低一个数量级以上；且 WMLES 真值 CM 本身统计
   不确定度最高（csv 含 stdev/ci95），15% 附近或已接近真值噪声地板。

复现：`python3 -m runners.field_prediction --tasks tasks/hilift_aeroml.lite
--out results/hilift_aeroml.lite/2026-08-19/ml-hilift --provider ml_hilift --seed 0`
（完整命令见 run_manifest.json `rerun_command`。）
