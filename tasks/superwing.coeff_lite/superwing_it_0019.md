You are given the parametric geometry of a transonic kinked wing and a single operating condition, and must predict its aerodynamic coefficients.

## Wing geometry parameters
- SA: 39.1896
- DA: 5.51008
- DA_kink: 2.54198
- AR: 10.3377
- TR: 0.3769
- kink: 0.361891
- rootadj: 0.641426
- rtcs_0: 0.691252
- rtcs_1: 0.933944
- rtcs_2: 0.997748
- cambers_0: 0.407617
- cambers_1: 0.60972
- cambers_2: 0.247859
- twists_0: -2.16969
- twists_1: -3.3771
- twists_2: -1.07749
- twists_3: -1.34523
- Uroot_0: 0.192099
- Uroot_1: 0.0775334
- Uroot_2: 0.161439
- Uroot_3: 0.124422
- Uroot_4: 0.170256
- Uroot_5: 0.082462
- Uroot_6: 0.315583
- Uroot_7: 0.0407845
- Uroot_8: 0.430886
- Uroot_9: 0.289707
- Utip_0: -0.123923
- Utip_1: -0.0366485
- Utip_2: -0.213093
- Utip_3: 0.0501684
- Utip_4: -0.3081
- Utip_5: 0.0171477
- Utip_6: -0.184481
- Utip_7: -0.0865076
- Utip_8: 0.0721835
- Utip_9: 0.222565
- tcroot: 0.157412

## Operating condition
- angle of attack (aoa, deg): 5.01658
- Mach number: 0.874538

The wing was simulated with a RANS solver (ADflow). Estimate the integrated aerodynamic coefficients.

Respond with a single JSON object of the form {"cl": <lift coefficient>, "cd": <drag coefficient>, "cm": <pitching moment coefficient>} and nothing else. Values must be finite numbers within physical ranges (cl in [-0.5, 1.2], cd in [0, 0.2], cm in [-0.5, 1.5]).
