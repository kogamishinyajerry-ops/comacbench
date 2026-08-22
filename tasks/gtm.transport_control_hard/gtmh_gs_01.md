# Gain scheduling — independent pole placement at three flight conditions (gs_01)

The SAME transport airframe is linearized at three flight conditions across its
envelope. At each condition the longitudinal state is x = [u, w, q, theta]
(ft/s, ft/s, rad/s, rad), xdot = A_i x + B_i delta_e. Design a SEPARATE full-state
feedback Ki at each condition (u = -Ki x) placing the short-period pole at the
condition's OWN target (natural frequency and damping), keeping the phugoid at its
open-loop values. The three conditions and targets are:

FC1 (true airspeed 740 ft/s), target omega_n = 2.0 rad/s, zeta = 0.6:
A1 =
  [ -0.0064, 0.038, 0.0, -32.174 ]
  [ -0.031, -0.71, 740.0, 0.0 ]
  [ 0.0, -0.0051, -0.9, 0.0 ]
  [ 0.0, 0.0, 1.0, 0.0 ]
B1 =
  [ 0.0 ]
  [ -6.0 ]
  [ -4.0 ]
  [ 0.0 ]

FC2 (true airspeed 700 ft/s), target omega_n = 1.9 rad/s, zeta = 0.55:
A2 =
  [ -0.0059, 0.026, 0.0, -32.174 ]
  [ -0.019, -0.55, 700.0, 0.0 ]
  [ 0.0, -0.0034, -0.64, 0.0 ]
  [ 0.0, 0.0, 1.0, 0.0 ]
B2 =
  [ 0.0 ]
  [ -6.0 ]
  [ -4.0 ]
  [ 0.0 ]

FC3 (true airspeed 660 ft/s), target omega_n = 1.7 rad/s, zeta = 0.5:
A3 =
  [ -0.0057, 0.02, 0.0, -32.174 ]
  [ -0.015, -0.5, 660.0, 0.0 ]
  [ 0.0, -0.003, -0.58, 0.0 ]
  [ 0.0, 0.0, 1.0, 0.0 ]
B3 =
  [ 0.0 ]
  [ -6.0 ]
  [ -4.0 ]
  [ 0.0 ]

Any gain Ki achieving the target closed-loop poles scores — grading uses the achieved
closed-loop eigenvalues, not K. Compute the achieved closed-loop short-period pair at
each condition from eig(A_i - B_i*K_i).

Write result.json with keys: cl_omega_sp_1, cl_zeta_sp_1, cl_omega_sp_2, cl_zeta_sp_2,
cl_omega_sp_3, cl_zeta_sp_3. Numeric tolerance 1%.

Output contract: write `result.json` to the current working directory — a MATLAB
`jsonencode` of a top-level struct with exactly the keys listed above. Numeric keys are
graded at 1% relative tolerance; string keys must match exactly.
Execution: your script is saved as `model.m` and executed with `matlab -batch model` in an
isolated working directory (MATLAB R2026a, Control System Toolbox available). Stay
self-contained (no shell, network, or filesystem escape).
Respond with a single ```matlab code block and nothing else.