You are given the parametric geometry of a transonic kinked wing and a single operating condition, and must predict its aerodynamic coefficients.

## Wing geometry parameters
- SA: 29.331
- DA: 5.85935
- DA_kink: 3.88397
- AR: 10.4701
- TR: 0.157592
- kink: 0.360849
- rootadj: 0.141445
- rtcs_0: 0.630123
- rtcs_1: 0.924592
- rtcs_2: 0.986921
- cambers_0: 0.620243
- cambers_1: 0.600407
- cambers_2: 0.550396
- twists_0: -3.36368
- twists_1: -2.85819
- twists_2: -1.32646
- twists_3: -2.39705
- Uroot_0: 0.132254
- Uroot_1: 0.0788282
- Uroot_2: 0.201483
- Uroot_3: -0.0251224
- Uroot_4: 0.409417
- Uroot_5: -0.212443
- Uroot_6: 0.602028
- Uroot_7: -0.050742
- Uroot_8: 0.31547
- Uroot_9: 0.252493
- Utip_0: -0.123504
- Utip_1: -0.0367675
- Utip_2: -0.213578
- Utip_3: 0.0543323
- Utip_4: -0.315019
- Utip_5: 0.0249587
- Utip_6: -0.193967
- Utip_7: -0.0779301
- Utip_8: 0.0631028
- Utip_9: 0.228783
- tcroot: 0.148219

## Operating condition
- angle of attack (aoa, deg): 7.44764
- Mach number: 0.828171

The wing was simulated with a RANS solver (ADflow). Estimate the integrated aerodynamic coefficients.

Respond with a single JSON object of the form {"cl": <lift coefficient>, "cd": <drag coefficient>, "cm": <pitching moment coefficient>} and nothing else. Values must be finite numbers within physical ranges (cl in [-0.5, 1.2], cd in [0, 0.2], cm in [-0.5, 1.5]).
