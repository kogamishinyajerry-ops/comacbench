"""
Generate CalculiX 2.23 input deck for cantilever beam static deflection.

Geometry: L=100 mm, H=10 mm, T=5 mm
Mesh: 16 x 4 x 2 C3D20 hexahedra (structured)
Material: Steel (E=210000 MPa, nu=0.3, rho=7.85e-9 tonne/mm^3)
Load: Total Fy=-1000 N at tip, distributed equally among all 45 tip-face nodes
BC: Fully clamped at root (all 6 DOFs)
"""

# --- Parameters ---------------------------------------------------------------
# Geometry (mm)
L = 100.0   # length along +x
H = 10.0    # height along y
T = 5.0     # width  along z

# Mesh density (elements per direction) -- meets minimum requirements
Nx = 16
Ny = 4
Nz = 2

# Material (steel)
E   = 210000.0     # MPa
nu  = 0.3
rho = 7.85e-9      # tonne/mm^3

# Load
Fy_total = -1000.0  # N (total y-force at tip)

# --- Structured grid of nodes ------------------------------------------------
# For C3D20 we need (2*Nx+1) x (2*Ny+1) x (2*Nz+1) nodes so that adjacent
# elements share mid-side nodes.
Nx_n = 2 * Nx + 1
Ny_n = 2 * Ny + 1
Nz_n = 2 * Nz + 1

nodes    = []
node_ids = {}  # (ix, iy, iz) -> global node id
for ix in range(Nx_n):
    for iy in range(Ny_n):
        for iz in range(Nz_n):
            x = ix * L / (2 * Nx)
            y = -H / 2.0 + iy * H / (2 * Ny)
            z = -T / 2.0 + iz * T / (2 * Nz)
            nid = ix * Ny_n * Nz_n + iy * Nz_n + iz + 1
            nodes.append((nid, x, y, z))
            node_ids[(ix, iy, iz)] = nid

# --- C3D20 connectivity (relative to element-local grid indices) --------------
# Corners 1..8, then mid-side nodes 9..20 on the 12 edges.
elem_conn = [
    (0, 0, 0), (2, 0, 0), (2, 2, 0), (0, 2, 0),   # 1..4 (bottom face)
    (0, 0, 2), (2, 0, 2), (2, 2, 2), (0, 2, 2),   # 5..8 (top face)
    (1, 0, 0), (2, 1, 0), (1, 2, 0), (0, 1, 0),   # 9..12 (bottom edges)
    (1, 0, 2), (2, 1, 2), (1, 2, 2), (0, 1, 2),   # 13..16 (top edges)
    (0, 0, 1), (2, 0, 1), (2, 2, 1), (0, 2, 1),   # 17..20 (vertical edges)
]

# --- Build elements -----------------------------------------------------------
elements = []
for ix in range(Nx):
    for iy in range(Ny):
        for iz in range(Nz):
            enodes = [node_ids[(2 * ix + di, 2 * iy + dj, 2 * iz + dk)]
                      for di, dj, dk in elem_conn]
            eid = ix * Ny * Nz + iy * Nz + iz + 1
            elements.append((eid, enodes))

# --- Root and tip face node sets ---------------------------------------------
root_nodes = []
tip_nodes  = []
for iy in range(Ny_n):
    for iz in range(Nz_n):
        root_nodes.append(node_ids[(0,      iy, iz)])
        tip_nodes .append(node_ids[(2 * Nx, iy, iz)])

n_tip        = len(tip_nodes)
Fy_per_node  = Fy_total / n_tip  # equal share per tip node

# --- Write the input deck -----------------------------------------------------
def write_block(f, items, per_line=15):
    """Write a comma-separated list wrapped to <=16 entries per line."""
    s = [str(x) for x in items]
    for i in range(0, len(s), per_line):
        f.write(", ".join(s[i:i + per_line]) + "\n")

with open('model.inp', 'w') as f:
    # Heading
    f.write("*HEADING\n")
    f.write("Cantilever beam static deflection\n")
    f.write("**\n")

    # Nodes
    f.write("*NODE\n")
    for nid, x, y, z in nodes:
        f.write(f"{nid}, {x:.4f}, {y:.4f}, {z:.4f}\n")

    # Elements (C3D20) -- connectivity wrapped to <=16 entries per line
    f.write("*ELEMENT, TYPE=C3D20, ELSET=EALL\n")
    for eid, enodes in elements:
        entries = [str(eid)] + [str(n) for n in enodes]   # 21 entries
        f.write(", ".join(entries[:16]) + "\n")          # 16 entries
        f.write(", ".join(entries[16:]) + "\n")          #  5 entries

    # Material
    f.write("*MATERIAL, NAME=STEEL\n")
    f.write("*ELASTIC\n")
    f.write(f"{E:.1f}, {nu}\n")
    f.write("*DENSITY\n")
    f.write(f"{rho:.3e}\n")

    # Section
    f.write("*SOLID SECTION, ELSET=EALL, MATERIAL=STEEL\n")

    # Node sets
    f.write("*NSET, NSET=NROOT\n")
    write_block(f, root_nodes, per_line=15)
    f.write("*NSET, NSET=NTIP\n")
    write_block(f, tip_nodes,  per_line=15)

    # Step
    f.write("*STEP, NAME=LOAD\n")
    f.write("*STATIC\n")
    f.write("**\n")

    # Boundary conditions: fully clamped at the root (all 6 DOFs)
    f.write("*BOUNDARY\n")
    f.write("NROOT, 1, 6, 0.0\n")

    # Concentrated nodal loads at the tip (sums exactly to Fy_total)
    f.write("*CLOAD\n")
    f.write(f"NTIP, 2, {Fy_per_node:.10f}\n")

    # Output requests
    f.write("*NODE PRINT, NSET=NTIP\n")
    f.write("U\n")
    f.write("*NODE PRINT, NSET=NROOT\n")
    f.write("RF\n")
    f.write("**\n")

    f.write("*END STEP\n")