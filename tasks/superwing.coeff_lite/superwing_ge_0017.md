You are given the parametric geometry of a transonic kinked wing and a single operating condition, and must predict its aerodynamic coefficients.

## Wing geometry parameters
- SA: 38.5726
- DA: 4.20062
- DA_kink: 2.33198
- AR: 9.71704
- TR: 0.287185
- kink: 0.379576
- rootadj: 0.362714
- rtcs_0: 0.684981
- rtcs_1: 0.907176
- rtcs_2: 0.962748
- cambers_0: 0.311275
- cambers_1: 0.538291
- cambers_2: 0.670995
- twists_0: -2.42954
- twists_1: -3.52465
- twists_2: -1.77476
- twists_3: -2.75899
- Uroot_0: 0.140817
- Uroot_1: 0.0783212
- Uroot_2: 0.195904
- Uroot_3: -0.00973039
- Uroot_4: 0.427962
- Uroot_5: -0.190391
- Uroot_6: 0.602131
- Uroot_7: -0.0770885
- Uroot_8: 0.32297
- Uroot_9: 0.256943
- Utip_0: -0.123196
- Utip_1: -0.0321906
- Utip_2: -0.218121
- Utip_3: 0.0674769
- Utip_4: -0.345429
- Utip_5: 0.0327617
- Utip_6: -0.17913
- Utip_7: -0.087573
- Utip_8: 0.068854
- Utip_9: 0.230585
- tcroot: 0.156489

## Operating condition
- angle of attack (aoa, deg): 5.37286
- Mach number: 0.791047

The wing was simulated with a RANS solver (ADflow). Estimate the integrated aerodynamic coefficients.

Respond with a single JSON object of the form {"cl": <lift coefficient>, "cd": <drag coefficient>, "cm": <pitching moment coefficient>} and nothing else. Values must be finite numbers within physical ranges (cl in [-0.5, 1.2], cd in [0, 0.2], cm in [-0.5, 1.5]).
