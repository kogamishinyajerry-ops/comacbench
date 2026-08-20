You are given the parametric geometry of a transonic kinked wing and a single operating condition, and must predict its aerodynamic coefficients.

## Wing geometry parameters
- SA: 35.3951
- DA: 9.92246
- DA_kink: 8.2184
- AR: 8.2598
- TR: 0.305175
- kink: 0.373156
- rootadj: 1.07866
- rtcs_0: 0.697619
- rtcs_1: 0.977446
- rtcs_2: 0.959575
- cambers_0: 0.378436
- cambers_1: 0.862545
- cambers_2: 0.45061
- twists_0: -3.82407
- twists_1: -2.63304
- twists_2: -2.13967
- twists_3: -2.10404
- Uroot_0: 0.198109
- Uroot_1: 0.0972822
- Uroot_2: 0.115289
- Uroot_3: 0.257983
- Uroot_4: 0.0305784
- Uroot_5: 0.0655192
- Uroot_6: 0.462479
- Uroot_7: -0.145366
- Uroot_8: 0.490901
- Uroot_9: 0.250759
- Utip_0: -0.128835
- Utip_1: -0.0245216
- Utip_2: -0.221152
- Utip_3: 0.0504517
- Utip_4: -0.317237
- Utip_5: 0.00764097
- Utip_6: -0.176208
- Utip_7: -0.0984093
- Utip_8: 0.0921986
- Utip_9: 0.206819
- tcroot: 0.140811

## Operating condition
- angle of attack (aoa, deg): 7.31686
- Mach number: 0.857817

The wing was simulated with a RANS solver (ADflow). Estimate the integrated aerodynamic coefficients.

Respond with a single JSON object of the form {"cl": <lift coefficient>, "cd": <drag coefficient>, "cm": <pitching moment coefficient>} and nothing else. Values must be finite numbers within physical ranges (cl in [-0.5, 1.2], cd in [0, 0.2], cm in [-0.5, 1.5]).
