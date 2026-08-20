You are given the parametric geometry of a transonic kinked wing and a single operating condition, and must predict its aerodynamic coefficients.

## Wing geometry parameters
- SA: 31.679
- DA: 6.45464
- DA_kink: 2.59604
- AR: 8.69489
- TR: 0.258137
- kink: 0.391552
- rootadj: 0.977834
- rtcs_0: 0.636728
- rtcs_1: 0.96747
- rtcs_2: 0.928228
- cambers_0: 0.652678
- cambers_1: 0.966363
- cambers_2: 0.18984
- twists_0: -2.23637
- twists_1: -3.78422
- twists_2: -2.38136
- twists_3: -2.46803
- Uroot_0: 0.131888
- Uroot_1: 0.13415
- Uroot_2: 0.197746
- Uroot_3: 0.0975297
- Uroot_4: 0.267968
- Uroot_5: 0.217232
- Uroot_6: 0.19191
- Uroot_7: 0.144615
- Uroot_8: 0.292313
- Uroot_9: 0.132607
- Utip_0: -0.149455
- Utip_1: -0.0609722
- Utip_2: -0.228997
- Utip_3: -0.0457367
- Utip_4: -0.161397
- Utip_5: -0.0939332
- Utip_6: -0.094214
- Utip_7: -0.200399
- Utip_8: 0.2
- Utip_9: 0.153683
- tcroot: 0.15438

## Operating condition
- angle of attack (aoa, deg): 6.86234
- Mach number: 0.764699

The wing was simulated with a RANS solver (ADflow). Estimate the integrated aerodynamic coefficients.

Respond with a single JSON object of the form {"cl": <lift coefficient>, "cd": <drag coefficient>, "cm": <pitching moment coefficient>} and nothing else. Values must be finite numbers within physical ranges (cl in [-0.5, 1.2], cd in [0, 0.2], cm in [-0.5, 1.5]).
