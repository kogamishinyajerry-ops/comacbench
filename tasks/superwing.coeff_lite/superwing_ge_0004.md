You are given the parametric geometry of a transonic kinked wing and a single operating condition, and must predict its aerodynamic coefficients.

## Wing geometry parameters
- SA: 28.2262
- DA: 5.21103
- DA_kink: 5.56466
- AR: 8.89948
- TR: 0.365263
- kink: 0.386866
- rootadj: 0.250181
- rtcs_0: 0.610475
- rtcs_1: 0.957345
- rtcs_2: 0.950579
- cambers_0: 0.448952
- cambers_1: 0.516653
- cambers_2: 0.289744
- twists_0: -3.49316
- twists_1: -3.12615
- twists_2: -2.4504
- twists_3: -1.15314
- Uroot_0: 0.140892
- Uroot_1: 0.0838837
- Uroot_2: 0.185765
- Uroot_3: 0.0340366
- Uroot_4: 0.355629
- Uroot_5: -0.12892
- Uroot_6: 0.488996
- Uroot_7: -0.00583788
- Uroot_8: 0.273177
- Uroot_9: 0.24169
- Utip_0: -0.11487
- Utip_1: -0.0345661
- Utip_2: -0.220701
- Utip_3: 0.0493321
- Utip_4: -0.299959
- Utip_5: 0.0147125
- Utip_6: -0.188546
- Utip_7: -0.0710045
- Utip_8: 0.0823614
- Utip_9: 0.204876
- tcroot: 0.149307

## Operating condition
- angle of attack (aoa, deg): 8.11403
- Mach number: 0.864034

The wing was simulated with a RANS solver (ADflow). Estimate the integrated aerodynamic coefficients.

Respond with a single JSON object of the form {"cl": <lift coefficient>, "cd": <drag coefficient>, "cm": <pitching moment coefficient>} and nothing else. Values must be finite numbers within physical ranges (cl in [-0.5, 1.2], cd in [0, 0.2], cm in [-0.5, 1.5]).
