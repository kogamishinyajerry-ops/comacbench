You are given the parametric geometry of a transonic kinked wing and a single operating condition, and must predict its aerodynamic coefficients.

## Wing geometry parameters
- SA: 39.4082
- DA: 4.76614
- DA_kink: 2.1626
- AR: 10.5785
- TR: 0.310464
- kink: 0.418717
- rootadj: 0.801032
- rtcs_0: 0.671327
- rtcs_1: 0.946413
- rtcs_2: 0.965039
- cambers_0: 0.301789
- cambers_1: 0.711262
- cambers_2: 0.0557936
- twists_0: -3.22947
- twists_1: -3.0496
- twists_2: -2.44083
- twists_3: -1.46062
- Uroot_0: 0.13623
- Uroot_1: 0.0884954
- Uroot_2: 0.297382
- Uroot_3: -0.000524158
- Uroot_4: 0.399687
- Uroot_5: -0.0194966
- Uroot_6: 0.449548
- Uroot_7: 0.108676
- Uroot_8: 0.263347
- Uroot_9: 0.297015
- Utip_0: -0.162651
- Utip_1: -0.036692
- Utip_2: -0.27944
- Utip_3: 0.0596013
- Utip_4: -0.397655
- Utip_5: 0.0250897
- Utip_6: -0.234747
- Utip_7: -0.111005
- Utip_8: 0.0839301
- Utip_9: 0.292329
- tcroot: 0.169143

## Operating condition
- angle of attack (aoa, deg): 3.10699
- Mach number: 0.754675

The wing was simulated with a RANS solver (ADflow). Estimate the integrated aerodynamic coefficients.

Respond with a single JSON object of the form {"cl": <lift coefficient>, "cd": <drag coefficient>, "cm": <pitching moment coefficient>} and nothing else. Values must be finite numbers within physical ranges (cl in [-0.5, 1.2], cd in [0, 0.2], cm in [-0.5, 1.5]).
