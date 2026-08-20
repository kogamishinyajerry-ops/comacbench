# SuperWing-Coeff-Lite 数据镜像溯源（PROVENANCE）

> assets_revision: `superwing@hf-coeff-lite-2026-08-19`
> 镜像日期: 2026-08-19 · M4 会话（dev 终端）

## 镜像内容（仅系数层，不触体数据）

| 文件 | 来源 | sha256 | 说明 |
| --- | --- | --- | --- |
| `configs.dat` | HF `yunplus/SuperWing` | 见 sha256.txt | 4239 构型 × 55 列（shape_idx + 38 几何参数 + 8 Mach + 8 AoA） |
| `index.npy` | 同上 | 见 sha256.txt | 28856 样本 × 12（idx/aoa/mach/ref_area/half_span/cl/cd/cm ×solver×surface） |
| `train.parquet` | 同上 | 见 sha256.txt | 25985 样本 / 3815 构型（列名与 index.npy 对齐） |
| `test.parquet` | 同上 | 见 sha256.txt | 2871 样本 / 424 构型（**与 train 构型零交集**） |
| `training_samples_index.txt` | 同上 | 见 sha256.txt | 训练样本索引（25985 行） |
| `upstream_README.md` | 同上 | 见 sha256.txt | 官方数据说明（列定义/系数定义/通道说明） |

## 许可证据链（先许可证后镜像，2026-08-19 核验）

- HF 数据集 README YAML `license: cc-by-sa-4.0` → 与 registry `confirmed-dataset` 一致；
- **SA 传染性（CC BY-SA 关键约束）**：派生评测子集须按同许可发布策略（scoring/README.md
  §8 口径）；本 harness 派生物 = 任务 YAML/题面（含几何参数与真值子集），随仓库发布时
  声明 CC BY-SA 4.0 归属 SuperWing 原作者（Tsinghua AeroLab，arXiv:2512.14397）；
- 仅镜像系数层（~10MB），**不下载** data_surf(26.7GB)/data_vol(3.2TB)/origingeom/geom0
  体数据——与 registry「仅取系数层，不下载 3.49TB 体流场」一致。

## 数据校验（镜像时核验）

- 28856 样本 = train 25985 + test 2871；4239 构型 = train 3815 + test 424；
- **划分纪律**：test 构型 ∩ train 构型 = ∅（按几何构型分组，满足 scoring/README.md §6）；
- 物理包络（train 实测）：cl∈[-0.413,1.104]、cd∈[0.008,0.152]、cm∈[-0.426,1.321]
  （gate 用放宽包络 cl[-0.5,1.2]/cd[0,0.2]/cm[-0.5,1.5]）；
- 系数真值取 `*_solver`（RANS ADflow 积分）；`*_surface` 为表面积分（未纳入首批任务，
  待议——二者差异可作为额外判分维度）。

## 任务口径（field_prediction）

- 100 任务 = 几何外推 70（test 构型）+ 内插 30（train 构型，泄漏风险层——类比公共可比层）；
- 输入 = 38 几何参数（configs.dat）+ (aoa, mach)；目标 = cl/cd/cm；
- 判分 = gate（JSON 可解析 + 系数在物理包络）→ physics（相对误差带：cl/cm 5%、cd 10%，
  分档 1.0/0.5/0.25/0）→ requirements（字段完备）；划分纪律在聚合层分组报告；
- **CRMpert 迁移设定（registry/scoring §6）**：CRMpert 为独立数据集（AeroTransformer），
  未包含在本 HF 仓库；首批以 SuperWing 自带 test.parquet（424 构型）为几何外推组，
  CRMpert 跨家族迁移测试进待议（需单独获取 CRMpert 并核对许可）。

## 重取方式

```bash
cd benchmarks/data/superwing/coeff_lite
for f in configs.dat index.npy train.parquet test.parquet training_samples_index.txt; do
  curl -sL "https://huggingface.co/datasets/yunplus/SuperWing/resolve/main/$f" -o $f
done
shasum -a 256 configs.dat index.npy train.parquet test.parquet  # 对照 sha256.txt
```
