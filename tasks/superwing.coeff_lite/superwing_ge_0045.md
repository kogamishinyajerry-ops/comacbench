You are given the parametric geometry of a transonic kinked wing and a single operating condition, and must predict its aerodynamic coefficients.

## Wing geometry parameters
- SA: 31.8202
- DA: 7.67064
- DA_kink: 3.58059
- AR: 10.2636
- TR: 0.315567
- kink: 0.37467
- rootadj: 1.05228
- rtcs_0: 0.615469
- rtcs_1: 0.925634
- rtcs_2: 0.987227
- cambers_0: 0.651822
- cambers_1: 0.77493
- cambers_2: 0.199326
- twists_0: -2.01212
- twists_1: -2.34362
- twists_2: -1.17749
- twists_3: -2.11822
- Uroot_0: 0.196271
- Uroot_1: 0.132866
- Uroot_2: 0.321684
- Uroot_3: -0.130441
- Uroot_4: 0.637305
- Uroot_5: -0.2604
- Uroot_6: 0.58442
- Uroot_7: 0.052928
- Uroot_8: 0.352247
- Uroot_9: 0.316147
- Utip_0: -0.163286
- Utip_1: -0.0485249
- Utip_2: -0.27944
- Utip_3: 0.0653081
- Utip_4: -0.403271
- Utip_5: 0.0229849
- Utip_6: -0.244719
- Utip_7: -0.111992
- Utip_8: 0.0934259
- Utip_9: 0.291319
- tcroot: 0.169586

## Operating condition
- angle of attack (aoa, deg): 3.06238
- Mach number: 0.770172

The wing was simulated with a RANS solver (ADflow). Estimate the integrated aerodynamic coefficients.

Respond with a single JSON object of the form {"cl": <lift coefficient>, "cd": <drag coefficient>, "cm": <pitching moment coefficient>} and nothing else. Values must be finite numbers within physical ranges (cl in [-0.5, 1.2], cd in [0, 0.2], cm in [-0.5, 1.5]).
