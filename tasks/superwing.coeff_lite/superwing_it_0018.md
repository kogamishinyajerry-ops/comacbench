You are given the parametric geometry of a transonic kinked wing and a single operating condition, and must predict its aerodynamic coefficients.

## Wing geometry parameters
- SA: 39.9481
- DA: 4.18082
- DA_kink: 3.35213
- AR: 10.055
- TR: 0.246307
- kink: 0.410737
- rootadj: 0.644671
- rtcs_0: 0.684153
- rtcs_1: 0.971786
- rtcs_2: 0.958548
- cambers_0: 0.624677
- cambers_1: 0.640829
- cambers_2: 0.50656
- twists_0: -3.24433
- twists_1: -3.97576
- twists_2: -1.71096
- twists_3: -2.07039
- Uroot_0: 0.152564
- Uroot_1: 0.134335
- Uroot_2: 0.216132
- Uroot_3: 0.0229088
- Uroot_4: 0.490637
- Uroot_5: -0.0634195
- Uroot_6: 0.474511
- Uroot_7: 0.197755
- Uroot_8: 0.345333
- Uroot_9: 0.420673
- Utip_0: -0.158272
- Utip_1: -0.0424699
- Utip_2: -0.288695
- Utip_3: 0.0663267
- Utip_4: -0.400511
- Utip_5: 0.0229849
- Utip_6: -0.249971
- Utip_7: -0.109783
- Utip_8: 0.0930892
- Utip_9: 0.292529
- tcroot: 0.166775

## Operating condition
- angle of attack (aoa, deg): 6.10883
- Mach number: 0.767897

The wing was simulated with a RANS solver (ADflow). Estimate the integrated aerodynamic coefficients.

Respond with a single JSON object of the form {"cl": <lift coefficient>, "cd": <drag coefficient>, "cm": <pitching moment coefficient>} and nothing else. Values must be finite numbers within physical ranges (cl in [-0.5, 1.2], cd in [0, 0.2], cm in [-0.5, 1.5]).
