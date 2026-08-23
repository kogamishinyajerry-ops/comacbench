"""make_case.py — write a valid CalculiX input deck `model.inp` in the cwd.

Units: mm, N, MPa, tonne/mm^3 (steel E=210000 MPa, nu=0.3, rho=7.85e-9).
20-node hex C3D20 elements on a structured mesh; connectivity and nset lines
are wrapped to at most 16 entries per line (CalculiX line limit).
"""
LH, LV, T, W = 60, 60, 10, 20
NXT, NXL, NYT, NYV, NZ = 2, 8, 2, 8, 2


def seg(x0, x1, n):
    return [x0 + (x1 - x0) * i / (2 * n) for i in range(2 * n + 1)]


xs = seg(0.0, T, NXT)[:-1] + seg(T, LH, NXL)
ys = seg(0.0, T, NYT)[:-1] + seg(T, LV, NYV)
zs = seg(0.0, W, NZ)
nx, ny, nz = (len(xs) - 1) // 2, (len(ys) - 1) // 2, (len(zs) - 1) // 2

nid = {}
nodes = []


def get_node(i, j, k):
    if (i, j, k) not in nid:
        nid[(i, j, k)] = len(nodes) + 1
        nodes.append((len(nodes) + 1, xs[i], ys[j], zs[k]))
    return nid[(i, j, k)]


def elem(i, j, k):
    c = [(2 * i, 2 * j, 2 * k), (2 * i + 2, 2 * j, 2 * k),
         (2 * i + 2, 2 * j + 2, 2 * k), (2 * i, 2 * j + 2, 2 * k),
         (2 * i, 2 * j, 2 * k + 2), (2 * i + 2, 2 * j, 2 * k + 2),
         (2 * i + 2, 2 * j + 2, 2 * k + 2), (2 * i, 2 * j + 2, 2 * k + 2),
         (2 * i + 1, 2 * j, 2 * k), (2 * i + 2, 2 * j + 1, 2 * k),
         (2 * i + 1, 2 * j + 2, 2 * k), (2 * i, 2 * j + 1, 2 * k),
         (2 * i + 1, 2 * j, 2 * k + 2), (2 * i + 2, 2 * j + 1, 2 * k + 2),
         (2 * i + 1, 2 * j + 2, 2 * k + 2), (2 * i, 2 * j + 1, 2 * k + 2),
         (2 * i, 2 * j, 2 * k + 1), (2 * i + 2, 2 * j, 2 * k + 1),
         (2 * i + 2, 2 * j + 2, 2 * k + 1), (2 * i, 2 * j + 2, 2 * k + 1)]
    return [get_node(*q) for q in c]


def in_L(i, j):
    return xs[2 * i + 2] <= T + 1e-9 or ys[2 * j + 2] <= T + 1e-9


els = []
for k in range(nz):
    for j in range(ny):
        for i in range(nx):
            if not in_L(i, j):
                continue
            els.append((len(els) + 1, elem(i, j, k)))

NROOT = [n[0] for n in nodes if abs(n[1]) < 1e-9]
NLOAD = [n[0] for n in nodes if abs(n[1] - LH) < 1e-9]
sets = {"NROOT": NROOT, "NLOAD": NLOAD}

with open("model.inp", "w") as f:
    f.write("*NODE\n")
    for n_, x, y, z in nodes:
        f.write(f"{n_}, {x:.6f}, {y:.6f}, {z:.6f}\n")
    f.write("*ELEMENT, TYPE=C3D20, ELSET=EALL\n")
    for en, conn in els:
        ids = [en] + conn
        for s in range(0, len(ids), 16):
            f.write(", ".join(str(c) for c in ids[s:s + 16]) + "\n")
    for name, idlist in sets.items():
        f.write(f"*NSET, NSET={name}\n")
        for s in range(0, len(idlist), 16):
            f.write(", ".join(str(c) for c in idlist[s:s + 16]) + "\n")
    f.write("*MATERIAL, NAME=STEEL\n*ELASTIC\n210000.0, 0.3\n*DENSITY\n7.85e-9\n")
    f.write("*SOLID SECTION, ELSET=EALL, MATERIAL=STEEL\n")
    f.write("*BOUNDARY\nNROOT, 1, 3, 0.0\n")
    f.write("*STEP\n*STATIC\n")
    for nd in NLOAD:
        f.write(f"*CLOAD\n{nd}, 2, {-500.0 / len(NLOAD):.9f}\n")
    f.write("*NODE PRINT, NSET=NLOAD\nU\n*NODE PRINT, NSET=NROOT\nRF\n*END STEP\n")
