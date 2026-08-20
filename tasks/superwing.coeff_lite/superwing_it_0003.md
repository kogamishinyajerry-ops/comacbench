You are given the parametric geometry of a transonic kinked wing and a single operating condition, and must predict its aerodynamic coefficients.

## Wing geometry parameters
- SA: 35.9557
- DA: 5.64019
- DA_kink: 2.34111
- AR: 10.4941
- TR: 0.32004
- kink: 0.390977
- rootadj: 0.589634
- rtcs_0: 0.654692
- rtcs_1: 0.973255
- rtcs_2: 0.977714
- cambers_0: 0.505551
- cambers_1: 0.729453
- cambers_2: 0.345373
- twists_0: -3.90632
- twists_1: -2.9505
- twists_2: -2.56358
- twists_3: -2.29226
- Uroot_0: 0.177836
- Uroot_1: 0.0970596
- Uroot_2: 0.286581
- Uroot_3: -0.01256
- Uroot_4: 0.455337
- Uroot_5: -0.054111
- Uroot_6: 0.430516
- Uroot_7: 0.125618
- Uroot_8: 0.31768
- Uroot_9: 0.333835
- Utip_0: -0.162651
- Utip_1: -0.0485249
- Utip_2: -0.27944
- Utip_3: 0.0653081
- Utip_4: -0.40373
- Utip_5: 0.0229849
- Utip_6: -0.24409
- Utip_7: -0.111992
- Utip_8: 0.0930892
- Utip_9: 0.292329
- tcroot: 0.168735

## Operating condition
- angle of attack (aoa, deg): 9.96884
- Mach number: 0.763723

The wing was simulated with a RANS solver (ADflow). Estimate the integrated aerodynamic coefficients.

Respond with a single JSON object of the form {"cl": <lift coefficient>, "cd": <drag coefficient>, "cm": <pitching moment coefficient>} and nothing else. Values must be finite numbers within physical ranges (cl in [-0.5, 1.2], cd in [0, 0.2], cm in [-0.5, 1.5]).
