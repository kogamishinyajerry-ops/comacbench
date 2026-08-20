You are given the parametric geometry of a transonic kinked wing and a single operating condition, and must predict its aerodynamic coefficients.

## Wing geometry parameters
- SA: 35.3214
- DA: 5.44076
- DA_kink: 3.65434
- AR: 8.41882
- TR: 0.287167
- kink: 0.396019
- rootadj: 0.369055
- rtcs_0: 0.654037
- rtcs_1: 0.969332
- rtcs_2: 0.92411
- cambers_0: 0.350848
- cambers_1: 0.603616
- cambers_2: 0.0796385
- twists_0: -2.82428
- twists_1: -3.01228
- twists_2: -1.0254
- twists_3: -1.83755
- Uroot_0: 0.15748
- Uroot_1: 0.0973148
- Uroot_2: 0.159828
- Uroot_3: 0.108334
- Uroot_4: 0.17094
- Uroot_5: 0.138698
- Uroot_6: 0.164952
- Uroot_7: 0.195453
- Uroot_8: 0.171013
- Uroot_9: 0.250707
- Utip_0: -0.122399
- Utip_1: -0.0359493
- Utip_2: -0.210183
- Utip_3: 0.0490813
- Utip_4: -0.303442
- Utip_5: 0.0169503
- Utip_6: -0.183281
- Utip_7: -0.082582
- Utip_8: 0.069972
- Utip_9: 0.219722
- tcroot: 0.147809

## Operating condition
- angle of attack (aoa, deg): 4.56411
- Mach number: 0.854626

The wing was simulated with a RANS solver (ADflow). Estimate the integrated aerodynamic coefficients.

Respond with a single JSON object of the form {"cl": <lift coefficient>, "cd": <drag coefficient>, "cm": <pitching moment coefficient>} and nothing else. Values must be finite numbers within physical ranges (cl in [-0.5, 1.2], cd in [0, 0.2], cm in [-0.5, 1.5]).
