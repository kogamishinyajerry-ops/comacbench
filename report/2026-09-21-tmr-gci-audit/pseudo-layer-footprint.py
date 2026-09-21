"""沿程足迹扫描：近壁 k / u / TVR 随 x 的分布，定位 k 污染的起点。

在仓库外，一次性诊断工具。
"""
import sys

sys.path.insert(0, "D:/comacbench")
from runners.tmr_cf import read_reference, _interp  # noqa: E402

U = 50.0
SLICE = "C:/Users/Kogami/cb_dl/tmr/run2/field_side273.daten"

rows = []
for ln in open(SLICE, encoding="utf-8", errors="replace"):
    ln = ln.strip()
    if not ln or ln.startswith("#"):
        continue
    q = ln.split()
    if len(q) >= 8:
        rows.append([float(v) for v in q])

cols = {}
for r in rows:
    cols.setdefault(round(r[1], 8), []).append(r)
xs = sorted(cols)

print("=" * 104)
print("A) 近壁逐层 k / u / TVR 随 x 的分布（层索引固定，看污染从哪开始）")
print("=" * 104)
print("     x       k[0]       k[8]       k[16]      k[32]      k[64]      k[104]     u[0]     TVR[0]")
for v in xs[::6]:
    col = sorted(cols[v], key=lambda r: r[2])
    g = lambda i, c: col[i][c] if i < len(col) else float("nan")
    print(f"{v:9.5f}  {g(0, 4):10.4g} {g(8, 4):10.4g} {g(16, 4):10.4g} {g(32, 4):10.4g} "
          f"{g(64, 4):10.4g} {g(104, 4):10.4g} {g(0, 6):8.4f} {g(0, 5):9.2f}")

print()
print("=" * 104)
print("B) 取 z≈5e-7（首层）与 z≈1.1e-3、z≈1.0e-2 三条水平线，看 k 的沿程足迹")
print("=" * 104)
zi = None
for v in xs:
    col = sorted(cols[v], key=lambda r: r[2])
    if zi is None:
        zi = [min(range(len(col)), key=lambda i: abs(col[i][2] - t))
              for t in (5e-7, 1.1e-3, 1.0e-2)]
print("     x       z=5e-7      z=1.1e-3    z=1e-2     u(z=5e-7)   u(z=1e-2)  TVR(z=5e-7)")
for v in xs[::4]:
    col = sorted(cols[v], key=lambda r: r[2])
    if len(col) < 192:
        continue
    a, b, c = [col[i] for i in zi]
    print(f"{v:9.5f}  {a[4]:10.4g} {b[4]:10.4g} {c[4]:10.4g}  {a[6]:9.4f} {c[6]:9.4f}  {a[5]:10.2f}")

print()
print("=" * 104)
print("C) 入口附近前 8 个站位的完整近壁列（定位 k 的爆发点）")
print("=" * 104)
for v in xs[:8]:
    col = sorted(cols[v], key=lambda r: r[2])
    print(f"  x={v:.5f}  k[0..40步6]={[round(col[i][4],4) for i in range(0,42,6)]}  "
          f"u[0]={col[0][6]:.4f}  u[8]={col[8][6]:.4f}")
