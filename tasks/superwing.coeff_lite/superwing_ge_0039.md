You are given the parametric geometry of a transonic kinked wing and a single operating condition, and must predict its aerodynamic coefficients.

## Wing geometry parameters
- SA: 32.858
- DA: 4.2409
- DA_kink: 5.13923
- AR: 10.8908
- TR: 0.22063
- kink: 0.366296
- rootadj: 0.546
- rtcs_0: 0.696703
- rtcs_1: 0.935556
- rtcs_2: 0.921389
- cambers_0: 0.32542
- cambers_1: 0.575196
- cambers_2: 0.173183
- twists_0: -3.33948
- twists_1: -3.81479
- twists_2: -2.87623
- twists_3: -2.23142
- Uroot_0: 0.135596
- Uroot_1: 0.0849547
- Uroot_2: 0.199881
- Uroot_3: -0.00376332
- Uroot_4: 0.382214
- Uroot_5: -0.163637
- Uroot_6: 0.540175
- Uroot_7: -0.0475996
- Uroot_8: 0.289549
- Uroot_9: 0.238541
- Utip_0: -0.125116
- Utip_1: -0.0373268
- Utip_2: -0.214954
- Utip_3: 0.0487864
- Utip_4: -0.309797
- Utip_5: 0.0176807
- Utip_6: -0.187762
- Utip_7: -0.0861474
- Utip_8: 0.071607
- Utip_9: 0.224508
- tcroot: 0.151907

## Operating condition
- angle of attack (aoa, deg): 9.6572
- Mach number: 0.856017

The wing was simulated with a RANS solver (ADflow). Estimate the integrated aerodynamic coefficients.

Respond with a single JSON object of the form {"cl": <lift coefficient>, "cd": <drag coefficient>, "cm": <pitching moment coefficient>} and nothing else. Values must be finite numbers within physical ranges (cl in [-0.5, 1.2], cd in [0, 0.2], cm in [-0.5, 1.5]).
