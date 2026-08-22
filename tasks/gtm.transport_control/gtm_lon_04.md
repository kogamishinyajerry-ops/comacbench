# Longitudinal modal analysis — cruise linear model (lon_04)

A transport aircraft (NASA CR-2144 DC-8 class) is linearized about a steady cruise
condition. The longitudinal state is x = [u, w, q, theta] (ft/s, ft/s, rad/s, rad),
body axes, with xdot = A x and

A =
  [ -0.0075, 0.055, 0.0, -32.174 ]
  [ -0.048, -0.78, 660.0, 0.0 ]
  [ 0.0, -0.0072, -1.05, 0.0 ]
  [ 0.0, 0.0, 1.0, 0.0 ]

The matrix has two classical complex-conjugate mode pairs. Compute the natural
frequency (rad/s) and damping ratio of each: the short-period pair and the phugoid
pair.

Write result.json with keys: omega_sp, zeta_sp (short period), omega_ph, zeta_ph
(phugoid). Numeric tolerance 1%.

Output contract: write `result.json` to the current working directory — a MATLAB
`jsonencode` of a top-level struct with exactly the keys listed above. Numeric keys are
graded at 1% relative tolerance; string keys must match exactly.
Execution: your script is saved as `model.m` and executed with `matlab -batch model` in an
isolated working directory (MATLAB R2026a, Control System Toolbox available). Stay
self-contained (no shell, network, or filesystem escape).
Respond with a single ```matlab code block and nothing else.