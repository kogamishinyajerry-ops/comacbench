# oracle: PINN 粘性 Burgers（ν=0.01/π），IC/BC 硬约束 + PDE 残差
import numpy as np
import torch

torch.manual_seed(0)
np.random.seed(0)
torch.set_num_threads(4)

net = torch.nn.Sequential(
    torch.nn.Linear(2, 64), torch.nn.Tanh(),
    torch.nn.Linear(64, 64), torch.nn.Tanh(),
    torch.nn.Linear(64, 64), torch.nn.Tanh(),
    torch.nn.Linear(64, 1))

NU = 0.01 / np.pi

def hard_u(x, t):
    # u = (1-t̂)·(-sin(πx)) + t̂·(1-x̂²)·N  —— 精确满足 IC 与 u(±1,t)=0
    xh = x / 1.0
    th = t / 1.0
    return (1 - th) * (-torch.sin(np.pi * x)) + th * (1 - xh**2) * net(
        torch.cat([x, t], dim=1))

def pde_residual(x, t):
    x = x.clone().requires_grad_(True)
    t = t.clone().requires_grad_(True)
    u = hard_u(x, t)
    u_x = torch.autograd.grad(u, x, torch.ones_like(u), create_graph=True)[0]
    u_t = torch.autograd.grad(u, t, torch.ones_like(u), create_graph=True)[0]
    u_xx = torch.autograd.grad(u_x, x, torch.ones_like(u_x), create_graph=True)[0]
    return u_t + u * u_x - NU * u_xx

opt = torch.optim.Adam(net.parameters(), lr=1e-3)
N = 8192
for it in range(12001):
    x = torch.rand(N, 1) * 2 - 1
    t = torch.rand(N, 1)
    opt.zero_grad()
    r = pde_residual(x, t)
    loss = (r ** 2).mean()
    loss.backward()
    opt.step()
    if it in (4000, 8000):
        for g in opt.param_groups:
            g["lr"] *= 0.4
    if it % 3000 == 0:
        print(f"iter {it} res {loss.item():.3e}")

xs = np.linspace(-1, 1, 101)
ts = np.round(np.arange(1, 11) * 0.1, 6)
pred = np.zeros((101, 10))
for j, tv in enumerate(ts):
    with torch.no_grad():
        X = torch.tensor(xs, dtype=torch.float32).reshape(-1, 1)
        T = torch.full_like(X, float(tv))
        pred[:, j] = hard_u(X, T).numpy().ravel()
np.save("pred.npy", pred.astype(np.float64))
print("pred.npy written", pred.shape)
