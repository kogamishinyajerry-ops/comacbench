You are given the parametric geometry of a transonic kinked wing and a single operating condition, and must predict its aerodynamic coefficients.

## Wing geometry parameters
- SA: 30.6377
- DA: 4.52239
- DA_kink: 5.85079
- AR: 8.29537
- TR: 0.177416
- kink: 0.412036
- rootadj: 0.37622
- rtcs_0: 0.691252
- rtcs_1: 0.91159
- rtcs_2: 0.924768
- cambers_0: 0.725623
- cambers_1: 0.925657
- cambers_2: 0.429986
- twists_0: -2.28268
- twists_1: -2.85384
- twists_2: -2.17973
- twists_3: -2.5329
- Uroot_0: 0.195911
- Uroot_1: 0.123337
- Uroot_2: 0.116065
- Uroot_3: 0.210165
- Uroot_4: 0.10455
- Uroot_5: 0.0482396
- Uroot_6: 0.4489
- Uroot_7: -0.0936401
- Uroot_8: 0.443865
- Uroot_9: 0.281038
- Utip_0: -0.126284
- Utip_1: -0.0428887
- Utip_2: -0.225654
- Utip_3: 0.0457118
- Utip_4: -0.309453
- Utip_5: 0.0171218
- Utip_6: -0.186247
- Utip_7: -0.0946069
- Utip_8: 0.0725515
- Utip_9: 0.211863
- tcroot: 0.146544

## Operating condition
- angle of attack (aoa, deg): 5.62712
- Mach number: 0.812547

The wing was simulated with a RANS solver (ADflow). Estimate the integrated aerodynamic coefficients.

Respond with a single JSON object of the form {"cl": <lift coefficient>, "cd": <drag coefficient>, "cm": <pitching moment coefficient>} and nothing else. Values must be finite numbers within physical ranges (cl in [-0.5, 1.2], cd in [0, 0.2], cm in [-0.5, 1.5]).
