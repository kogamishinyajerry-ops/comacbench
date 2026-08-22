# Steady level-flight trim — transport aircraft (trim_02)

Given (transport cruise class):
  weight W = 280000.0 lbf; wing area S = 2730.0 ft^2; altitude h = 35000.0 ft;
  true airspeed V = 780.0 ft/s;
  lift curve CL = CL0 + CLalpha * alpha with CL0 = 0.18, CLalpha = 5.6 /rad
  (alpha in rad); parabolic drag polar CD = CD0 + k * CL^2 with CD0 = 0.019,
  k = 0.045;
  simple exponential atmosphere: rho(h) = rho0 * exp(-h/23800), rho0 = 0.0023769
  slug/ft^3, so dynamic pressure qbar = 0.5 * rho * V^2;
  engine model: thrust available T(V) = T0 * (V/V0)^0.8 * delta_t with T0 = 68000.0 lbf
  at V0 = 780.0 ft/s and throttle delta_t adjustable in [0, 1].

Solve the steady level-flight trim (lift equals weight, drag equals thrust) for the
two unknowns: angle of attack and required thrust.

Write result.json with keys: alpha_trim_deg (trim angle of attack, degrees),
thrust_lbf (required thrust, lbf). Numeric tolerance 1%.

Output contract: write `result.json` to the current working directory — a MATLAB
`jsonencode` of a top-level struct with exactly the keys listed above. Numeric keys are
graded at 1% relative tolerance; string keys must match exactly.
Execution: your script is saved as `model.m` and executed with `matlab -batch model` in an
isolated working directory (MATLAB R2026a, Control System Toolbox available). Stay
self-contained (no shell, network, or filesystem escape).
Respond with a single ```matlab code block and nothing else.