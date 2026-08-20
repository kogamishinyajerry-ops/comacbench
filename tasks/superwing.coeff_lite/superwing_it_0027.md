You are given the parametric geometry of a transonic kinked wing and a single operating condition, and must predict its aerodynamic coefficients.

## Wing geometry parameters
- SA: 25.4462
- DA: 4.41176
- DA_kink: 0.606366
- AR: 10.8928
- TR: 0.292881
- kink: 0.395319
- rootadj: 0.536894
- rtcs_0: 0.612295
- rtcs_1: 0.969726
- rtcs_2: 0.991767
- cambers_0: 0.333864
- cambers_1: 0.706779
- cambers_2: 0.236282
- twists_0: -2.46376
- twists_1: -3.11128
- twists_2: -1.49123
- twists_3: -1.09197
- Uroot_0: 0.19468
- Uroot_1: 0.108878
- Uroot_2: 0.116065
- Uroot_3: 0.210876
- Uroot_4: 0.10455
- Uroot_5: 0.0480446
- Uroot_6: 0.448297
- Uroot_7: -0.0886015
- Uroot_8: 0.443865
- Uroot_9: 0.272668
- Utip_0: -0.126284
- Utip_1: -0.0373268
- Utip_2: -0.214954
- Utip_3: 0.050237
- Utip_4: -0.309453
- Utip_5: 0.0176807
- Utip_6: -0.187762
- Utip_7: -0.0861474
- Utip_8: 0.0725788
- Utip_9: 0.224868
- tcroot: 0.147493

## Operating condition
- angle of attack (aoa, deg): 2.15753
- Mach number: 0.846992

The wing was simulated with a RANS solver (ADflow). Estimate the integrated aerodynamic coefficients.

Respond with a single JSON object of the form {"cl": <lift coefficient>, "cd": <drag coefficient>, "cm": <pitching moment coefficient>} and nothing else. Values must be finite numbers within physical ranges (cl in [-0.5, 1.2], cd in [0, 0.2], cm in [-0.5, 1.5]).
