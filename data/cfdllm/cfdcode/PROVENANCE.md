# CFDCodeBench 数据镜像溯源（PROVENANCE）

> assets_revision: `cfdcode@3b46d30+kaggle_v1`
> 镜像日期: 2026-08-19 · 镜像执行: M2 会话（dev 终端）

## 镜像内容

| 文件/目录 | 来源 | 说明 |
| --- | --- | --- |
| `prompt/PDE_TASK_QUESTION_ONLY.json` | Kaggle `nithinsekhar/cfdcodebench` v1（sha256 `d76d2c59…2bbee65f`） | 24 任务结构化题面（官方指定数据源） |
| `prompt/prompts.json` | 同上（sha256 `54df3736…f4a96584`） | 官方成品提示（题面 .md 逐字取自此处） |
| `solution/`（26 文件） | 同上 | gold 参考实现；2 个多余解文件 + 1 个命名不齐对（2D_Possion↔2D_Poisson_Equation） |
| `gold_outputs/`（31 npy） | 本 harness 离线预计算 | gold 运行产物，逐文件 sha256 锁定于 `gold_outputs_digests.json` |
| `upstream_utils.py.reference` 等 | GitHub `NREL-Theseus/cfdllmbench` @ `3b46d30` | 上游判分/管线参考（只读，不参与运行） |

## 许可证据链（先许可证后镜像，2026-08-19 核验）

与 cfdquery 同源同链：GitHub 仓库 LICENSE = BSD-3-Clause + 论文 arXiv:2509.20374
"CFDLLMBench is released under the terms of the BSD 3-Clause License"（覆盖全部子基准含题目与 gold）；
Kaggle 页 license 徽标 "Unknown"（上传者未选），不改变数据本体许可。镜像放行。

## 任务口径：24 -> 15（如实排除记录）

gold 预计算（2026-08-19，dev 终端）24 个任务中 9 个不可用：

| 排除任务 | 原因（实测） |
| --- | --- |
| 1D_KdV_Burgers / 2D_Rayleigh_Benard / 2D_Shear_Flow_With_Tracer / Lane_Emden / Pipe_Flow_Disk_EVP | gold 依赖 `dedalus`（谱方法包），本机构建失败（FFTW 系统依赖不可得；brew 目录无写权限） |
| 2D_Navier_Stokes_Cavity | gold 自身压力泊松 1e4 次迭代不收敛（诊断副本放宽到 2e6 仍不收敛）——上游 gold 缺陷 |
| 2D_Unsteady_Heat_Equation | gold 运行 >1800s（超时） |
| 2D_Diffusion | 上游不一致：prompt 要求存 `p`，gold 只存 `u` |
| Fully_Developed_Turbulent_Channel_Flow | 上游不一致：prompt 要求存 `u`，gold 存 `u1..u5`（各湍流模型变体） |

恢复条件：dedalus 系环境可用（装 FFTW+fftw-dev 头文件后重装）可救回 5 题；其余 4 题需上游修复。
gold 运行注意：7 个 gold 脚本含 `plt.show()`（无头挂死），预计算用 wrapper 中和 show 后运行；
Cylinder/Lid_Driven 两题 gold 写死相对路径 `../../PDE_Benchmark/results/solution/`，需对应目录布局。

## 判分口径（官方语义）

- 形状不一致：`scipy.ndimage.zoom` 一阶插值对齐（官方 `interpolate_to_match`）；
- 指标：MSE/MAE/RMSE/Cosine/R²/NMSE（官方 `compute_losses`，sklearn 实现）；
- physics 子分 = 逐变量 mean(clamp01(Cosine), clamp01(R²)) 再按变量均值（本 harness 口径，
  官方只报指标不折分——如实标注）；
- gate：脚本跑通 + 全部 save_values npy 产出 + 无 NaN/Inf。

## 重取方式

```bash
curl -sL "https://www.kaggle.com/api/v1/datasets/download/nithinsekhar/cfdcodebench" -o cfdcode.zip
unzip cfdcode.zip   # -> CFDCodeBench/{prompt,solution}
shasum -a 256 CFDCodeBench/prompt/*.json   # 对照上表
# gold_outputs 重算：见 runners/gen_tasks_cfdcode.py 注释（wrapper 中和 plt.show + 目录布局）
```
