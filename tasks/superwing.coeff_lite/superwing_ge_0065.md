You are given the parametric geometry of a transonic kinked wing and a single operating condition, and must predict its aerodynamic coefficients.

## Wing geometry parameters
- SA: 36.8331
- DA: 4.47104
- DA_kink: 0.711737
- AR: 10.1024
- TR: 0.308936
- kink: 0.416224
- rootadj: 0.41975
- rtcs_0: 0.695705
- rtcs_1: 0.962707
- rtcs_2: 0.920874
- cambers_0: 0.586496
- cambers_1: 0.57688
- cambers_2: 0.798431
- twists_0: -2.55299
- twists_1: -2.3975
- twists_2: -2.78431
- twists_3: -1.83955
- Uroot_0: 0.157776
- Uroot_1: 0.0730059
- Uroot_2: 0.329088
- Uroot_3: -0.240569
- Uroot_4: 0.830081
- Uroot_5: -0.645935
- Uroot_6: 0.910818
- Uroot_7: -0.234253
- Uroot_8: 0.260155
- Uroot_9: 0.239185
- Utip_0: -0.137627
- Utip_1: -0.0410595
- Utip_2: -0.236434
- Utip_3: 0.0552607
- Utip_4: -0.341618
- Utip_5: 0.0194488
- Utip_6: -0.206829
- Utip_7: -0.0947622
- Utip_8: 0.0787678
- Utip_9: 0.247214
- tcroot: 0.154932

## Operating condition
- angle of attack (aoa, deg): 7.15746
- Mach number: 0.777806

The wing was simulated with a RANS solver (ADflow). Estimate the integrated aerodynamic coefficients.

Respond with a single JSON object of the form {"cl": <lift coefficient>, "cd": <drag coefficient>, "cm": <pitching moment coefficient>} and nothing else. Values must be finite numbers within physical ranges (cl in [-0.5, 1.2], cd in [0, 0.2], cm in [-0.5, 1.5]).
