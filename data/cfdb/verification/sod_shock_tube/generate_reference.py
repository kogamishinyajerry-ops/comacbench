#!/usr/bin/env python3
"""Generate the exact Riemann-solution reference for the Sod (1978) shock tube.

Pure Python (stdlib only). Solves the classic Sod problem

    (rho, u, p)_L = (1, 0, 1)      x <  0.5
    (rho, u, p)_R = (0.125, 0, 0.1)  x >= 0.5     gamma = 1.4

at t = 0.2 by Newton-iterating the star pressure p* (Toro, "Riemann Solvers
and Numerical Methods for Fluid Dynamics", ch. 4) and sampling the exact
wave structure pointwise. NO hand-typed profile numbers: every CSV row is
evaluated from the closed-form solution.

Outputs (relative to this script's directory):
  reference/sod1978_exact_t0.2.csv   x,rho,u,p sampled at the 1000 cell
                                     centres of the case mesh (dx = 1e-3)
  held_out/qoi.json                  shock_x_t02, rho_plateau_t02 (exact)

Also prints the QoI values that are inlined into case.yaml (qoi_values) so
they are script-computed, never hand-typed.

Self-checks: p*, u* and the star densities are asserted against the
universally tabulated Sod values (p* = 0.30313, u* = 0.92745,
rho*_L = 0.42632, rho*_R = 0.26557; e.g. Toro 2009 §4.3.3, and the values
reproduced in Sod 1978 Fig. 2 / countless textbooks) to guard against
regressions in this script.

Reference: Sod, G. A., "A Survey of Several Finite Difference Methods for
Systems of Nonlinear Hyperbolic Conservation Laws", J. Comput. Phys. 27,
pp. 1-31, 1978.
"""

import json
import math
from pathlib import Path

GAMMA = 1.4
RHO_L, U_L, P_L = 1.0, 0.0, 1.0
RHO_R, U_R, P_R = 0.125, 0.0, 0.1
X0 = 0.5          # diaphragm position
T_END = 0.2       # evaluation time
N_CELLS = 1000    # matches constant/polyMesh/blockMeshDict


def wave_f(p_star, rho, u, p, a):
    """Pressure function f and its derivative (Toro eq. 4.5/4.9).

    Shock branch for p_star > p, rarefaction branch otherwise.
    """
    if p_star > p:  # shock
        A = 2.0 / ((GAMMA + 1.0) * rho)
        B = (GAMMA - 1.0) / (GAMMA + 1.0) * p
        f = (p_star - p) * math.sqrt(A / (p_star + B))
        df = math.sqrt(A / (p_star + B)) * (
            1.0 - 0.5 * (p_star - p) / (p_star + B)
        )
    else:  # rarefaction
        pr = p_star / p
        f = 2.0 * a / (GAMMA - 1.0) * (pr ** ((GAMMA - 1.0) / (2.0 * GAMMA)) - 1.0)
        df = (1.0 / (rho * a)) * pr ** (-(GAMMA + 1.0) / (2.0 * GAMMA))
    return f, df


def solve_star():
    a_l = math.sqrt(GAMMA * P_L / RHO_L)
    a_r = math.sqrt(GAMMA * P_R / RHO_R)
    # Two-rarefaction guess (Toro eq. 4.47) as Newton start value.
    p_pv = 0.5 * (P_L + P_R)
    p_star = max(1e-12, p_pv)
    for _ in range(50):
        f_l, df_l = wave_f(p_star, RHO_L, U_L, P_L, a_l)
        f_r, df_r = wave_f(p_star, RHO_R, U_R, P_R, a_r)
        dp = (f_l + f_r + U_R - U_L) / (df_l + df_r)
        p_star -= dp
        if abs(dp) / p_star < 1e-12:
            break
    else:
        raise RuntimeError("Newton iteration for p* did not converge")
    f_l, _ = wave_f(p_star, RHO_L, U_L, P_L, a_l)
    f_r, _ = wave_f(p_star, RHO_R, U_R, P_R, a_r)
    u_star = 0.5 * (U_L + U_R) + 0.5 * (f_r - f_l)
    return p_star, u_star


def sample(x, t, p_star, u_star):
    """Exact solution at position x and time t (x relative to diaphragm X0)."""
    xi = (x - X0) / t
    a_l = math.sqrt(GAMMA * P_L / RHO_L)
    a_r = math.sqrt(GAMMA * P_R / RHO_R)

    # Left wave is a rarefaction (p* < P_L), right wave a shock (p* > P_R).
    a_star_l = a_l * (p_star / P_L) ** ((GAMMA - 1.0) / (2.0 * GAMMA))
    rho_star_l = RHO_L * (p_star / P_L) ** (1.0 / GAMMA)
    alpha = (GAMMA - 1.0) / (GAMMA + 1.0)
    rho_star_r = RHO_R * (p_star / P_R + alpha) / (alpha * p_star / P_R + 1.0)

    s_head = U_L - a_l                 # rarefaction head speed
    s_tail = u_star - a_star_l         # rarefaction tail speed
    s_shock = U_R + a_r * math.sqrt(
        (GAMMA + 1.0) / (2.0 * GAMMA) * p_star / P_R
        + (GAMMA - 1.0) / (2.0 * GAMMA)
    )

    if xi <= s_head:
        return RHO_L, U_L, P_L
    if xi <= s_tail:
        # Inside the left rarefaction fan (Toro eq. 4.56).
        u = 2.0 / (GAMMA + 1.0) * (a_l + 0.5 * (GAMMA - 1.0) * U_L + xi)
        a = 2.0 / (GAMMA + 1.0) * (a_l + 0.5 * (GAMMA - 1.0) * (U_L - xi))
        rho = RHO_L * (a / a_l) ** (2.0 / (GAMMA - 1.0))
        p = P_L * (a / a_l) ** (2.0 * GAMMA / (GAMMA - 1.0))
        return rho, u, p
    if xi <= u_star:
        return rho_star_l, u_star, p_star
    if xi <= s_shock:
        return rho_star_r, u_star, p_star
    return RHO_R, U_R, P_R


def main():
    here = Path(__file__).resolve().parent
    p_star, u_star = solve_star()

    # --- self-checks against universally tabulated Sod values --------------
    rho_star_l = RHO_L * (p_star / P_L) ** (1.0 / GAMMA)
    alpha = (GAMMA - 1.0) / (GAMMA + 1.0)
    rho_star_r = RHO_R * (p_star / P_R + alpha) / (alpha * p_star / P_R + 1.0)
    assert abs(p_star - 0.30313) < 5e-5, p_star
    assert abs(u_star - 0.92745) < 5e-5, u_star
    assert abs(rho_star_l - 0.42632) < 5e-5, rho_star_l
    assert abs(rho_star_r - 0.26557) < 5e-5, rho_star_r

    # --- exact wave positions at t = 0.2 ------------------------------------
    a_r = math.sqrt(GAMMA * P_R / RHO_R)
    s_shock = U_R + a_r * math.sqrt(
        (GAMMA + 1.0) / (2.0 * GAMMA) * p_star / P_R
        + (GAMMA - 1.0) / (2.0 * GAMMA)
    )
    shock_x = X0 + s_shock * T_END
    # Star-region plateau probe at x = 0.6 (xi = 0.5 lies between the
    # rarefaction tail and the contact discontinuity -> exact rho*_L).
    rho_plateau = sample(0.6, T_END, p_star, u_star)[0]
    assert abs(rho_plateau - rho_star_l) < 1e-12

    # --- CSV: exact profile at the 1000 cell centres of the case mesh ------
    ref_dir = here / "reference"
    ref_dir.mkdir(exist_ok=True)
    csv_path = ref_dir / "sod1978_exact_t0.2.csv"
    with csv_path.open("w", encoding="utf-8", newline="") as f:
        f.write("x,rho,u,p\n")
        for i in range(N_CELLS):
            x = (i + 0.5) / N_CELLS
            rho, u, p = sample(x, T_END, p_star, u_star)
            f.write(f"{x:.4f},{rho:.8f},{u:.8f},{p:.8f}\n")

    # --- held-out QoI (same values inlined in case.yaml qoi_values) --------
    ho_dir = here / "held_out"
    ho_dir.mkdir(exist_ok=True)
    qoi = {"shock_x_t02": shock_x, "rho_plateau_t02": rho_plateau}
    with (ho_dir / "qoi.json").open("w", encoding="utf-8") as f:
        json.dump(qoi, f, indent=2)
        f.write("\n")

    print(f"p_star        = {p_star:.8f}")
    print(f"u_star        = {u_star:.8f}")
    print(f"rho_star_l    = {rho_star_l:.8f}")
    print(f"rho_star_r    = {rho_star_r:.8f}")
    print(f"shock speed   = {s_shock:.8f}")
    print(f"shock_x_t02   = {shock_x:.8f}")
    print(f"rho_plateau_t02 = {rho_plateau:.8f}")
    print(f"wrote {csv_path.relative_to(here)} and held_out/qoi.json")


if __name__ == "__main__":
    main()
