You are given the parametric geometry of a transonic kinked wing and a single operating condition, and must predict its aerodynamic coefficients.

## Wing geometry parameters
- SA: 38.5481
- DA: 7.4471
- DA_kink: 7.38661
- AR: 9.32775
- TR: 0.38355
- kink: 0.410252
- rootadj: 0.757252
- rtcs_0: 0.637441
- rtcs_1: 0.969967
- rtcs_2: 0.980436
- cambers_0: 0.392283
- cambers_1: 0.746574
- cambers_2: 0.525811
- twists_0: -3.16997
- twists_1: -2.31979
- twists_2: -1.19072
- twists_3: -1.32803
- Uroot_0: 0.18675
- Uroot_1: 0.145181
- Uroot_2: 0.042533
- Uroot_3: 0.312749
- Uroot_4: 0.0874347
- Uroot_5: -0.051569
- Uroot_6: 0.628569
- Uroot_7: -0.288863
- Uroot_8: 0.490223
- Uroot_9: 0.209132
- Utip_0: -0.123553
- Utip_1: -0.0407012
- Utip_2: -0.195587
- Utip_3: 0.0725395
- Utip_4: -0.308181
- Utip_5: 0.00394257
- Utip_6: -0.20683
- Utip_7: -0.0829116
- Utip_8: 0.0837542
- Utip_9: 0.235989
- tcroot: 0.165084

## Operating condition
- angle of attack (aoa, deg): 8.93615
- Mach number: 0.810731

The wing was simulated with a RANS solver (ADflow). Estimate the integrated aerodynamic coefficients.

Respond with a single JSON object of the form {"cl": <lift coefficient>, "cd": <drag coefficient>, "cm": <pitching moment coefficient>} and nothing else. Values must be finite numbers within physical ranges (cl in [-0.5, 1.2], cd in [0, 0.2], cm in [-0.5, 1.5]).
