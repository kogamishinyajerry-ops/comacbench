You are given the parametric geometry of a transonic kinked wing and a single operating condition, and must predict its aerodynamic coefficients.

## Wing geometry parameters
- SA: 34.7149
- DA: 9.10813
- DA_kink: 5.21752
- AR: 9.0444
- TR: 0.284831
- kink: 0.37508
- rootadj: 0.770419
- rtcs_0: 0.61528
- rtcs_1: 0.949715
- rtcs_2: 0.921155
- cambers_0: 0.705355
- cambers_1: 0.557581
- cambers_2: 0.275772
- twists_0: -2.39034
- twists_1: -3.30721
- twists_2: -2.61143
- twists_3: -1.30831
- Uroot_0: 0.19459
- Uroot_1: 0.108878
- Uroot_2: 0.116065
- Uroot_3: 0.210165
- Uroot_4: 0.10455
- Uroot_5: 0.0482396
- Uroot_6: 0.4489
- Uroot_7: -0.088421
- Uroot_8: 0.443865
- Uroot_9: 0.272668
- Utip_0: -0.126284
- Utip_1: -0.0373268
- Utip_2: -0.215174
- Utip_3: 0.0501733
- Utip_4: -0.309453
- Utip_5: 0.0176807
- Utip_6: -0.187903
- Utip_7: -0.0861474
- Utip_8: 0.0725788
- Utip_9: 0.224868
- tcroot: 0.148731

## Operating condition
- angle of attack (aoa, deg): 10.7776
- Mach number: 0.804443

The wing was simulated with a RANS solver (ADflow). Estimate the integrated aerodynamic coefficients.

Respond with a single JSON object of the form {"cl": <lift coefficient>, "cd": <drag coefficient>, "cm": <pitching moment coefficient>} and nothing else. Values must be finite numbers within physical ranges (cl in [-0.5, 1.2], cd in [0, 0.2], cm in [-0.5, 1.5]).
