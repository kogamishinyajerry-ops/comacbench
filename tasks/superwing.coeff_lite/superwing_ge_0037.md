You are given the parametric geometry of a transonic kinked wing and a single operating condition, and must predict its aerodynamic coefficients.

## Wing geometry parameters
- SA: 36.0933
- DA: 4.43195
- DA_kink: 2.11862
- AR: 10.4474
- TR: 0.307172
- kink: 0.392568
- rootadj: 0.749615
- rtcs_0: 0.669683
- rtcs_1: 0.949444
- rtcs_2: 0.924476
- cambers_0: 0.348259
- cambers_1: 0.957161
- cambers_2: 0.228035
- twists_0: -3.81045
- twists_1: -2.01875
- twists_2: -2.79116
- twists_3: -1.43034
- Uroot_0: 0.189457
- Uroot_1: 0.0695032
- Uroot_2: 0.176844
- Uroot_3: 0.11953
- Uroot_4: 0.188138
- Uroot_5: 0.0803927
- Uroot_6: 0.327043
- Uroot_7: 0.0411822
- Uroot_8: 0.433546
- Uroot_9: 0.303087
- Utip_0: -0.123498
- Utip_1: -0.0271564
- Utip_2: -0.212269
- Utip_3: 0.0534975
- Utip_4: -0.312624
- Utip_5: 0.0140699
- Utip_6: -0.185338
- Utip_7: -0.0869987
- Utip_8: 0.0712577
- Utip_9: 0.21827
- tcroot: 0.161089

## Operating condition
- angle of attack (aoa, deg): 4.3906
- Mach number: 0.872954

The wing was simulated with a RANS solver (ADflow). Estimate the integrated aerodynamic coefficients.

Respond with a single JSON object of the form {"cl": <lift coefficient>, "cd": <drag coefficient>, "cm": <pitching moment coefficient>} and nothing else. Values must be finite numbers within physical ranges (cl in [-0.5, 1.2], cd in [0, 0.2], cm in [-0.5, 1.5]).
