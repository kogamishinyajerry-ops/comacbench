You are given the parametric geometry of a transonic kinked wing and a single operating condition, and must predict its aerodynamic coefficients.

## Wing geometry parameters
- SA: 29.2296
- DA: 5.5625
- DA_kink: 0.886696
- AR: 10.4674
- TR: 0.252496
- kink: 0.364497
- rootadj: 0.49545
- rtcs_0: 0.621909
- rtcs_1: 0.907303
- rtcs_2: 0.993069
- cambers_0: 0.697599
- cambers_1: 0.528513
- cambers_2: 0.756504
- twists_0: -2.85399
- twists_1: -2.53922
- twists_2: -2.93416
- twists_3: -1.46085
- Uroot_0: 0.188001
- Uroot_1: 0.10882
- Uroot_2: 0.225163
- Uroot_3: 0.0575202
- Uroot_4: 0.199646
- Uroot_5: 0.0882891
- Uroot_6: 0.237997
- Uroot_7: 0.041828
- Uroot_8: 0.142296
- Uroot_9: 0.302299
- Utip_0: -0.125115
- Utip_1: -0.0365849
- Utip_2: -0.223139
- Utip_3: 0.0472711
- Utip_4: -0.310608
- Utip_5: 0.0176069
- Utip_6: -0.193436
- Utip_7: -0.0840185
- Utip_8: 0.0715269
- Utip_9: 0.212127
- tcroot: 0.148807

## Operating condition
- angle of attack (aoa, deg): 5.22554
- Mach number: 0.863426

The wing was simulated with a RANS solver (ADflow). Estimate the integrated aerodynamic coefficients.

Respond with a single JSON object of the form {"cl": <lift coefficient>, "cd": <drag coefficient>, "cm": <pitching moment coefficient>} and nothing else. Values must be finite numbers within physical ranges (cl in [-0.5, 1.2], cd in [0, 0.2], cm in [-0.5, 1.5]).
