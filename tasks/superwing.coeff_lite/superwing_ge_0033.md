You are given the parametric geometry of a transonic kinked wing and a single operating condition, and must predict its aerodynamic coefficients.

## Wing geometry parameters
- SA: 35.7598
- DA: 4.85593
- DA_kink: 1.62937
- AR: 8.63161
- TR: 0.292477
- kink: 0.378159
- rootadj: 1.0355
- rtcs_0: 0.640461
- rtcs_1: 0.953076
- rtcs_2: 0.930797
- cambers_0: 0.430412
- cambers_1: 0.943058
- cambers_2: 0.214886
- twists_0: -2.16419
- twists_1: -2.06051
- twists_2: -2.28761
- twists_3: -2.538
- Uroot_0: 0.194064
- Uroot_1: 0.112057
- Uroot_2: 0.277057
- Uroot_3: -0.0600495
- Uroot_4: 0.56076
- Uroot_5: -0.280893
- Uroot_6: 0.639033
- Uroot_7: -0.175289
- Uroot_8: 0.240582
- Uroot_9: 0.338289
- Utip_0: -0.149087
- Utip_1: -0.0447922
- Utip_2: -0.257944
- Utip_3: 0.059651
- Utip_4: -0.372674
- Utip_5: 0.0212169
- Utip_6: -0.225427
- Utip_7: -0.103377
- Utip_8: 0.0859285
- Utip_9: 0.269842
- tcroot: 0.153964

## Operating condition
- angle of attack (aoa, deg): 4.65149
- Mach number: 0.894105

The wing was simulated with a RANS solver (ADflow). Estimate the integrated aerodynamic coefficients.

Respond with a single JSON object of the form {"cl": <lift coefficient>, "cd": <drag coefficient>, "cm": <pitching moment coefficient>} and nothing else. Values must be finite numbers within physical ranges (cl in [-0.5, 1.2], cd in [0, 0.2], cm in [-0.5, 1.5]).
