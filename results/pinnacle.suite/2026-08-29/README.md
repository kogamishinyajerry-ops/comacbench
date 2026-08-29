# pinnacle.suite 2026-08-29 首批基线（3 任务）

> 来源：PINNacle（MIT，NeurIPS 2024）转化；任务 = 模型写 PyTorch PINN 训练脚本，
> 沙箱内训练写 pred.npy，冻结 loader 宿主算 rel L2，与阈值（oracle 实测 ×3）二值比对。
> 标定与撤换记录（洞域 Laplace 三轮不可训练 → Helmholtz 制造解）见
> data/pinnacle/PROVENANCE.md §B。

## 结果矩阵

| provider | 任务数 | gate | mean | 备注 |
| --- | --- | --- | --- | --- |
| oracle | 3 | **3/3** | **1.0000** | 判分管线自检满分 ✅（训练实跑，CPU 275-440s/题） |
| stub | 3 | 0/3 | 0.0000 | 确定性垃圾脚本全灭（缺 pred.npy）✅ |

## Oracle 逐题明细

| 任务 | rel_l2 | 阈值 | 训练时长 |
| --- | --- | --- | --- |
| pinnacle_burgers1d | 0.0276 | 0.09 | ~235s |
| pinnacle_helmholtz2d | 0.00023 | 0.01 | ~275s |
| pinnacle_poisson1d | 0.0263 | 0.08 | ~30s |

## 环境要点

- 沙箱 torch 可用性前提与部署冒烟命令：env-matrix.md Phase-C
  （typing_extensions 须在解释器主 site-packages，2026-08-29 修复）。
- 训练类 CPU 非逐位确定 → 不做双跑确定性（robustness 权重 0，YAML 声明）。
- 真实 LLM 基线（glm/minimax）待补：每题训练墙钟 ×3 题，预计 ~30-40 min/provider。
