# Lateral-directional modal analysis (lat_03)

The lateral-directional state of a transport aircraft at cruise is
x = [beta, p, r, phi] (rad, rad/s, rad/s, rad) with xdot = A x and

A =
  [ -0.14, 0.02, -0.88, 0.055 ]
  [ -8.5, -1.45, -0.06, 0.0 ]
  [ 1.55, -0.05, -0.42, 0.0 ]
  [ 0.0, 1.0, 0.0, 0.0 ]

The matrix has one complex-conjugate pair (Dutch roll) and two real roots (roll
convergence and spiral). Compute: dutch_roll_omega (rad/s) and dutch_roll_zeta for
the Dutch roll pair; roll_mode_lambda and spiral_mode_lambda — the REAL eigenvalues
themselves (not time constants; roll convergence is the more negative root).

Write result.json with keys: dutch_roll_omega, dutch_roll_zeta, roll_mode_lambda,
spiral_mode_lambda. Numeric tolerance 1%.

Output contract: write `result.json` to the current working directory — a MATLAB
`jsonencode` of a top-level struct with exactly the keys listed above. Numeric keys are
graded at 1% relative tolerance; string keys must match exactly.
Execution: your script is saved as `model.m` and executed with `matlab -batch model` in an
isolated working directory (MATLAB R2026a, Control System Toolbox available). Stay
self-contained (no shell, network, or filesystem escape).
Respond with a single ```matlab code block and nothing else.