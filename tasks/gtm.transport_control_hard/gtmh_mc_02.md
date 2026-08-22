# Monte Carlo robustness screening — closed-loop short-period spec (mc_02)

An elevator state-feedback loop is designed on the NOMINAL longitudinal model
x = [u, w, q, theta] (ft/s, ft/s, rad/s, rad), xdot = A x + B delta_e, u = -K x:

  nominal A = [ [Xu, Xw, 0, -g], [Zu, Zw, V, 0], [0, Mw, Mq, 0], [0, 0, 1, 0] ]
  with V = 740.0, Xu = -0.006, Xw = 0.033, Zu = -0.027, Zw = -0.66,
  Mw = -0.0046, Mq = -0.78, g = 32.174;
  B = [0; -5.5; -4.5; 0].

The gain K is any gain placing the nominal closed-loop short-period pole at
omega_n = 2.1 rad/s, zeta = 0.55 (phugoid held at open-loop).

The three pitch derivatives Mw, Zw, Mq are uncertain by ±20% each (uniform box).
Run a Monte Carlo over exactly N = 200 DETERMINISTIC samples:
  draw the three multipliers f_Mw, f_Zw, f_Mq independently uniform in [1-pct, 1+pct]
  using MATLAB rng(seed) with these INDEPENDENT seeds:
    f_Mw:  rng(20260828);      f_Zw:  rng(20261828);      f_Mq:  rng(20262828);
  generating f = 1 + pct*(2*rand(N,1) - 1) for each derivative, then loop over the N
  samples evaluating the closed-loop short-period (eig(A_i - B*K)) at each sample.

Count how many of the 200 samples satisfy BOTH:
  short-period omega_n in [2.0, 2.2] rad/s AND
  short-period zeta >= 0.52.

Write result.json with keys: pass_fraction (count/N, a number in [0,1]) and
failing_case_count (N - count, an integer). pass_fraction tolerance 2%; failing_case_count
tolerance 5%. You MUST actually run the loop and count — the seeded sampling makes the
result reproducible.

Output contract: write `result.json` to the current working directory — a MATLAB
`jsonencode` of a top-level struct with exactly the keys listed above. Numeric keys are
graded at 1% relative tolerance; string keys must match exactly.
Execution: your script is saved as `model.m` and executed with `matlab -batch model` in an
isolated working directory (MATLAB R2026a, Control System Toolbox available). Stay
self-contained (no shell, network, or filesystem escape).
Respond with a single ```matlab code block and nothing else.