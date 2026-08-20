You are given the parametric geometry of a transonic kinked wing and a single operating condition, and must predict its aerodynamic coefficients.

## Wing geometry parameters
- SA: 25.4388
- DA: 5.45998
- DA_kink: 1.27749
- AR: 9.1192
- TR: 0.298603
- kink: 0.39997
- rootadj: 0.222605
- rtcs_0: 0.619845
- rtcs_1: 0.955285
- rtcs_2: 0.995217
- cambers_0: 0.437571
- cambers_1: 0.796919
- cambers_2: 0.196427
- twists_0: -2.39294
- twists_1: -3.04049
- twists_2: -2.96722
- twists_3: -1.9798
- Uroot_0: 0.202398
- Uroot_1: 0.0707864
- Uroot_2: 0.194463
- Uroot_3: 0.0734807
- Uroot_4: 0.176621
- Uroot_5: 0.0621797
- Uroot_6: 0.350016
- Uroot_7: 0.00176461
- Uroot_8: 0.472745
- Uroot_9: 0.299983
- Utip_0: -0.125161
- Utip_1: -0.038645
- Utip_2: -0.209483
- Utip_3: 0.0537762
- Utip_4: -0.31785
- Utip_5: 0.0176807
- Utip_6: -0.180388
- Utip_7: -0.0905511
- Utip_8: 0.071607
- Utip_9: 0.228732
- tcroot: 0.157052

## Operating condition
- angle of attack (aoa, deg): 2.48557
- Mach number: 0.866727

The wing was simulated with a RANS solver (ADflow). Estimate the integrated aerodynamic coefficients.

Respond with a single JSON object of the form {"cl": <lift coefficient>, "cd": <drag coefficient>, "cm": <pitching moment coefficient>} and nothing else. Values must be finite numbers within physical ranges (cl in [-0.5, 1.2], cd in [0, 0.2], cm in [-0.5, 1.5]).
