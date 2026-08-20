You are given the parametric geometry of a transonic kinked wing and a single operating condition, and must predict its aerodynamic coefficients.

## Wing geometry parameters
- SA: 31.4545
- DA: 4.40565
- DA_kink: 0.816284
- AR: 8.19938
- TR: 0.383455
- kink: 0.371419
- rootadj: 0.805511
- rtcs_0: 0.697205
- rtcs_1: 0.925537
- rtcs_2: 0.962763
- cambers_0: 0.652122
- cambers_1: 0.756299
- cambers_2: 0.758791
- twists_0: -3.77913
- twists_1: -2.5054
- twists_2: -1.00459
- twists_3: -1.113
- Uroot_0: 0.133133
- Uroot_1: 0.0815625
- Uroot_2: 0.201828
- Uroot_3: -0.0154085
- Uroot_4: 0.394389
- Uroot_5: -0.177432
- Uroot_6: 0.564381
- Uroot_7: -0.0337698
- Uroot_8: 0.307782
- Uroot_9: 0.243499
- Utip_0: -0.125116
- Utip_1: -0.0373268
- Utip_2: -0.214954
- Utip_3: 0.050237
- Utip_4: -0.310562
- Utip_5: 0.0176807
- Utip_6: -0.187762
- Utip_7: -0.0861474
- Utip_8: 0.071607
- Utip_9: 0.224868
- tcroot: 0.150087

## Operating condition
- angle of attack (aoa, deg): 5.26338
- Mach number: 0.867639

The wing was simulated with a RANS solver (ADflow). Estimate the integrated aerodynamic coefficients.

Respond with a single JSON object of the form {"cl": <lift coefficient>, "cd": <drag coefficient>, "cm": <pitching moment coefficient>} and nothing else. Values must be finite numbers within physical ranges (cl in [-0.5, 1.2], cd in [0, 0.2], cm in [-0.5, 1.5]).
