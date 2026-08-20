You are given the parametric geometry of a transonic kinked wing and a single operating condition, and must predict its aerodynamic coefficients.

## Wing geometry parameters
- SA: 37.9399
- DA: 4.03438
- DA_kink: 1.93611
- AR: 10.3779
- TR: 0.227873
- kink: 0.392796
- rootadj: 0.794543
- rtcs_0: 0.690875
- rtcs_1: 0.948337
- rtcs_2: 0.957397
- cambers_0: 0.667159
- cambers_1: 0.576055
- cambers_2: 0.412435
- twists_0: -3.87357
- twists_1: -2.26122
- twists_2: -2.73566
- twists_3: -1.19287
- Uroot_0: 0.150596
- Uroot_1: 0.112467
- Uroot_2: 0.202898
- Uroot_3: 0.0115928
- Uroot_4: 0.445098
- Uroot_5: -0.0538019
- Uroot_6: 0.268393
- Uroot_7: 0.238666
- Uroot_8: 0.0484943
- Uroot_9: 0.344093
- Utip_0: -0.105598
- Utip_1: -0.0966262
- Utip_2: -0.173483
- Utip_3: -0.0970615
- Utip_4: -0.229604
- Utip_5: -0.0593951
- Utip_6: -0.290351
- Utip_7: 0.0157493
- Utip_8: -0.190637
- Utip_9: 0.193968
- tcroot: 0.158002

## Operating condition
- angle of attack (aoa, deg): 5.73461
- Mach number: 0.840338

The wing was simulated with a RANS solver (ADflow). Estimate the integrated aerodynamic coefficients.

Respond with a single JSON object of the form {"cl": <lift coefficient>, "cd": <drag coefficient>, "cm": <pitching moment coefficient>} and nothing else. Values must be finite numbers within physical ranges (cl in [-0.5, 1.2], cd in [0, 0.2], cm in [-0.5, 1.5]).
