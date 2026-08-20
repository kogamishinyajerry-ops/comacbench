You are given the parametric geometry of a transonic kinked wing and a single operating condition, and must predict its aerodynamic coefficients.

## Wing geometry parameters
- SA: 31.7712
- DA: 4.75476
- DA_kink: 2.83706
- AR: 8.53052
- TR: 0.247375
- kink: 0.393233
- rootadj: 0.519494
- rtcs_0: 0.629995
- rtcs_1: 0.932067
- rtcs_2: 0.997489
- cambers_0: 0.695126
- cambers_1: 0.538967
- cambers_2: 0.235757
- twists_0: -3.77038
- twists_1: -3.14525
- twists_2: -1.40839
- twists_3: -2.1133
- Uroot_0: 0.13108
- Uroot_1: 0.0830806
- Uroot_2: 0.205351
- Uroot_3: -0.046407
- Uroot_4: 0.437571
- Uroot_5: -0.24857
- Uroot_6: 0.648343
- Uroot_7: -0.0421186
- Uroot_8: 0.338952
- Uroot_9: 0.281151
- Utip_0: -0.123593
- Utip_1: -0.0357154
- Utip_2: -0.218013
- Utip_3: 0.0642213
- Utip_4: -0.310767
- Utip_5: 0.0166235
- Utip_6: -0.203076
- Utip_7: -0.0667499
- Utip_8: 0.040577
- Utip_9: 0.246974
- tcroot: 0.151556

## Operating condition
- angle of attack (aoa, deg): 11.5365
- Mach number: 0.79907

The wing was simulated with a RANS solver (ADflow). Estimate the integrated aerodynamic coefficients.

Respond with a single JSON object of the form {"cl": <lift coefficient>, "cd": <drag coefficient>, "cm": <pitching moment coefficient>} and nothing else. Values must be finite numbers within physical ranges (cl in [-0.5, 1.2], cd in [0, 0.2], cm in [-0.5, 1.5]).
