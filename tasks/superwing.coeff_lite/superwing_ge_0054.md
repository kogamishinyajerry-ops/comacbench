You are given the parametric geometry of a transonic kinked wing and a single operating condition, and must predict its aerodynamic coefficients.

## Wing geometry parameters
- SA: 32.0758
- DA: 4.77771
- DA_kink: 2.69006
- AR: 8.54316
- TR: 0.251322
- kink: 0.371974
- rootadj: 0.969247
- rtcs_0: 0.627871
- rtcs_1: 0.938233
- rtcs_2: 0.999195
- cambers_0: 0.757152
- cambers_1: 0.525034
- cambers_2: 0.482276
- twists_0: -3.97874
- twists_1: -2.80677
- twists_2: -1.98263
- twists_3: -1.24077
- Uroot_0: 0.144969
- Uroot_1: 0.11265
- Uroot_2: 0.237285
- Uroot_3: 0.0483607
- Uroot_4: 0.236291
- Uroot_5: 0.290784
- Uroot_6: 0.0927142
- Uroot_7: 0.164767
- Uroot_8: 0.233057
- Uroot_9: 0.163067
- Utip_0: -0.149739
- Utip_1: -0.0487842
- Utip_2: -0.246247
- Utip_3: 0.0223451
- Utip_4: -0.288234
- Utip_5: -0.0990243
- Utip_6: -0.0965247
- Utip_7: -0.199903
- Utip_8: 0.2
- Utip_9: 0.19568
- tcroot: 0.140463

## Operating condition
- angle of attack (aoa, deg): 7.96639
- Mach number: 0.78576

The wing was simulated with a RANS solver (ADflow). Estimate the integrated aerodynamic coefficients.

Respond with a single JSON object of the form {"cl": <lift coefficient>, "cd": <drag coefficient>, "cm": <pitching moment coefficient>} and nothing else. Values must be finite numbers within physical ranges (cl in [-0.5, 1.2], cd in [0, 0.2], cm in [-0.5, 1.5]).
