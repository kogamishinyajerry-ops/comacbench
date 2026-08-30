# PROVENANCE — unifoil.airfoil（transi 系数层 Lite）

> 上游：HF 数据集 rkanchi/UniFoil（**CC BY-SA 4.0**，数据集卡片核验 2026-08-29；
> 论文 arXiv:2505.21124）。UniFoil 全量 2.2TB（38 文件），本镜像仅取**系数层 Lite**。

## A. 镜像内容

| 文件 | 大小 | 内容 |
| --- | --- | --- |
| data/unifoil/unifoil_transi_coeff.csv | 7.9MB | **63,372 行 / 4,618 翼型** 的气动系数表：airfoil, case, mach (0.10-0.85), aoa_deg (-2..6), reynolds (1e6-1e7), cl, cd, case_file |
| data/unifoil/extract_from_zip.py | — | 可重放抽取脚本（重放校验 2026-08-29：与镜像 CSV 逐字节一致） |

- 源文件：`transi/airfoil_data_from_simulations.zip`（342,859,366B，
  sha256 `ac2ea66c96f30ddf680dcba1550a4bc05b4810c5386de9bdbf7cf20940b1d84a`）——
  zip 本体不入 git（体量），按上 sha256 可重新下载并用脚本重放。
- 抽取含 float 宽容解析（科学计数法 CL/CD）；bad=0（63,372/63,372 全收）。

## B. 覆盖范围与后续

- transi 族（转捩档，SA + e^N）系数层已收；NLF/FT 族（nlf_turb 889MB、
  ft_turb_cutout_1..4 各 ~1.2-1.3GB）的系数层同格式，按需扩镜像。
- 场数据（cutout/CGNS，数十 GB/文件）**不镜像**——field_prediction 任务如需场参考
  另行评审体量。
- **SA 传染性注意**（同 superwing 策略）：本 Lite 子集为 CC BY-SA 4.0 派生，
  对外发布须同许可。

## C. 任务转化路径（未做，立此存照）

- field_prediction 任务族：给定翼型几何参数/工况 → 预测 Cl/Cd，判分 vs 本表
  （held-out 划分按翼型分组防泄漏）；适配 field_prediction adapter 的
  表格回归模式（superwing.coeff_lite 同款）。
