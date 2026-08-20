You are given the parametric geometry of a transonic kinked wing and a single operating condition, and must predict its aerodynamic coefficients.

## Wing geometry parameters
- SA: 38.3352
- DA: 5.16964
- DA_kink: 1.79151
- AR: 10.5266
- TR: 0.150619
- kink: 0.407562
- rootadj: 0.404139
- rtcs_0: 0.688558
- rtcs_1: 0.950703
- rtcs_2: 0.932026
- cambers_0: 0.734873
- cambers_1: 0.627894
- cambers_2: 0.456805
- twists_0: -3.19467
- twists_1: -2.2386
- twists_2: -2.01507
- twists_3: -1.15322
- Uroot_0: 0.133826
- Uroot_1: 0.0797324
- Uroot_2: 0.211544
- Uroot_3: -0.0421921
- Uroot_4: 0.446829
- Uroot_5: -0.252403
- Uroot_6: 0.633464
- Uroot_7: -0.0632086
- Uroot_8: 0.329135
- Uroot_9: 0.250665
- Utip_0: -0.125118
- Utip_1: -0.0373206
- Utip_2: -0.214939
- Utip_3: 0.0502374
- Utip_4: -0.310555
- Utip_5: 0.0176735
- Utip_6: -0.187761
- Utip_7: -0.0861545
- Utip_8: 0.0716067
- Utip_9: 0.224868
- tcroot: 0.140093

## Operating condition
- angle of attack (aoa, deg): 5.34817
- Mach number: 0.864307

The wing was simulated with a RANS solver (ADflow). Estimate the integrated aerodynamic coefficients.

Respond with a single JSON object of the form {"cl": <lift coefficient>, "cd": <drag coefficient>, "cm": <pitching moment coefficient>} and nothing else. Values must be finite numbers within physical ranges (cl in [-0.5, 1.2], cd in [0, 0.2], cm in [-0.5, 1.5]).
