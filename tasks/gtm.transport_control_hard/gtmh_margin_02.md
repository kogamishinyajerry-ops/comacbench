# Robust stability margins of a designed loop (margin_02)

A flight-control loop transfer function L(s) is already designed (plant times
compensator). Its open-loop transfer function is, in descending-power polynomial form:

  numerator   num = [9.0]
  denominator den = [1.0, 5.0, 6.0, 0.0]

so L(s) = num(s) / den(s) (den includes the integrator; this is a type-1 loop).
Compute the classical gain and phase stability margins of this loop.
Write result.json with keys: gm_db (gain margin, dB), pm_deg (phase margin, degrees),
w_gc (gain crossover frequency, rad/s), w_pc (phase crossover frequency, rad/s).
Numeric tolerance 1%. (Use Control System Toolbox margin(); note gm_db must be
20*log10 of the linear gain margin.)

Output contract: write `result.json` to the current working directory — a MATLAB
`jsonencode` of a top-level struct with exactly the keys listed above. Numeric keys are
graded at 1% relative tolerance; string keys must match exactly.
Execution: your script is saved as `model.m` and executed with `matlab -batch model` in an
isolated working directory (MATLAB R2026a, Control System Toolbox available). Stay
self-contained (no shell, network, or filesystem escape).
Respond with a single ```matlab code block and nothing else.