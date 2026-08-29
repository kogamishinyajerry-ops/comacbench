# oracle: Helmholtz 2D（制造解 sin(πx)sin(πy)，k=3，硬边界约束）
import numpy as np
import torch

torch.manual_seed(0)
np.random.seed(0)
torch.set_num_threads(4)

A = np.pi   # 制造解波数
K = 3.0     # Helmholtz k

net = torch.nn.Sequential(
    torch.nn.Linear(2, 64), torch.nn.Tanh(),
    torch.nn.Linear(64, 64), torch.nn.Tanh(),
    torch.nn.Linear(64, 64), torch.nn.Tanh(),
    torch.nn.Linear(64, 1))

def hard_u(x, y):
    g = (1 - x ** 2) * (1 - y ** 2)   # 边界精确为 0
    return g * net(torch.cat([x * 1.0, y * 1.0], dim=1))

def pde_residual(x, y):
    x = x.clone().requires_grad_(True)
    y = y.clone().requires_grad_(True)
    u = hard_u(x, y)
    u_x = torch.autograd.grad(u, x, torch.ones_like(u), create_graph=True)[0]
    u_y = torch.autograd.grad(u, y, torch.ones_like(u), create_graph=True)[0]
    u_xx = torch.autograd.grad(u_x, x, torch.ones_like(u_x), create_graph=True)[0]
    u_yy = torch.autograd.grad(u_y, y, torch.ones_like(u_y), create_graph=True)[0]
    f = (K ** 2 - 2 * A ** 2) * torch.sin(A * x) * torch.sin(A * y)
    return u_xx + u_yy + K ** 2 * u - f

opt = torch.optim.Adam(net.parameters(), lr=2e-3)
N = 8192
for it in range(10001):
    x = torch.rand(N, 1) * 2 - 1
    y = torch.rand(N, 1) * 2 - 1
    opt.zero_grad()
    loss = (pde_residual(x, y) ** 2).mean()
    loss.backward()
    opt.step()
    if it in (5000, 8500):
        for g_ in opt.param_groups:
            g_["lr"] *= 0.4
    if it % 5000 == 0:
        print(f"iter {it} pde {loss.item():.3e}", flush=True)

xs = np.linspace(-1, 1, 101)
X, Y = np.meshgrid(xs, xs, indexing="ij")
with torch.no_grad():
    P = torch.tensor(np.stack([X.ravel(), Y.ravel()], axis=1), dtype=torch.float32)
    pred = hard_u(P[:, 0:1], P[:, 1:2]).numpy().astype(np.float64).ravel()
ref = (np.sin(A * X) * np.sin(A * Y)).ravel()
rel = float(np.linalg.norm(pred - ref) / np.linalg.norm(ref))
np.save("pred.npy", pred)
print("pred.npy written", pred.shape, "self-check rel_l2 =", rel)
