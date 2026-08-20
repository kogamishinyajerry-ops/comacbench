# HiLiftAeroML-Lite 数据镜像溯源（PROVENANCE）

> assets_revision: `hilift@hf-lite-2026-08-19`
> 镜像日期: 2026-08-19 · batch-2 会话（dev 终端）

## 镜像内容（仅系数元数据层，~280KB）

| 文件 | 来源 | 说明 |
| --- | --- | --- |
| `force_mom_all.csv` | HF `nvidia/HiLiftAeroML`（sha256 `f06527cc…0687aabb`） | **1800 样本全量系数层**：180 构型 × 10 迎角（4-22°），列含 cd/cl/cm + 压差/粘性分解 + stdev/stderr/ci95 |
| `data_quality_README.md` / `data_quality_SHA256SUMS` | 同上 | 数据质量说明与校验和 |
| `upstream_README.md` | 同上 | 官方数据集说明 |

## 许可证据链（先许可证后镜像，2026-08-19 核验）

HF 数据集 README YAML `license: cc-by-4.0` → 与 registry `confirmed-dataset` 一致。
BY 归属：Neil Ashton (contact@caemldatasets.org)，NASA CRM-HL 高升力构型 WMLES 数据集。

## 未镜像（如实记录）

- 体数据 `volume_*.vtu.tgz`（每样本 ~23GB）与边界面数据 `boundary_*.vtu.tgz`（~12GB）——
  registry 明确 66.9TB 体数据不进日常 Harness；
- 分离涡标签 / 截面分布（registry content 提及）位于体/面数据内，首批仅接系数层
  （与 superwing.coeff_lite 同口径），扩展层进待议。

## 任务口径（field_prediction，复用 superwing 同款 adapter）

- 输入 = GeoID（构型标识）+ AoA → 目标 cd/cl/cm；
- 注意：与 superwing 不同，**几何参数不可直接获取**（每构型的 stl/stp 在体数据目录内，
  ~50-200MB/个）——首批任务以 (GeoID, AoA) 为条件做系数预测（构型身份嵌入问题），
  几何参数化扩展待议；
- 划分纪律：180 构型按几何分组划分（内插 = 训练构型的保留迎角；几何外推 = 保留构型全部迎角）。

## 重取方式

```bash
curl -sL "https://huggingface.co/datasets/nvidia/HiLiftAeroML/resolve/main/force_mom_all.csv" -o force_mom_all.csv
shasum -a 256 force_mom_all.csv   # 应 == f06527cc…0687aabb
```
