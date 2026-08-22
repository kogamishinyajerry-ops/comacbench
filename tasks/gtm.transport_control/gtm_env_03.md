# Envelope robustness — short-period modes across three flight conditions

The same transport airframe is linearized (env_03) about three cruise flight
conditions of its operating envelope. The longitudinal state is x = [u, w, q, theta]
(ft/s, ft/s, rad/s, rad), xdot = A x, with
FC1: altitude 30000 ft, true airspeed 720 ft/s
A1 =
  [ -0.0056, 0.044, 0.0, -32.174 ]
  [ -0.038, -0.76, 720.0, 0.0 ]
  [ 0.0, -0.0058, -0.98, 0.0 ]
  [ 0.0, 0.0, 1.0, 0.0 ]
FC2: altitude 34000 ft, true airspeed 665 ft/s
A2 =
  [ -0.0058, 0.034, 0.0, -32.174 ]
  [ -0.028, -0.66, 665.0, 0.0 ]
  [ 0.0, -0.0046, -0.84, 0.0 ]
  [ 0.0, 0.0, 1.0, 0.0 ]
FC3: altitude 39000 ft, true airspeed 610 ft/s
A3 =
  [ -0.006, 0.024, 0.0, -32.174 ]
  [ -0.02, -0.56, 610.0, 0.0 ]
  [ 0.0, -0.0036, -0.68, 0.0 ]
  [ 0.0, 0.0, 1.0, 0.0 ]
Compute the short-period natural frequency (rad/s) and damping ratio at each flight
condition.

Write result.json with keys: omega_sp_1, zeta_sp_1, omega_sp_2, zeta_sp_2,
omega_sp_3, zeta_sp_3. Numeric tolerance 1%.

Output contract: write `result.json` to the current working directory — a MATLAB
`jsonencode` of a top-level struct with exactly the keys listed above. Numeric keys are
graded at 1% relative tolerance; string keys must match exactly.
Execution: your script is saved as `model.m` and executed with `matlab -batch model` in an
isolated working directory (MATLAB R2026a, Control System Toolbox available). Stay
self-contained (no shell, network, or filesystem escape).
Respond with a single ```matlab code block and nothing else.