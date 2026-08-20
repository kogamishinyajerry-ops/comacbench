You are given the parametric geometry of a transonic kinked wing and a single operating condition, and must predict its aerodynamic coefficients.

## Wing geometry parameters
- SA: 39.4016
- DA: 4.88935
- DA_kink: 5.78946
- AR: 9.95122
- TR: 0.333519
- kink: 0.365818
- rootadj: 0.469363
- rtcs_0: 0.624003
- rtcs_1: 0.909748
- rtcs_2: 0.993617
- cambers_0: 0.749642
- cambers_1: 0.717136
- cambers_2: 0.0945046
- twists_0: -2.14816
- twists_1: -3.91853
- twists_2: -1.64037
- twists_3: -1.35278
- Uroot_0: 0.125677
- Uroot_1: 0.0993112
- Uroot_2: 0.205028
- Uroot_3: -0.0118514
- Uroot_4: 0.39469
- Uroot_5: -0.13739
- Uroot_6: 0.535045
- Uroot_7: -0.0269908
- Uroot_8: 0.304355
- Uroot_9: 0.240281
- Utip_0: -0.125116
- Utip_1: -0.0352151
- Utip_2: -0.21155
- Utip_3: 0.0522851
- Utip_4: -0.310562
- Utip_5: 0.0173008
- Utip_6: -0.187762
- Utip_7: -0.0953357
- Utip_8: 0.0557942
- Utip_9: 0.204273
- tcroot: 0.149496

## Operating condition
- angle of attack (aoa, deg): 4.8606
- Mach number: 0.853353

The wing was simulated with a RANS solver (ADflow). Estimate the integrated aerodynamic coefficients.

Respond with a single JSON object of the form {"cl": <lift coefficient>, "cd": <drag coefficient>, "cm": <pitching moment coefficient>} and nothing else. Values must be finite numbers within physical ranges (cl in [-0.5, 1.2], cd in [0, 0.2], cm in [-0.5, 1.5]).
