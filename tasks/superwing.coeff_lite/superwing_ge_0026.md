You are given the parametric geometry of a transonic kinked wing and a single operating condition, and must predict its aerodynamic coefficients.

## Wing geometry parameters
- SA: 33.3523
- DA: 5.67921
- DA_kink: 2.62192
- AR: 9.26712
- TR: 0.230735
- kink: 0.380931
- rootadj: 0.43544
- rtcs_0: 0.678278
- rtcs_1: 0.918293
- rtcs_2: 0.989038
- cambers_0: 0.753616
- cambers_1: 0.712278
- cambers_2: 0.0498195
- twists_0: -3.53645
- twists_1: -3.91364
- twists_2: -1.8594
- twists_3: -1.64949
- Uroot_0: 0.209638
- Uroot_1: 0.0962067
- Uroot_2: 0.29367
- Uroot_3: -0.113743
- Uroot_4: 0.707423
- Uroot_5: -0.501342
- Uroot_6: 0.75381
- Uroot_7: -0.108422
- Uroot_8: 0.342842
- Uroot_9: 0.350613
- Utip_0: -0.150701
- Utip_1: -0.0445986
- Utip_2: -0.25683
- Utip_3: 0.0600238
- Utip_4: -0.371063
- Utip_5: 0.0209816
- Utip_6: -0.22434
- Utip_7: -0.102028
- Utip_8: 0.0855571
- Utip_9: 0.268947
- tcroot: 0.168218

## Operating condition
- angle of attack (aoa, deg): 9.50213
- Mach number: 0.795107

The wing was simulated with a RANS solver (ADflow). Estimate the integrated aerodynamic coefficients.

Respond with a single JSON object of the form {"cl": <lift coefficient>, "cd": <drag coefficient>, "cm": <pitching moment coefficient>} and nothing else. Values must be finite numbers within physical ranges (cl in [-0.5, 1.2], cd in [0, 0.2], cm in [-0.5, 1.5]).
