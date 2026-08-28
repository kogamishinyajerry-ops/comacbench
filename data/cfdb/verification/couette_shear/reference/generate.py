#!/usr/bin/env python3
"""Generate the frozen analytical reference for the couette_shear case.

Steady planar Couette flow (bottom wall stationary no-slip, top lid moving
at U_lid, gap H, kinematic viscosity nu):

    u(y) / U_lid = y / H                      (linear profile)
    |tau_wall|  = nu * U_lid / H              (kinematic, per unit density)
    bottom_wall_shear_normalized = |tau_bottom| / (nu * U_lid / H) = 1.0

Outputs (both deterministic, stdlib only, no hand-typed digits):
  reference/couette_profile.csv  — u/U_lid vs y/H at 21 stations
  held_out/qoi.json              — held-out QoI anchor

Reference: Couette (1890), Ann. Chim. Phys. ser. VI, 21, 433-510; standard
textbook result (White, "Viscous Fluid Flow"; Schlichting, "Boundary-Layer
Theory"). See provenance.yaml.
"""

from __future__ import annotations

import json
from pathlib import Path

# Physical parameters — MUST match case.yaml, 0/U and
# constant/transportProperties (single source of truth for the numbers).
U_LID = 0.1      # m/s, lid velocity (0/U, movingWall)
H = 0.01         # m, gap height (blockMeshDict)
NU = 5e-05       # m^2/s, kinematic viscosity (transportProperties)

N_STATIONS = 21  # profile stations, y/H = 0, 0.05, ..., 1.0

CASE_DIR = Path(__file__).resolve().parent.parent


def main() -> None:
    re_h = U_LID * H / NU
    tau_ref = NU * U_LID / H  # kinematic wall shear stress, m^2/s^2

    # --- velocity profile CSV -------------------------------------------
    csv_path = CASE_DIR / "reference" / "couette_profile.csv"
    lines = ["y_over_H,u_over_U_lid"]
    for i in range(N_STATIONS):
        y_over_h = i / (N_STATIONS - 1)
        u_over_u = y_over_h  # exact linear solution
        lines.append(f"{y_over_h:.4f},{u_over_u:.6f}")
    csv_path.write_text("\n".join(lines) + "\n", encoding="utf-8")

    # --- held-out QoI anchor --------------------------------------------
    qoi_path = CASE_DIR / "held_out" / "qoi.json"
    qoi_path.parent.mkdir(parents=True, exist_ok=True)
    qoi = {"bottom_wall_shear_normalized": 1.0}  # tau_bottom / tau_ref
    qoi_path.write_text(json.dumps(qoi, indent=2) + "\n", encoding="utf-8")

    print(f"Re_H = {re_h:g}")
    print(f"tau_ref = nu*U_lid/H = {tau_ref:g} m^2/s^2 (kinematic)")
    print(f"wrote {csv_path.relative_to(CASE_DIR)} ({N_STATIONS} stations)")
    print(f"wrote {qoi_path.relative_to(CASE_DIR)}")


if __name__ == "__main__":
    main()
