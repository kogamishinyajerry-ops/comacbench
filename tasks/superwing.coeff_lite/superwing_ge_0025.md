You are given the parametric geometry of a transonic kinked wing and a single operating condition, and must predict its aerodynamic coefficients.

## Wing geometry parameters
- SA: 34.932
- DA: 9.12706
- DA_kink: 6.88023
- AR: 9.02816
- TR: 0.25611
- kink: 0.418756
- rootadj: 0.894952
- rtcs_0: 0.609873
- rtcs_1: 0.930216
- rtcs_2: 0.958513
- cambers_0: 0.333483
- cambers_1: 0.926936
- cambers_2: 0.781667
- twists_0: -3.20376
- twists_1: -3.35162
- twists_2: -1.4353
- twists_3: -2.01954
- Uroot_0: 0.130334
- Uroot_1: 0.124481
- Uroot_2: 0.200188
- Uroot_3: 0.0779785
- Uroot_4: 0.256713
- Uroot_5: 0.191226
- Uroot_6: 0.209704
- Uroot_7: 0.142991
- Uroot_8: 0.286575
- Uroot_9: 0.0629129
- Utip_0: -0.1494
- Utip_1: -0.0512874
- Utip_2: -0.227466
- Utip_3: -0.0336422
- Utip_4: -0.166803
- Utip_5: -0.1
- Utip_6: -0.1
- Utip_7: -0.2
- Utip_8: 0.2
- Utip_9: 0.100019
- tcroot: 0.152092

## Operating condition
- angle of attack (aoa, deg): 8.93838
- Mach number: 0.788295

The wing was simulated with a RANS solver (ADflow). Estimate the integrated aerodynamic coefficients.

Respond with a single JSON object of the form {"cl": <lift coefficient>, "cd": <drag coefficient>, "cm": <pitching moment coefficient>} and nothing else. Values must be finite numbers within physical ranges (cl in [-0.5, 1.2], cd in [0, 0.2], cm in [-0.5, 1.5]).
