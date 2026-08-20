You are given the parametric geometry of a transonic kinked wing and a single operating condition, and must predict its aerodynamic coefficients.

## Wing geometry parameters
- SA: 36.6542
- DA: 9.4451
- DA_kink: 2.81093
- AR: 9.87438
- TR: 0.318935
- kink: 0.384123
- rootadj: 0.956224
- rtcs_0: 0.63924
- rtcs_1: 0.973003
- rtcs_2: 0.993722
- cambers_0: 0.717337
- cambers_1: 0.899249
- cambers_2: 0.659778
- twists_0: -2.1908
- twists_1: -2.98782
- twists_2: -1.70319
- twists_3: -1.56768
- Uroot_0: 0.133394
- Uroot_1: 0.0823462
- Uroot_2: 0.20277
- Uroot_3: -0.0162854
- Uroot_4: 0.397033
- Uroot_5: -0.184252
- Uroot_6: 0.571002
- Uroot_7: -0.0341312
- Uroot_8: 0.311971
- Uroot_9: 0.243548
- Utip_0: -0.125064
- Utip_1: -0.0373268
- Utip_2: -0.21477
- Utip_3: 0.0502664
- Utip_4: -0.310562
- Utip_5: 0.017798
- Utip_6: -0.187762
- Utip_7: -0.0861474
- Utip_8: 0.071607
- Utip_9: 0.224868
- tcroot: 0.140054

## Operating condition
- angle of attack (aoa, deg): 9.19834
- Mach number: 0.88589

The wing was simulated with a RANS solver (ADflow). Estimate the integrated aerodynamic coefficients.

Respond with a single JSON object of the form {"cl": <lift coefficient>, "cd": <drag coefficient>, "cm": <pitching moment coefficient>} and nothing else. Values must be finite numbers within physical ranges (cl in [-0.5, 1.2], cd in [0, 0.2], cm in [-0.5, 1.5]).
