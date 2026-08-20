You are given the parametric geometry of a transonic kinked wing and a single operating condition, and must predict its aerodynamic coefficients.

## Wing geometry parameters
- SA: 28.6889
- DA: 5.38719
- DA_kink: 1.1148
- AR: 10.1305
- TR: 0.356126
- kink: 0.386321
- rootadj: 0.383727
- rtcs_0: 0.672733
- rtcs_1: 0.973727
- rtcs_2: 0.977529
- cambers_0: 0.390791
- cambers_1: 0.502758
- cambers_2: 0.438994
- twists_0: -3.63906
- twists_1: -2.8324
- twists_2: -2.77738
- twists_3: -1.8759
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
- tcroot: 0.148188

## Operating condition
- angle of attack (aoa, deg): 9.77476
- Mach number: 0.811578

The wing was simulated with a RANS solver (ADflow). Estimate the integrated aerodynamic coefficients.

Respond with a single JSON object of the form {"cl": <lift coefficient>, "cd": <drag coefficient>, "cm": <pitching moment coefficient>} and nothing else. Values must be finite numbers within physical ranges (cl in [-0.5, 1.2], cd in [0, 0.2], cm in [-0.5, 1.5]).
