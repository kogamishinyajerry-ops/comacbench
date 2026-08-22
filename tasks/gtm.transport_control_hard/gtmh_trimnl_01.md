# Nonlinear climb + coordinated-turn trim — 3 coupled equations (trimnl_01)

A transport aircraft must be trimmed in a steady climbing coordinated turn. The trim is
THREE coupled simultaneous nonlinear equations (no closed form; thrust, drag, lift, and
the thrust-axis offset all interlock):

  Given:
    weight W = 230000.0 lbf; wing area S = 2400.0 ft^2; altitude h = 31000.0 ft;
    true airspeed V = 730.0 ft/s; climb angle gamma = 3.0 deg; bank angle
    phi = 30.0 deg;
    lift CL(alpha, delta_e) = CL0 + CLa*alpha + CLde*delta_e, with CL0 = 0.15,
    CLa = 5.2 /rad, CLde = 0.35 /rad;
    parabolic drag CD = CD0 + k*CL^2 with CD0 = 0.021, k = 0.043;
    exponential atmosphere rho(h) = rho0*exp(-h/23800), rho0 = 0.0023769 slug/ft^3,
    q = 0.5*rho*V^2;
    thrust installation: thrust line pitched i_T = 2.5 deg vs body axis at a
    perpendicular arm z_T = 2.0 ft from the CG;
    pitch coefficients about CG: Cm0 = 0.02, Cmalpha = -0.3 /rad,
    Cmdelta_e = -0.85 /rad, mean chord cbar = 17.0 ft.

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