You are given the parametric geometry of a transonic kinked wing and a single operating condition, and must predict its aerodynamic coefficients.

## Wing geometry parameters
- SA: 31.6939
- DA: 5.24043
- DA_kink: 5.70477
- AR: 8.45646
- TR: 0.38918
- kink: 0.375146
- rootadj: 0.27436
- rtcs_0: 0.687379
- rtcs_1: 0.93061
- rtcs_2: 0.993795
- cambers_0: 0.752783
- cambers_1: 0.851637
- cambers_2: 0.138415
- twists_0: -2.13792
- twists_1: -2.19248
- twists_2: -1.58287
- twists_3: -2.52758
- Uroot_0: 0.148998
- Uroot_1: 0.128418
- Uroot_2: 0.185974
- Uroot_3: -0.0826142
- Uroot_4: 0.601973
- Uroot_5: -0.26269
- Uroot_6: 0.44234
- Uroot_7: 0.225717
- Uroot_8: 0.269384
- Uroot_9: 0.131362
- Utip_0: -0.128024
- Utip_1: -0.137041
- Utip_2: -0.135829
- Utip_3: -0.163402
- Utip_4: -0.179802
- Utip_5: -0.153445
- Utip_6: -0.0990012
- Utip_7: -0.0610417
- Utip_8: -0.0515696
- Utip_9: 0.072057
- tcroot: 0.157396

## Operating condition
- angle of attack (aoa, deg): 5.74421
- Mach number: 0.855167

The wing was simulated with a RANS solver (ADflow). Estimate the integrated aerodynamic coefficients.

Respond with a single JSON object of the form {"cl": <lift coefficient>, "cd": <drag coefficient>, "cm": <pitching moment coefficient>} and nothing else. Values must be finite numbers within physical ranges (cl in [-0.5, 1.2], cd in [0, 0.2], cm in [-0.5, 1.5]).
