You are given the parametric geometry of a transonic kinked wing and a single operating condition, and must predict its aerodynamic coefficients.

## Wing geometry parameters
- SA: 39.1224
- DA: 5.99672
- DA_kink: 4.77927
- AR: 8.35501
- TR: 0.377204
- kink: 0.404142
- rootadj: 0.665319
- rtcs_0: 0.657909
- rtcs_1: 0.958361
- rtcs_2: 0.933842
- cambers_0: 0.454674
- cambers_1: 0.841997
- cambers_2: 0.513015
- twists_0: -3.96333
- twists_1: -2.89988
- twists_2: -2.19851
- twists_3: -1.07379
- Uroot_0: 0.147666
- Uroot_1: 0.127635
- Uroot_2: 0.169555
- Uroot_3: 0.152845
- Uroot_4: 0.158831
- Uroot_5: 0.247742
- Uroot_6: 0.0955082
- Uroot_7: 0.418807
- Uroot_8: 0.0557704
- Uroot_9: 0.46801
- Utip_0: -0.131193
- Utip_1: -0.0787554
- Utip_2: -0.205124
- Utip_3: 0.0269261
- Utip_4: -0.364186
- Utip_5: 0.18076
- Utip_6: -0.341003
- Utip_7: 0.0936294
- Utip_8: -0.108432
- Utip_9: 0.311948
- tcroot: 0.152933

## Operating condition
- angle of attack (aoa, deg): 5.40273
- Mach number: 0.846574

The wing was simulated with a RANS solver (ADflow). Estimate the integrated aerodynamic coefficients.

Respond with a single JSON object of the form {"cl": <lift coefficient>, "cd": <drag coefficient>, "cm": <pitching moment coefficient>} and nothing else. Values must be finite numbers within physical ranges (cl in [-0.5, 1.2], cd in [0, 0.2], cm in [-0.5, 1.5]).
