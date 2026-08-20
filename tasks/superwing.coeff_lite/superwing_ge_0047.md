You are given the parametric geometry of a transonic kinked wing and a single operating condition, and must predict its aerodynamic coefficients.

## Wing geometry parameters
- SA: 39.3693
- DA: 4.01165
- DA_kink: 2.95811
- AR: 10.3018
- TR: 0.167621
- kink: 0.375277
- rootadj: 0.529331
- rtcs_0: 0.649351
- rtcs_1: 0.914359
- rtcs_2: 0.94341
- cambers_0: 0.556282
- cambers_1: 0.965496
- cambers_2: 0.452285
- twists_0: -2.15034
- twists_1: -3.58916
- twists_2: -1.88742
- twists_3: -1.30487
- Uroot_0: 0.129084
- Uroot_1: 0.148327
- Uroot_2: 0.193246
- Uroot_3: 0.126096
- Uroot_4: 0.19464
- Uroot_5: 0.333582
- Uroot_6: 0.0706468
- Uroot_7: 0.221968
- Uroot_8: 0.291599
- Uroot_9: -0.041925
- Utip_0: -0.160744
- Utip_1: -0.0579594
- Utip_2: -0.229704
- Utip_3: -0.0829786
- Utip_4: -0.0785848
- Utip_5: -0.152627
- Utip_6: -0.0597671
- Utip_7: -0.250491
- Utip_8: 0.2
- Utip_9: 0.0243434
- tcroot: 0.146619

## Operating condition
- angle of attack (aoa, deg): 3.89745
- Mach number: 0.777332

The wing was simulated with a RANS solver (ADflow). Estimate the integrated aerodynamic coefficients.

Respond with a single JSON object of the form {"cl": <lift coefficient>, "cd": <drag coefficient>, "cm": <pitching moment coefficient>} and nothing else. Values must be finite numbers within physical ranges (cl in [-0.5, 1.2], cd in [0, 0.2], cm in [-0.5, 1.5]).
