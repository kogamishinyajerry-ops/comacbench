# Short-period pole placement by elevator state feedback (kdesign_02)

A transport aircraft longitudinal model x = [u, w, q, theta] (ft/s, ft/s, rad/s, rad)
has xdot = A x + B delta_e with elevator input and

A =
  [ -0.0062, 0.048, 0.0, -32.174 ]
  [ -0.044, -0.82, 640.0, 0.0 ]
  [ 0.0, -0.0068, -1.08, 0.0 ]
  [ 0.0, 0.0, 1.0, 0.0 ]

B =
  [ 0.0 ]
  [ -5.0 ]
  [ -5.5 ]
  [ 0.0 ]

Design a full-state feedback u = -K x placing the CLOSED-LOOP short-period poles at
natural frequency wn = 2.3 rad/s with damping zeta = 0.55, while keeping
the phugoid poles at their open-loop values.

Any gain K that achieves the target closed-loop poles scores — grading uses the
closed-loop eigenvalues, not K. Compute the achieved closed-loop short-period pair
from eig(A - B*K).

Write result.json with keys: cl_omega_sp (achieved closed-loop short-period natural
frequency, rad/s), cl_zeta_sp (achieved damping). Numeric tolerance 1%.

Output contract: write `result.json` to the current working directory — a MATLAB
`jsonencode` of a top-level struct with exactly the keys listed above. Numeric keys are
graded at 1% relative tolerance; string keys must match exactly.
Execution: your script is saved as `model.m` and executed with `matlab -batch model` in an
isolated working directory (MATLAB R2026a, Control System Toolbox available). Stay
self-contained (no shell, network, or filesystem escape).
Respond with a single ```matlab code block and nothing else.