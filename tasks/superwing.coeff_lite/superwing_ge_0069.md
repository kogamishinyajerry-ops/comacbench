You are given the parametric geometry of a transonic kinked wing and a single operating condition, and must predict its aerodynamic coefficients.

## Wing geometry parameters
- SA: 38.1514
- DA: 7.58457
- DA_kink: 5.60478
- AR: 10.1213
- TR: 0.350569
- kink: 0.416276
- rootadj: 0.559833
- rtcs_0: 0.655486
- rtcs_1: 0.93818
- rtcs_2: 0.976677
- cambers_0: 0.326591
- cambers_1: 0.954009
- cambers_2: 0.441766
- twists_0: -3.76989
- twists_1: -2.48404
- twists_2: -2.04413
- twists_3: -2.78609
- Uroot_0: 0.132999
- Uroot_1: 0.0783212
- Uroot_2: 0.201594
- Uroot_3: -0.025098
- Uroot_4: 0.410003
- Uroot_5: -0.211932
- Uroot_6: 0.601395
- Uroot_7: -0.0514321
- Uroot_8: 0.314445
- Uroot_9: 0.256282
- Utip_0: -0.123196
- Utip_1: -0.036571
- Utip_2: -0.214344
- Utip_3: 0.0559219
- Utip_4: -0.318988
- Utip_5: 0.0270009
- Utip_6: -0.194708
- Utip_7: -0.0773998
- Utip_8: 0.0615873
- Utip_9: 0.232409
- tcroot: 0.1531

## Operating condition
- angle of attack (aoa, deg): 9.42752
- Mach number: 0.802485

The wing was simulated with a RANS solver (ADflow). Estimate the integrated aerodynamic coefficients.

Respond with a single JSON object of the form {"cl": <lift coefficient>, "cd": <drag coefficient>, "cm": <pitching moment coefficient>} and nothing else. Values must be finite numbers within physical ranges (cl in [-0.5, 1.2], cd in [0, 0.2], cm in [-0.5, 1.5]).
