# Static margin and neutral point (sm_02)

A transport aircraft configuration is defined by:
  lift-curve slope CLalpha = 4.8 /rad; pitching-moment slope Cmalpha = -1.1 /rad;
  wing loading W/S = 110.0 lbf/ft^2; mean aerodynamic chord c = 19.5 ft;
  center-of-gravity position h_cg = 0.3 (fraction of mean aerodynamic chord).

Using the classical linear relation for static longitudinal stability,
static margin = -Cmalpha / CLalpha, and neutral point h_n = h_cg + static_margin:

Write result.json with keys: static_margin (dimensionless), h_n (neutral point,
fraction of MAC). Numeric tolerance 1%.

Output contract: write `result.json` to the current working directory — a MATLAB
`jsonencode` of a top-level struct with exactly the keys listed above. Numeric keys are
graded at 1% relative tolerance; string keys must match exactly.
Execution: your script is saved as `model.m` and executed with `matlab -batch model` in an
isolated working directory (MATLAB R2026a, Control System Toolbox available). Stay
self-contained (no shell, network, or filesystem escape).
Respond with a single ```matlab code block and nothing else.