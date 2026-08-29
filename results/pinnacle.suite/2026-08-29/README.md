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
| glm-5.3 | 3 | 3/3 | **0.7667** | 2/3 过阈；burgers1d rel 0.346 > 0.09（训练不充分） |
| minimax | 3 | 2/3 | **0.6667** | 2/3 过阈；helmholtz 候选脚本 1.4s 崩溃（code_not_executable） |

区分带：0（stub）<< 0.667 < 0.767 < 1.0（oracle）——健康。

## Oracle 逐题明细

| 任务 | rel_l2 | 阈值 | 训练时长 |
| --- | --- | --- | --- |
| pinnacle_burgers1d | 0.0276 | 0.09 | ~235s |
| pinnacle_helmholtz2d | 0.00023 | 0.01 | ~275s |
| pinnacle_poisson1d | 0.0263 | 0.08 | ~30s |

## 真实 LLM 逐题明细（2026-08-29）

| 任务 | glm-5.3 | MiniMax-M3 |
| --- | --- | --- |
| burgers1d | 0.346 ❌（未收敛到阈值内） | 0.0294 ✅（与 oracle 同量级） |
| helmholtz2d | 0.0052 ✅ | 崩溃 ❌（脚本 1.4s 退出） |
| poisson1d | 0.0013 ✅ | 0.00016 ✅ |

观察：两模型在解析参考的 1D/制造解题上稳定，分化在"非定常非线性 PDE 的训练充分性"
（glm burgers 欠训练）与"生成代码可执行性"（minimax helmholtz 崩溃）——区分维度正交，
与基准设计意图（code_exec 三层：可执行→收敛→精度）一致。

## 环境要点

- 沙箱 torch 可用性前提与部署冒烟命令：env-matrix.md Phase-C
  （typing_extensions 须在解释器主 site-packages，2026-08-29 修复）。
- 训练类 CPU 非逐位确定 → 不做双跑确定性（robustness 权重 0，YAML 声明）。
