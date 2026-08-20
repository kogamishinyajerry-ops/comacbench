You are given the parametric geometry of a transonic kinked wing and a single operating condition, and must predict its aerodynamic coefficients.

## Wing geometry parameters
- SA: 26.2819
- DA: 5.69218
- DA_kink: 1.08488
- AR: 9.76721
- TR: 0.273149
- kink: 0.416537
- rootadj: 0.454313
- rtcs_0: 0.665845
- rtcs_1: 0.947695
- rtcs_2: 0.96794
- cambers_0: 0.421711
- cambers_1: 0.995476
- cambers_2: 0.379104
- twists_0: -3.35377
- twists_1: -2.6894
- twists_2: -2.1662
- twists_3: -2.6549
- Uroot_0: 0.177093
- Uroot_1: 0.0817851
- Uroot_2: 0.325358
- Uroot_3: -0.0800375
- Uroot_4: 0.46476
- Uroot_5: -0.0700562
- Uroot_6: 0.392228
- Uroot_7: 0.136678
- Uroot_8: 0.270245
- Uroot_9: 0.251686
- Utip_0: -0.150139
- Utip_1: -0.0447922
- Utip_2: -0.257944
- Utip_3: 0.0602844
- Utip_4: -0.372674
- Utip_5: 0.0212672
- Utip_6: -0.225314
- Utip_7: -0.103377
- Utip_8: 0.0859285
- Utip_9: 0.269842
- tcroot: 0.15409

## Operating condition
- angle of attack (aoa, deg): 7.88329
- Mach number: 0.88938

The wing was simulated with a RANS solver (ADflow). Estimate the integrated aerodynamic coefficients.

Respond with a single JSON object of the form {"cl": <lift coefficient>, "cd": <drag coefficient>, "cm": <pitching moment coefficient>} and nothing else. Values must be finite numbers within physical ranges (cl in [-0.5, 1.2], cd in [0, 0.2], cm in [-0.5, 1.5]).
