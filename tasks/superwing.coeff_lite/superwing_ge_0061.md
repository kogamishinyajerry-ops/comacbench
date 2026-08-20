You are given the parametric geometry of a transonic kinked wing and a single operating condition, and must predict its aerodynamic coefficients.

## Wing geometry parameters
- SA: 36.4996
- DA: 5.87671
- DA_kink: 0.616393
- AR: 8.10013
- TR: 0.309172
- kink: 0.364372
- rootadj: 0.580458
- rtcs_0: 0.646833
- rtcs_1: 0.973826
- rtcs_2: 0.987143
- cambers_0: 0.435447
- cambers_1: 0.837945
- cambers_2: 0.0728507
- twists_0: -2.94326
- twists_1: -2.06109
- twists_2: -1.78722
- twists_3: -2.64611
- Uroot_0: 0.152567
- Uroot_1: 0.0983209
- Uroot_2: 0.255352
- Uroot_3: 0.0653731
- Uroot_4: 0.350968
- Uroot_5: 0.0355687
- Uroot_6: 0.378549
- Uroot_7: 0.190043
- Uroot_8: 0.292862
- Uroot_9: 0.312128
- Utip_0: -0.163116
- Utip_1: -0.0486669
- Utip_2: -0.28027
- Utip_3: 0.0654769
- Utip_4: -0.404917
- Utip_5: 0.0230499
- Utip_6: -0.244805
- Utip_7: -0.112319
- Utip_8: 0.0933493
- Utip_9: 0.293186
- tcroot: 0.164471

## Operating condition
- angle of attack (aoa, deg): 5.6173
- Mach number: 0.761311

The wing was simulated with a RANS solver (ADflow). Estimate the integrated aerodynamic coefficients.

Respond with a single JSON object of the form {"cl": <lift coefficient>, "cd": <drag coefficient>, "cm": <pitching moment coefficient>} and nothing else. Values must be finite numbers within physical ranges (cl in [-0.5, 1.2], cd in [0, 0.2], cm in [-0.5, 1.5]).
