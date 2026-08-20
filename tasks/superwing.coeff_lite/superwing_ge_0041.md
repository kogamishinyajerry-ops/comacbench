You are given the parametric geometry of a transonic kinked wing and a single operating condition, and must predict its aerodynamic coefficients.

## Wing geometry parameters
- SA: 33.5487
- DA: 7.14969
- DA_kink: 5.37835
- AR: 8.62099
- TR: 0.266228
- kink: 0.395312
- rootadj: 0.790999
- rtcs_0: 0.657999
- rtcs_1: 0.965159
- rtcs_2: 0.987174
- cambers_0: 0.454
- cambers_1: 0.798586
- cambers_2: 0.148214
- twists_0: -2.63857
- twists_1: -2.87473
- twists_2: -2.12517
- twists_3: -2.67101
- Uroot_0: 0.162575
- Uroot_1: 0.0960106
- Uroot_2: 0.172425
- Uroot_3: 0.101035
- Uroot_4: 0.180585
- Uroot_5: 0.148063
- Uroot_6: 0.15714
- Uroot_7: 0.20508
- Uroot_8: 0.183441
- Uroot_9: 0.25447
- Utip_0: -0.125251
- Utip_1: -0.036475
- Utip_2: -0.215177
- Utip_3: 0.0482002
- Utip_4: -0.309675
- Utip_5: 0.0175829
- Utip_6: -0.187402
- Utip_7: -0.084715
- Utip_8: 0.0717824
- Utip_9: 0.220271
- tcroot: 0.14921

## Operating condition
- angle of attack (aoa, deg): 3.6184
- Mach number: 0.867207

The wing was simulated with a RANS solver (ADflow). Estimate the integrated aerodynamic coefficients.

Respond with a single JSON object of the form {"cl": <lift coefficient>, "cd": <drag coefficient>, "cm": <pitching moment coefficient>} and nothing else. Values must be finite numbers within physical ranges (cl in [-0.5, 1.2], cd in [0, 0.2], cm in [-0.5, 1.5]).
