You are given the parametric geometry of a transonic kinked wing and a single operating condition, and must predict its aerodynamic coefficients.

## Wing geometry parameters
- SA: 36.7341
- DA: 4.31946
- DA_kink: 4.22337
- AR: 10.5421
- TR: 0.30064
- kink: 0.387788
- rootadj: 0.552346
- rtcs_0: 0.660274
- rtcs_1: 0.976979
- rtcs_2: 0.933655
- cambers_0: 0.701371
- cambers_1: 0.863026
- cambers_2: 0.00247599
- twists_0: -2.54472
- twists_1: -2.9402
- twists_2: -1.5741
- twists_3: -2.22011
- Uroot_0: 0.140733
- Uroot_1: 0.138653
- Uroot_2: 0.190091
- Uroot_3: 0.0826731
- Uroot_4: 0.251615
- Uroot_5: 0.239653
- Uroot_6: 0.225968
- Uroot_7: 0.1309
- Uroot_8: 0.266696
- Uroot_9: 0.125896
- Utip_0: -0.150885
- Utip_1: -0.0426435
- Utip_2: -0.232863
- Utip_3: -0.0418347
- Utip_4: -0.146982
- Utip_5: -0.10631
- Utip_6: -0.0938383
- Utip_7: -0.190001
- Utip_8: 0.2
- Utip_9: 0.16388
- tcroot: 0.147884

## Operating condition
- angle of attack (aoa, deg): 5.78089
- Mach number: 0.783332

The wing was simulated with a RANS solver (ADflow). Estimate the integrated aerodynamic coefficients.

Respond with a single JSON object of the form {"cl": <lift coefficient>, "cd": <drag coefficient>, "cm": <pitching moment coefficient>} and nothing else. Values must be finite numbers within physical ranges (cl in [-0.5, 1.2], cd in [0, 0.2], cm in [-0.5, 1.5]).
