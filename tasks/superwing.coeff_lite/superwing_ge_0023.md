You are given the parametric geometry of a transonic kinked wing and a single operating condition, and must predict its aerodynamic coefficients.

## Wing geometry parameters
- SA: 29.3598
- DA: 4.92701
- DA_kink: 0.783535
- AR: 10.5814
- TR: 0.243952
- kink: 0.377812
- rootadj: 0.197446
- rtcs_0: 0.669231
- rtcs_1: 0.9163
- rtcs_2: 0.995282
- cambers_0: 0.307731
- cambers_1: 0.949273
- cambers_2: 0.615191
- twists_0: -2.32398
- twists_1: -3.48198
- twists_2: -1.20896
- twists_3: -2.39146
- Uroot_0: 0.132071
- Uroot_1: 0.0794729
- Uroot_2: 0.197542
- Uroot_3: -0.00924795
- Uroot_4: 0.382583
- Uroot_5: -0.170058
- Uroot_6: 0.559454
- Uroot_7: -0.0332172
- Uroot_8: 0.274442
- Uroot_9: 0.24698
- Utip_0: -0.124385
- Utip_1: -0.0362811
- Utip_2: -0.213726
- Utip_3: 0.0532962
- Utip_4: -0.313926
- Utip_5: 0.0213788
- Utip_6: -0.191097
- Utip_7: -0.0822972
- Utip_8: 0.0661694
- Utip_9: 0.229224
- tcroot: 0.146876

## Operating condition
- angle of attack (aoa, deg): 7.15556
- Mach number: 0.871975

The wing was simulated with a RANS solver (ADflow). Estimate the integrated aerodynamic coefficients.

Respond with a single JSON object of the form {"cl": <lift coefficient>, "cd": <drag coefficient>, "cm": <pitching moment coefficient>} and nothing else. Values must be finite numbers within physical ranges (cl in [-0.5, 1.2], cd in [0, 0.2], cm in [-0.5, 1.5]).
