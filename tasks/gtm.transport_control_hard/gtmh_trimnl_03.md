# Nonlinear climb + coordinated-turn trim — 3 coupled equations (trimnl_03)

A transport aircraft must be trimmed in a steady climbing coordinated turn. The trim is
THREE coupled simultaneous nonlinear equations (no closed form; thrust, drag, lift, and
the thrust-axis offset all interlock):

  Given:
    weight W = 200000.0 lbf; wing area S = 2100.0 ft^2; altitude h = 27000.0 ft;
    true airspeed V = 700.0 ft/s; climb angle gamma = 4.0 deg; bank angle
    phi = 25.0 deg;
    lift CL(alpha, delta_e) = CL0 + CLa*alpha + CLde*delta_e, with CL0 = 0.12,
    CLa = 4.9 /rad, CLde = 0.4 /rad;
    parabolic drag CD = CD0 + k*CL^2 with CD0 = 0.023, k = 0.041;
    exponential atmosphere rho(h) = rho0*exp(-h/23800), rho0 = 0.0023769 slug/ft^3,
    q = 0.5*rho*V^2;
    thrust installation: thrust line pitched i_T = 2.0 deg vs body axis at a
    perpendicular arm z_T = 1.8 ft from the CG;
    pitch coefficients about CG: Cm0 = 0.018, Cmalpha = -0.28 /rad,
    Cmdelta_e = -0.8 /rad, mean chord cbar = 16.0 ft.

  The three equilibrium equations IN THE THREE UNKNOWNS (alpha, thrust T, elevator delta_e):
    1. vertical:  q*S*CL(alpha,delta_e)*cos(phi) + T*sin(alpha + i_T) - W*cos(gamma) = 0
    2. along flight path:  T*cos(alpha + i_T) - q*S*CD - W*sin(gamma) = 0
    3. pitching about CG:  q*S*cbar*(Cm0 + Cmalpha*alpha + Cmdelta_e*delta_e)
                             + T*sin(i_T)*z_T = 0
  (Note alpha and delta_e both enter the lift, T enters the moment through the thrust
  offset, and alpha enters both the drag and the thrust projection — you must solve all
  three simultaneously; fzero on a single variable will not suffice.)

  The load factor is n = cos(gamma) / cos(phi).

Solve by a Newton iteration or by a coupled fzero scheme. The unique physical solution
has alpha in [0.5, 10] deg and T in [5000, 60000] lbf.

Write result.json with keys: alpha_trim_deg (deg), thrust_lbf (lbf),
delta_e_trim_deg (deg), load_factor. Numeric tolerance 1%.

Output contract: write `result.json` to the current working directory — a MATLAB
`jsonencode` of a top-level struct with exactly the keys listed above. Numeric keys are
graded at 1% relative tolerance; string keys must match exactly.
Execution: your script is saved as `model.m` and executed with `matlab -batch model` in an
isolated working directory (MATLAB R2026a, Control System Toolbox available). Stay
self-contained (no shell, network, or filesystem escape).
Respond with a single ```matlab code block and nothing else.