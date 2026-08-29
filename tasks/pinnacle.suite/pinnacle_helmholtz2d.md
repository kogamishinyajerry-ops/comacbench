# PINN 基准 — Helmholtz 2D（制造解）

求解 Helmholtz 方程（制造解形式）：

    Δu + k²·u = f,   k = 3,  (x, y) ∈ [-1, 1]²
    f = (k² - 2π²)·sin(πx)·sin(πy)
    边界条件 u = 0（x=±1 与 y=±1 上制造解恒为 0）
    精确解 u(x, y) = sin(πx)·sin(πy)

## 输出规格

`pred.npy` 形状 **(10201,)**：101×101 网格点（x/y 均为 linspace(-1,1,101)，
np.meshgrid(indexing="ij") 后按 C 序展平——即先变 x 后变 y），给出 u。

## 训练建议

硬边界约束 u = (1-x²)(1-y²)·N_θ(x,y) 可精确满足零边界，只需训 PDE 残差；
MLP 2→64×4→1 tanh，Adam ~1e4 步即可到 1e-3 量级；固定种子。
## 交付形式（严格遵守）

输出**单个 ```python 代码块**：脚本在当前工作目录训练 PINN 并写出 `pred.npy`。
- 仅允许 PyTorch（CPU）与 numpy/标准库；固定随机种子保证可复现；
- 建议显存无关：`torch.set_num_threads(4)` 控制线程；训练预算见题面（墙钟 900s）；
- `pred.npy` 形状与网格规格逐题给定，判分脚本按规格加载，错形/非有限值判 0；
- 判分 = 相对误差 rel L2 = ||pred-ref||₂/||ref||₂ ≤ 阈值（阈值随题面给出，满分线）。
