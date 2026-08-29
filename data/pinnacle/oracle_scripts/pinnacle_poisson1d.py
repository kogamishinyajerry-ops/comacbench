# oracle: PINN u''+sin(x)=0, u=sin(x)（解析验证档）
import numpy as np
import torch

torch.manual_seed(0)
np.random.seed(0)
torch.set_num_threads(4)

net = torch.nn.Sequential(
    torch.nn.Linear(1, 32), torch.nn.Tanh(),
    torch.nn.Linear(32, 32), torch.nn.Tanh(),
    torch.nn.Linear(32, 32), torch.nn.Tanh(),
    torch.nn.Linear(32, 1))
opt = torch.optim.Adam(net.parameters(), lr=1e-3)

x_c = torch.rand(2048, 1) * 2 * np.pi  # collocation
x_b = torch.tensor([[0.0], [2 * np.pi]])
ones = torch.ones_like(x_c)
for it in range(8000):
    opt.zero_grad()
    xc = x_c.clone().requires_grad_(True)
    u = net(xc)
    u_x = torch.autograd.grad(u, xc, torch.ones_like(u), create_graph=True)[0]
    u_xx = torch.autograd.grad(u_x, xc, torch.ones_like(u_x), create_graph=True)[0]
    loss_pde = ((u_xx + torch.sin(xc)) ** 2).mean()
    loss_bc = ((net(x_b) - 0.0) ** 2).sum()
    loss = loss_pde + 10.0 * loss_bc
    loss.backward()
    opt.step()
    if it % 2000 == 0:
        print(f"iter {it} loss {loss.item():.3e}")

x = np.linspace(0.0, 2.0 * np.pi, 256).reshape(-1, 1)
with torch.no_grad():
    pred = net(torch.tensor(x, dtype=torch.float32)).numpy().astype(np.float64).ravel()
np.save("pred.npy", pred)
print("pred.npy written", pred.shape)
