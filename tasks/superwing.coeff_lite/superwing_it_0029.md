You are given the parametric geometry of a transonic kinked wing and a single operating condition, and must predict its aerodynamic coefficients.

## Wing geometry parameters
- SA: 39.1551
- DA: 5.95122
- DA_kink: 3.44344
- AR: 9.75102
- TR: 0.399236
- kink: 0.361963
- rootadj: 0.638502
- rtcs_0: 0.685079
- rtcs_1: 0.927874
- rtcs_2: 0.967329
- cambers_0: 0.702878
- cambers_1: 0.79992
- cambers_2: 0.192637
- twists_0: -3.72765
- twists_1: -2.09753
- twists_2: -2.63517
- twists_3: -1.49132
- Uroot_0: 0.148998
- Uroot_1: 0.131561
- Uroot_2: 0.194588
- Uroot_3: -0.0787859
- Uroot_4: 0.591067
- Uroot_5: -0.254015
- Uroot_6: 0.44234
- Uroot_7: 0.249233
- Uroot_8: 0.238872
- Uroot_9: 0.138992
- Utip_0: -0.123092
- Utip_1: -0.138363
- Utip_2: -0.125894
- Utip_3: -0.160322
- Utip_4: -0.177137
- Utip_5: -0.156611
- Utip_6: -0.0987278
- Utip_7: -0.0601823
- Utip_8: -0.042927
- Utip_9: 0.0359014
- tcroot: 0.163151

## Operating condition
- angle of attack (aoa, deg): 7.25406
- Mach number: 0.842669

The wing was simulated with a RANS solver (ADflow). Estimate the integrated aerodynamic coefficients.

Respond with a single JSON object of the form {"cl": <lift coefficient>, "cd": <drag coefficient>, "cm": <pitching moment coefficient>} and nothing else. Values must be finite numbers within physical ranges (cl in [-0.5, 1.2], cd in [0, 0.2], cm in [-0.5, 1.5]).
