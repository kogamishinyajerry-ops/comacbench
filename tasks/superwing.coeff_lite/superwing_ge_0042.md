You are given the parametric geometry of a transonic kinked wing and a single operating condition, and must predict its aerodynamic coefficients.

## Wing geometry parameters
- SA: 33.4263
- DA: 5.36334
- DA_kink: 1.50549
- AR: 9.42299
- TR: 0.22329
- kink: 0.383136
- rootadj: 0.210689
- rtcs_0: 0.645262
- rtcs_1: 0.911848
- rtcs_2: 0.939752
- cambers_0: 0.409472
- cambers_1: 0.797097
- cambers_2: 0.493502
- twists_0: -2.83009
- twists_1: -3.81766
- twists_2: -2.87814
- twists_3: -2.79884
- Uroot_0: 0.139026
- Uroot_1: 0.124204
- Uroot_2: 0.20271
- Uroot_3: 0.0987919
- Uroot_4: 0.236141
- Uroot_5: 0.244102
- Uroot_6: 0.101901
- Uroot_7: 0.1166
- Uroot_8: 0.209934
- Uroot_9: 0.161403
- Utip_0: -0.149756
- Utip_1: -0.0478537
- Utip_2: -0.243571
- Utip_3: 0.0161109
- Utip_4: -0.27574
- Utip_5: -0.0998649
- Utip_6: -0.100836
- Utip_7: -0.19986
- Utip_8: 0.2
- Utip_9: 0.182382
- tcroot: 0.151173

## Operating condition
- angle of attack (aoa, deg): 5.65943
- Mach number: 0.752757

The wing was simulated with a RANS solver (ADflow). Estimate the integrated aerodynamic coefficients.

Respond with a single JSON object of the form {"cl": <lift coefficient>, "cd": <drag coefficient>, "cm": <pitching moment coefficient>} and nothing else. Values must be finite numbers within physical ranges (cl in [-0.5, 1.2], cd in [0, 0.2], cm in [-0.5, 1.5]).
