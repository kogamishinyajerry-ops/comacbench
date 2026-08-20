You are given the parametric geometry of a transonic kinked wing and a single operating condition, and must predict its aerodynamic coefficients.

## Wing geometry parameters
- SA: 33.9924
- DA: 5.7837
- DA_kink: 2.35527
- AR: 9.41211
- TR: 0.330286
- kink: 0.370347
- rootadj: 0.581645
- rtcs_0: 0.685147
- rtcs_1: 0.963147
- rtcs_2: 0.931097
- cambers_0: 0.422049
- cambers_1: 0.798445
- cambers_2: 0.178994
- twists_0: -3.59323
- twists_1: -2.18292
- twists_2: -1.21635
- twists_3: -2.28546
- Uroot_0: 0.132515
- Uroot_1: 0.13218
- Uroot_2: 0.195248
- Uroot_3: 0.081836
- Uroot_4: 0.259026
- Uroot_5: 0.18405
- Uroot_6: 0.213816
- Uroot_7: 0.140817
- Uroot_8: 0.291225
- Uroot_9: 0.0534317
- Utip_0: -0.149568
- Utip_1: -0.0516101
- Utip_2: -0.235854
- Utip_3: -0.038661
- Utip_4: -0.154433
- Utip_5: -0.0901926
- Utip_6: -0.113298
- Utip_7: -0.199857
- Utip_8: 0.1974
- Utip_9: 0.0910482
- tcroot: 0.140131

## Operating condition
- angle of attack (aoa, deg): 8.54233
- Mach number: 0.785258

The wing was simulated with a RANS solver (ADflow). Estimate the integrated aerodynamic coefficients.

Respond with a single JSON object of the form {"cl": <lift coefficient>, "cd": <drag coefficient>, "cm": <pitching moment coefficient>} and nothing else. Values must be finite numbers within physical ranges (cl in [-0.5, 1.2], cd in [0, 0.2], cm in [-0.5, 1.5]).
