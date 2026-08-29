# PINN 基准 — 粘性 Burgers 方程（1D 非定常）

求解粘性 Burgers 方程：

    u_t + u·u_x = ν·u_xx,   ν = 0.01/π
    定义域 x ∈ [-1, 1], t ∈ [0, 1]
    初始条件 u(x, 0) = -sin(πx)
    边界条件 u(±1, t) = 0

参考解：COMSOL 高精度数值解（PINNacle ref/burgers1d.dat）。

## 输出规格

`pred.npy` 形状 **(101, 10)**：x 方向 101 个均匀点（-1 到 1，与参考场一致），
t 方向 10 列对应 t = 0.1, 0.2, …, 1.0（不含 t=0）。判分与参考场逐点相对 L2。

## 训练建议

MLP（如 2→64×4→1, tanh），Adam ~2e4 步（lr 1e-3，可分段衰减）即可达标；
固定 `torch.manual_seed(0)` + `np.random.seed(0)`。
## 交付形式（严格遵守）

输出**单个 ```python 代码块**：脚本在当前工作目录训练 PINN 并写出 `pred.npy`。
- 仅允许 PyTorch（CPU）与 numpy/标准库；固定随机种子保证可复现；
- 建议显存无关：`torch.set_num_threads(4)` 控制线程；训练预算见题面（墙钟 900s）；
- `pred.npy` 形状与网格规格逐题给定，判分脚本按规格加载，错形/非有限值判 0；
- 判分 = 相对误差 rel L2 = ||pred-ref||₂/||ref||₂ ≤ 阈值（阈值随题面给出，满分线）。
