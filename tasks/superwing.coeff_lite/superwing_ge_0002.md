You are given the parametric geometry of a transonic kinked wing and a single operating condition, and must predict its aerodynamic coefficients.

## Wing geometry parameters
- SA: 27.3958
- DA: 5.26392
- DA_kink: 2.91544
- AR: 9.60031
- TR: 0.246647
- kink: 0.40316
- rootadj: 1.05841
- rtcs_0: 0.619542
- rtcs_1: 0.950205
- rtcs_2: 0.986757
- cambers_0: 0.640045
- cambers_1: 0.908001
- cambers_2: 0.0695289
- twists_0: -2.5685
- twists_1: -2.32979
- twists_2: -2.07798
- twists_3: -1.15403
- Uroot_0: 0.128299
- Uroot_1: 0.127324
- Uroot_2: 0.240024
- Uroot_3: 0.0824143
- Uroot_4: 0.251484
- Uroot_5: 0.206163
- Uroot_6: 0.199012
- Uroot_7: 0.151562
- Uroot_8: 0.29169
- Uroot_9: 0.046005
- Utip_0: -0.150877
- Utip_1: -0.0523298
- Utip_2: -0.226467
- Utip_3: -0.0364123
- Utip_4: -0.278501
- Utip_5: -0.106198
- Utip_6: -0.0951745
- Utip_7: -0.205952
- Utip_8: 0.2
- Utip_9: 0.0864471
- tcroot: 0.141022

## Operating condition
- angle of attack (aoa, deg): 2.67232
- Mach number: 0.765063

The wing was simulated with a RANS solver (ADflow). Estimate the integrated aerodynamic coefficients.

Respond with a single JSON object of the form {"cl": <lift coefficient>, "cd": <drag coefficient>, "cm": <pitching moment coefficient>} and nothing else. Values must be finite numbers within physical ranges (cl in [-0.5, 1.2], cd in [0, 0.2], cm in [-0.5, 1.5]).
