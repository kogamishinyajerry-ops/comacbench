# Corrupted stability derivative repair (repair_02)

A longitudinal linear model x = [u, w, q, theta] (ft/s, ft/s, rad/s, rad),
xdot = A x, was assembled for a transport at cruise, but exactly ONE of the stability
derivatives Mw or Mq was corrupted (its value was scaled by a constant factor). The
matrix as assembled is

A_corrupt =
  [ -0.0064, 0.038, 0.0, -32.174 ]
  [ -0.033, -0.7, 680.0, 0.0 ]
  [ 0.0, -0.005, -0.34, 0.0 ]
  [ 0.0, 0.0, 1.0, 0.0 ]

(The physical row structure is udot = Xu*u + Xw*w - g*theta, wdot = Zu*u + Zw*w + V*q,
qdot = Mw*w + Mq*q, theta_dot = q, g = 32.174 ft/s^2 — so Mw is the (3,2) entry and
Mq the (3,3) entry.)

An independent modal-identification test of the TRUE (uncorrupted) aircraft gave:
  short period: omega_sp = 1.99883 rad/s, zeta_sp = 0.38779;
  phugoid:      omega_ph = 0.0364518 rad/s, zeta_ph = 0.0843678.

Determine which parameter (Mw or Mq) was corrupted and its correct value (the value
that restores the reference modal data).

Write result.json with keys: corrupted_param (exact string 'Mw' or 'Mq'),
restored_value (the correct value of that parameter). corrupted_param is graded by
exact string match; restored_value at 1% relative tolerance.

Output contract: write `result.json` to the current working directory — a MATLAB
`jsonencode` of a top-level struct with exactly the keys listed above. Numeric keys are
graded at 1% relative tolerance; string keys must match exactly.
Execution: your script is saved as `model.m` and executed with `matlab -batch model` in an
isolated working directory (MATLAB R2026a, Control System Toolbox available). Stay
self-contained (no shell, network, or filesystem escape).
Respond with a single ```matlab code block and nothing else.