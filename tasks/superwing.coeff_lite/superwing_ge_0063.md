You are given the parametric geometry of a transonic kinked wing and a single operating condition, and must predict its aerodynamic coefficients.

## Wing geometry parameters
- SA: 35.5229
- DA: 6.72273
- DA_kink: 3.65651
- AR: 9.1543
- TR: 0.360458
- kink: 0.416103
- rootadj: 1.08403
- rtcs_0: 0.649129
- rtcs_1: 0.97281
- rtcs_2: 0.94065
- cambers_0: 0.390377
- cambers_1: 0.833541
- cambers_2: 0.15577
- twists_0: -2.93341
- twists_1: -3.43068
- twists_2: -1.61844
- twists_3: -2.73404
- Uroot_0: 0.195445
- Uroot_1: 0.143689
- Uroot_2: 0.359146
- Uroot_3: -0.110049
- Uroot_4: 0.517244
- Uroot_5: -0.062264
- Uroot_6: 0.373846
- Uroot_7: 0.23653
- Uroot_8: 0.251233
- Uroot_9: 0.276198
- Utip_0: -0.162651
- Utip_1: -0.0485249
- Utip_2: -0.274856
- Utip_3: 0.0741382
- Utip_4: -0.40373
- Utip_5: 0.0291201
- Utip_6: -0.25113
- Utip_7: -0.120435
- Utip_8: 0.0930892
- Utip_9: 0.293699
- tcroot: 0.168137

## Operating condition
- angle of attack (aoa, deg): 2.1171
- Mach number: 0.755196

The wing was simulated with a RANS solver (ADflow). Estimate the integrated aerodynamic coefficients.

Respond with a single JSON object of the form {"cl": <lift coefficient>, "cd": <drag coefficient>, "cm": <pitching moment coefficient>} and nothing else. Values must be finite numbers within physical ranges (cl in [-0.5, 1.2], cd in [0, 0.2], cm in [-0.5, 1.5]).
