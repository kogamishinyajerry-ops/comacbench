You are given the parametric geometry of a transonic kinked wing and a single operating condition, and must predict its aerodynamic coefficients.

## Wing geometry parameters
- SA: 27.0964
- DA: 9.5899
- DA_kink: 4.67503
- AR: 8.3523
- TR: 0.276013
- kink: 0.414074
- rootadj: 0.986502
- rtcs_0: 0.638763
- rtcs_1: 0.929312
- rtcs_2: 0.991205
- cambers_0: 0.633205
- cambers_1: 0.763273
- cambers_2: 0.21982
- twists_0: -3.83328
- twists_1: -2.80933
- twists_2: -1.028
- twists_3: -1.20075
- Uroot_0: 0.157765
- Uroot_1: 0.093126
- Uroot_2: 0.257291
- Uroot_3: 0.0718822
- Uroot_4: 0.317394
- Uroot_5: 0.072964
- Uroot_6: 0.366793
- Uroot_7: 0.218093
- Uroot_8: 0.290605
- Uroot_9: 0.31624
- Utip_0: -0.162654
- Utip_1: -0.0485249
- Utip_2: -0.27944
- Utip_3: 0.0653081
- Utip_4: -0.40373
- Utip_5: 0.022983
- Utip_6: -0.24409
- Utip_7: -0.11205
- Utip_8: 0.0930893
- Utip_9: 0.292295
- tcroot: 0.168114

## Operating condition
- angle of attack (aoa, deg): 7.70294
- Mach number: 0.763938

The wing was simulated with a RANS solver (ADflow). Estimate the integrated aerodynamic coefficients.

Respond with a single JSON object of the form {"cl": <lift coefficient>, "cd": <drag coefficient>, "cm": <pitching moment coefficient>} and nothing else. Values must be finite numbers within physical ranges (cl in [-0.5, 1.2], cd in [0, 0.2], cm in [-0.5, 1.5]).
