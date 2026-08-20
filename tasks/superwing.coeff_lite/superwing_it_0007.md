You are given the parametric geometry of a transonic kinked wing and a single operating condition, and must predict its aerodynamic coefficients.

## Wing geometry parameters
- SA: 38.1153
- DA: 5.10732
- DA_kink: 3.91678
- AR: 9.61799
- TR: 0.376288
- kink: 0.367349
- rootadj: 0.582668
- rtcs_0: 0.651569
- rtcs_1: 0.926835
- rtcs_2: 0.997637
- cambers_0: 0.51924
- cambers_1: 0.66013
- cambers_2: 0.338798
- twists_0: -2.40998
- twists_1: -2.32981
- twists_2: -1.98402
- twists_3: -1.7509
- Uroot_0: 0.120451
- Uroot_1: 0.136754
- Uroot_2: 0.198511
- Uroot_3: 0.0812663
- Uroot_4: 0.264918
- Uroot_5: 0.186589
- Uroot_6: 0.172316
- Uroot_7: 0.141933
- Uroot_8: 0.29695
- Uroot_9: 0.0576985
- Utip_0: -0.149307
- Utip_1: -0.0493713
- Utip_2: -0.226511
- Utip_3: -0.036567
- Utip_4: -0.161112
- Utip_5: -0.099998
- Utip_6: -0.100054
- Utip_7: -0.196618
- Utip_8: 0.2
- Utip_9: 0.0976857
- tcroot: 0.140498

## Operating condition
- angle of attack (aoa, deg): 8.8224
- Mach number: 0.797882

The wing was simulated with a RANS solver (ADflow). Estimate the integrated aerodynamic coefficients.

Respond with a single JSON object of the form {"cl": <lift coefficient>, "cd": <drag coefficient>, "cm": <pitching moment coefficient>} and nothing else. Values must be finite numbers within physical ranges (cl in [-0.5, 1.2], cd in [0, 0.2], cm in [-0.5, 1.5]).
