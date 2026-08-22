# Closed-loop step-response metrics (tdm_02)

A closed-loop pitch-axis tracking loop is given by xdot = A_cl x + B_cl u, y = C_cl x
(x(0) = 0), with a unit step input u = 1 applied at t = 0.

A_cl =
  [ -0.8, 1.0 ]
  [ -6.2, -1.9 ]

B_cl =
  [ 0.0 ]
  [ 1.0 ]

C_cl =
  [ 1.0, 0.0 ]

Compute rise time (10%-90%), percent overshoot, and 2% settling time of y(t) using
EXACTLY this pinned simulation protocol (so results are unique):
  - exact zero-order-hold discretization: Ad = expm(A_cl*dt), Bd = A_cl \ ((Ad - I)*B_cl),
    x[k+1] = Ad*x[k] + Bd (u = 1 for all steps), dt = 0.01 s, T = 30 s;
  - y_inf = -C_cl * (A_cl \ B_cl) (DC value);
  - rise_time_s: from the first 10% to the first 90% crossing of y_inf, with linear
    interpolation between grid samples;
  - overshoot_pct = (max(y) - y_inf)/|y_inf| * 100;
  - settling_time_s: time of the LAST grid sample where |y - y_inf| > 0.02*|y_inf|.

Write result.json with keys: rise_time_s (s), overshoot_pct (%), settling_time_s (s).
Numeric tolerance 1%.

Output contract: write `result.json` to the current working directory — a MATLAB
`jsonencode` of a top-level struct with exactly the keys listed above. Numeric keys are
graded at 1% relative tolerance; string keys must match exactly.
Execution: your script is saved as `model.m` and executed with `matlab -batch model` in an
isolated working directory (MATLAB R2026a, Control System Toolbox available). Stay
self-contained (no shell, network, or filesystem escape).
Respond with a single ```matlab code block and nothing else.