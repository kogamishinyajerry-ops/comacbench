You are given the parametric geometry of a transonic kinked wing and a single operating condition, and must predict its aerodynamic coefficients.

## Wing geometry parameters
- SA: 36.7612
- DA: 8.42344
- DA_kink: 3.21287
- AR: 10.9424
- TR: 0.319939
- kink: 0.364894
- rootadj: 0.62581
- rtcs_0: 0.601865
- rtcs_1: 0.962482
- rtcs_2: 0.964283
- cambers_0: 0.33966
- cambers_1: 0.634973
- cambers_2: 0.104402
- twists_0: -2.55301
- twists_1: -2.18697
- twists_2: -2.39692
- twists_3: -2.48353
- Uroot_0: 0.183292
- Uroot_1: 0.0788907
- Uroot_2: 0.325083
- Uroot_3: -0.0800375
- Uroot_4: 0.444346
- Uroot_5: -0.0488937
- Uroot_6: 0.40118
- Uroot_7: 0.136678
- Uroot_8: 0.233113
- Uroot_9: 0.254518
- Utip_0: -0.151481
- Utip_1: -0.0451993
- Utip_2: -0.263228
- Utip_3: 0.0605576
- Utip_4: -0.368342
- Utip_5: 0.0225997
- Utip_6: -0.226223
- Utip_7: -0.103377
- Utip_8: 0.0859285
- Utip_9: 0.269842
- tcroot: 0.157903

## Operating condition
- angle of attack (aoa, deg): 4.31988
- Mach number: 0.897742

The wing was simulated with a RANS solver (ADflow). Estimate the integrated aerodynamic coefficients.

Respond with a single JSON object of the form {"cl": <lift coefficient>, "cd": <drag coefficient>, "cm": <pitching moment coefficient>} and nothing else. Values must be finite numbers within physical ranges (cl in [-0.5, 1.2], cd in [0, 0.2], cm in [-0.5, 1.5]).
