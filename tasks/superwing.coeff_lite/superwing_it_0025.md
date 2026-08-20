You are given the parametric geometry of a transonic kinked wing and a single operating condition, and must predict its aerodynamic coefficients.

## Wing geometry parameters
- SA: 29.9885
- DA: 5.12212
- DA_kink: 3.88732
- AR: 9.76082
- TR: 0.297365
- kink: 0.377886
- rootadj: 0.343118
- rtcs_0: 0.695857
- rtcs_1: 0.93351
- rtcs_2: 0.92964
- cambers_0: 0.550305
- cambers_1: 0.985099
- cambers_2: 0.649673
- twists_0: -2.38502
- twists_1: -2.19442
- twists_2: -2.2834
- twists_3: -2.31406
- Uroot_0: 0.132023
- Uroot_1: 0.0798305
- Uroot_2: 0.212777
- Uroot_3: -0.045647
- Uroot_4: 0.450789
- Uroot_5: -0.254399
- Uroot_6: 0.636018
- Uroot_7: -0.0647877
- Uroot_8: 0.332563
- Uroot_9: 0.250306
- Utip_0: -0.12527
- Utip_1: -0.0373889
- Utip_2: -0.215086
- Utip_3: 0.0498969
- Utip_4: -0.31008
- Utip_5: 0.0170021
- Utip_6: -0.187282
- Utip_7: -0.0868039
- Utip_8: 0.0723583
- Utip_9: 0.22443
- tcroot: 0.150857

## Operating condition
- angle of attack (aoa, deg): 8.82926
- Mach number: 0.833444

The wing was simulated with a RANS solver (ADflow). Estimate the integrated aerodynamic coefficients.

Respond with a single JSON object of the form {"cl": <lift coefficient>, "cd": <drag coefficient>, "cm": <pitching moment coefficient>} and nothing else. Values must be finite numbers within physical ranges (cl in [-0.5, 1.2], cd in [0, 0.2], cm in [-0.5, 1.5]).
