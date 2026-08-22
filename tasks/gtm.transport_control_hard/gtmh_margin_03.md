# Robust stability margins of a cascaded (inner + outer) loop (margin_03)

A two-loop cascade controller for a transport pitch-axis is given:

  INNER loop: plant G_in(s) = 1 / (s * (s + 4.0)) with feedback gain ki = 12.0
  (unity negative feedback, so the closed inner loop is
   G_in_cl(s) = ki * G_in(s) / (1 + ki * G_in(s))).

  OUTER loop: plant/compensator G_out(s) = 2.5 / (s * (s + 2.0)).

The cascaded total open loop is L(s) = G_out(s) * G_in_cl(s). Close the INNER loop
first, then cascade — this combination is the hard part. Compute the gain and phase
margins of the TOTAL open loop L(s).
Write result.json with keys: gm_db (gain margin, dB), pm_deg (phase margin, degrees),
w_gc (gain crossover frequency, rad/s), w_pc (phase crossover frequency, rad/s).
Numeric tolerance 1%. (Use Control System Toolbox: tf / feedback / margin;
gm_db = 20*log10 of the linear gain margin.)

Output contract: write `result.json` to the current working directory — a MATLAB
`jsonencode` of a top-level struct with exactly the keys listed above. Numeric keys are
graded at 1% relative tolerance; string keys must match exactly.
Execution: your script is saved as `model.m` and executed with `matlab -batch model` in an
isolated working directory (MATLAB R2026a, Control System Toolbox available). Stay
self-contained (no shell, network, or filesystem escape).
Respond with a single ```matlab code block and nothing else.