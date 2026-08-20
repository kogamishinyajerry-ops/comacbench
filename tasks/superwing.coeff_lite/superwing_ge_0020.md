You are given the parametric geometry of a transonic kinked wing and a single operating condition, and must predict its aerodynamic coefficients.

## Wing geometry parameters
- SA: 39.7868
- DA: 4.869
- DA_kink: 3.52111
- AR: 10.6784
- TR: 0.34244
- kink: 0.398587
- rootadj: 0.694371
- rtcs_0: 0.664729
- rtcs_1: 0.945794
- rtcs_2: 0.992273
- cambers_0: 0.55146
- cambers_1: 0.501534
- cambers_2: 0.408695
- twists_0: -2.79318
- twists_1: -3.22785
- twists_2: -1.09337
- twists_3: -1.74016
- Uroot_0: 0.193149
- Uroot_1: 0.110624
- Uroot_2: 0.112796
- Uroot_3: 0.21777
- Uroot_4: 0.102593
- Uroot_5: 0.047516
- Uroot_6: 0.452057
- Uroot_7: -0.0954074
- Uroot_8: 0.441245
- Uroot_9: 0.270436
- Utip_0: -0.124876
- Utip_1: -0.0373433
- Utip_2: -0.214456
- Utip_3: 0.0502589
- Utip_4: -0.312206
- Utip_5: 0.0187904
- Utip_6: -0.187844
- Utip_7: -0.0861854
- Utip_8: 0.0716387
- Utip_9: 0.224968
- tcroot: 0.154967

## Operating condition
- angle of attack (aoa, deg): 4.6551
- Mach number: 0.886887

The wing was simulated with a RANS solver (ADflow). Estimate the integrated aerodynamic coefficients.

Respond with a single JSON object of the form {"cl": <lift coefficient>, "cd": <drag coefficient>, "cm": <pitching moment coefficient>} and nothing else. Values must be finite numbers within physical ranges (cl in [-0.5, 1.2], cd in [0, 0.2], cm in [-0.5, 1.5]).
