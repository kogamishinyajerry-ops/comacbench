You are given the parametric geometry of a transonic kinked wing and a single operating condition, and must predict its aerodynamic coefficients.

## Wing geometry parameters
- SA: 31.0014
- DA: 5.28431
- DA_kink: 2.9456
- AR: 10.2449
- TR: 0.324761
- kink: 0.387428
- rootadj: 0.569217
- rtcs_0: 0.614412
- rtcs_1: 0.95355
- rtcs_2: 0.975531
- cambers_0: 0.520363
- cambers_1: 0.85453
- cambers_2: 0.762159
- twists_0: -3.52215
- twists_1: -3.89812
- twists_2: -2.94186
- twists_3: -2.03973
- Uroot_0: 0.171637
- Uroot_1: 0.0861771
- Uroot_2: 0.257674
- Uroot_3: -0.0204321
- Uroot_4: 0.38182
- Uroot_5: -0.0340221
- Uroot_6: 0.349268
- Uroot_7: 0.11506
- Uroot_8: 0.263663
- Uroot_9: 0.276826
- Utip_0: -0.138256
- Utip_1: -0.0409043
- Utip_2: -0.235555
- Utip_3: 0.0550518
- Utip_4: -0.340327
- Utip_5: 0.0193753
- Utip_6: -0.205757
- Utip_7: -0.094404
- Utip_8: 0.0782689
- Utip_9: 0.247057
- tcroot: 0.157983

## Operating condition
- angle of attack (aoa, deg): 4.34159
- Mach number: 0.804414

The wing was simulated with a RANS solver (ADflow). Estimate the integrated aerodynamic coefficients.

Respond with a single JSON object of the form {"cl": <lift coefficient>, "cd": <drag coefficient>, "cm": <pitching moment coefficient>} and nothing else. Values must be finite numbers within physical ranges (cl in [-0.5, 1.2], cd in [0, 0.2], cm in [-0.5, 1.5]).
