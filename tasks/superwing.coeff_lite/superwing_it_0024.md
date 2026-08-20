You are given the parametric geometry of a transonic kinked wing and a single operating condition, and must predict its aerodynamic coefficients.

## Wing geometry parameters
- SA: 37.5237
- DA: 4.02268
- DA_kink: 3.62999
- AR: 10.3489
- TR: 0.333938
- kink: 0.385319
- rootadj: 0.4046
- rtcs_0: 0.612182
- rtcs_1: 0.967001
- rtcs_2: 0.944366
- cambers_0: 0.631292
- cambers_1: 0.785869
- cambers_2: 0.159907
- twists_0: -2.93041
- twists_1: -2.53604
- twists_2: -1.89336
- twists_3: -2.88686
- Uroot_0: 0.203561
- Uroot_1: 0.117528
- Uroot_2: 0.204517
- Uroot_3: 0.132732
- Uroot_4: 0.198356
- Uroot_5: 0.193321
- Uroot_6: 0.208348
- Uroot_7: 0.135302
- Uroot_8: 0.321591
- Uroot_9: 0.320937
- Utip_0: -0.150139
- Utip_1: -0.0447922
- Utip_2: -0.257944
- Utip_3: 0.0601758
- Utip_4: -0.372674
- Utip_5: 0.0212169
- Utip_6: -0.225652
- Utip_7: -0.103377
- Utip_8: 0.0859285
- Utip_9: 0.269842
- tcroot: 0.153246

## Operating condition
- angle of attack (aoa, deg): 3.17011
- Mach number: 0.826077

The wing was simulated with a RANS solver (ADflow). Estimate the integrated aerodynamic coefficients.

Respond with a single JSON object of the form {"cl": <lift coefficient>, "cd": <drag coefficient>, "cm": <pitching moment coefficient>} and nothing else. Values must be finite numbers within physical ranges (cl in [-0.5, 1.2], cd in [0, 0.2], cm in [-0.5, 1.5]).
