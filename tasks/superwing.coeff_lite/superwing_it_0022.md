You are given the parametric geometry of a transonic kinked wing and a single operating condition, and must predict its aerodynamic coefficients.

## Wing geometry parameters
- SA: 34.8316
- DA: 4.55102
- DA_kink: 5.89996
- AR: 8.60171
- TR: 0.264204
- kink: 0.398799
- rootadj: 0.561445
- rtcs_0: 0.602091
- rtcs_1: 0.973644
- rtcs_2: 0.960533
- cambers_0: 0.764905
- cambers_1: 0.575809
- cambers_2: 0.441159
- twists_0: -3.46268
- twists_1: -2.2415
- twists_2: -1.92344
- twists_3: -2.2063
- Uroot_0: 0.200377
- Uroot_1: 0.143922
- Uroot_2: 0.317447
- Uroot_3: -0.0824782
- Uroot_4: 0.502445
- Uroot_5: -0.0750788
- Uroot_6: 0.463296
- Uroot_7: 0.0796822
- Uroot_8: 0.250602
- Uroot_9: 0.452568
- Utip_0: -0.162651
- Utip_1: -0.0485249
- Utip_2: -0.27944
- Utip_3: 0.0653081
- Utip_4: -0.403601
- Utip_5: 0.0229849
- Utip_6: -0.24406
- Utip_7: -0.111992
- Utip_8: 0.0930892
- Utip_9: 0.292329
- tcroot: 0.164598

## Operating condition
- angle of attack (aoa, deg): 5.98468
- Mach number: 0.753205

The wing was simulated with a RANS solver (ADflow). Estimate the integrated aerodynamic coefficients.

Respond with a single JSON object of the form {"cl": <lift coefficient>, "cd": <drag coefficient>, "cm": <pitching moment coefficient>} and nothing else. Values must be finite numbers within physical ranges (cl in [-0.5, 1.2], cd in [0, 0.2], cm in [-0.5, 1.5]).
