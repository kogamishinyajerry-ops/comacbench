You are given the parametric geometry of a transonic kinked wing and a single operating condition, and must predict its aerodynamic coefficients.

## Wing geometry parameters
- SA: 32.4477
- DA: 4.23059
- DA_kink: 5.07678
- AR: 8.15067
- TR: 0.321997
- kink: 0.369205
- rootadj: 0.401284
- rtcs_0: 0.607312
- rtcs_1: 0.902044
- rtcs_2: 0.954408
- cambers_0: 0.607855
- cambers_1: 0.805103
- cambers_2: 0.546614
- twists_0: -3.47784
- twists_1: -2.85175
- twists_2: -1.51377
- twists_3: -2.2455
- Uroot_0: 0.196553
- Uroot_1: 0.114248
- Uroot_2: 0.128473
- Uroot_3: 0.210438
- Uroot_4: 0.104214
- Uroot_5: 0.0482396
- Uroot_6: 0.466392
- Uroot_7: -0.0893745
- Uroot_8: 0.459717
- Uroot_9: 0.270903
- Utip_0: -0.138499
- Utip_1: -0.0363513
- Utip_2: -0.20865
- Utip_3: 0.0538432
- Utip_4: -0.309803
- Utip_5: 0.00760022
- Utip_6: -0.182261
- Utip_7: -0.0748701
- Utip_8: 0.0670954
- Utip_9: 0.245311
- tcroot: 0.15506

## Operating condition
- angle of attack (aoa, deg): 7.50817
- Mach number: 0.820215

The wing was simulated with a RANS solver (ADflow). Estimate the integrated aerodynamic coefficients.

Respond with a single JSON object of the form {"cl": <lift coefficient>, "cd": <drag coefficient>, "cm": <pitching moment coefficient>} and nothing else. Values must be finite numbers within physical ranges (cl in [-0.5, 1.2], cd in [0, 0.2], cm in [-0.5, 1.5]).
