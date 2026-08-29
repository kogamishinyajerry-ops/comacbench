# PROVENANCE — pinnacle.suite

> 上游：github.com/i207M/PINNacle（MIT，NeurIPS 2024）。2026-08-29 快照克隆
> （/tmp/asset_recon/PINNacle），revision 记 **pinnacle@2026-08-29-clone**。
> 任务形态：code_exec（exec_kind=pinnacle_rel_l2）——模型写 PyTorch PINN 训练脚本，
> 沙箱内训练写 pred.npy；冻结 loader 宿主执行算 rel L2（cfdb qoi_script 同款协议），
> 与 YAML 阈值二值比对。判分材料不经模型，LLM-judge 永不进判分。

## A. 镜像与派生

| 文件 | 来源 | 说明 |
| --- | --- | --- |
| data/pinnacle/ref/burgers1d.dat | 上游 ref/ 逐字复制 | COMSOL 6.0 导出，101 x × [t=0]+10 时刻列；判分取 t=0.1..1.0 十列 |
| data/pinnacle/ref/loaders/*.py | 本仓库自建（3 个） | 冻结判分 loader（stdlib+numpy），协议：`python3 loader <pred.npy>` → 末行 JSON {"rel_l2"} |
| data/pinnacle/oracle_scripts/*.py | 本仓库自建（3 个） | oracle PINN（GT verbatim writer 同款 trust 层级）；训练曲线/自检值见 oracle_calibration.json |
| data/pinnacle/thresholds.json | 本仓库标定 | 阈值 = max(3×oracle rel_l2, 任务级下限)：burgers1d 0.09 / helmholtz2d 0.01 / poisson1d 0.08 |
| data/pinnacle/oracle_calibration.json | 标定记录 | oracle 实测 rel L2（poisson1d 0.0263 / burgers1d 0.0276 / helmholtz2d 0.00023） |

- poisson1d / helmholtz2d 参考为题面**解析解**（loader 内闭式计算，零镜像）。
- MIT 允许镜像；再分发保留上游版权声明。

## B. 任务集（3 题）与设计决策

- pinnacle_burgers1d：ν=0.01/π，IC sin(-πx)，u(±1,t)=0；pred (101,10) 对应 t=0.1..1.0
  （参考场 t=0 列为 IC，不作为预测目标）。
- pinnacle_helmholtz2d：Δu+k²u=f 制造解 sin(πx)sin(πy)，k=3；pred (10201,) =
  101×101 grid(ij) C 序展平。
- pinnacle_poisson1d：u''+sin x=0，u=sin x；pred (256,)。冒烟难度档。
- **撤换记录**：原第三题"洞域 Laplace（方腔-4 圆孔）"经三轮 oracle 迭代
  （软边界 v1 0.52 / 强权 v2 0.73 / 距离函数硬约束 v3 1.17，PDE loss 卡死）
  确认对原生 PINN 不可训练——这与 PINNacle 论文"几何 BC 是核心挑战"的结论一致；
  撤换为 Helmholtz 制造解（git 历史留档）。给 LLM 出题的前提是 oracle 能稳过。
- 训练类任务 CPU 非逐位确定 → 不做双跑确定性（robustness 权重 0，YAML 声明）。

## C. 环境依赖（判分侧硬前提）

- 沙箱内 `import torch` 必须可用：torch 及其传递依赖须在解释器**主** site-packages
  （沙箱 `-s` 屏蔽 user-site）。2026-08-29 修复记录与部署冒烟命令见 env-matrix.md Phase-C。
- 新机器部署先跑：`python3 -s -E -c "import torch"`。
