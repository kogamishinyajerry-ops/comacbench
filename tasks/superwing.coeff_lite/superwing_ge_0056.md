You are given the parametric geometry of a transonic kinked wing and a single operating condition, and must predict its aerodynamic coefficients.

## Wing geometry parameters
- SA: 32.1427
- DA: 4.71069
- DA_kink: 5.00508
- AR: 8.12183
- TR: 0.157409
- kink: 0.377778
- rootadj: 0.32067
- rtcs_0: 0.659504
- rtcs_1: 0.93545
- rtcs_2: 0.942769
- cambers_0: 0.404024
- cambers_1: 0.507053
- cambers_2: 0.554563
- twists_0: -2.53376
- twists_1: -3.98628
- twists_2: -2.77866
- twists_3: -1.55497
- Uroot_0: 0.148399
- Uroot_1: 0.0969362
- Uroot_2: 0.232617
- Uroot_3: 0.00399104
- Uroot_4: 0.35405
- Uroot_5: -0.013727
- Uroot_6: 0.372204
- Uroot_7: 0.0955716
- Uroot_8: 0.28132
- Uroot_9: 0.296835
- Utip_0: -0.137737
- Utip_1: -0.0410595
- Utip_2: -0.236449
- Utip_3: 0.0552607
- Utip_4: -0.342437
- Utip_5: 0.0194488
- Utip_6: -0.206543
- Utip_7: -0.0947622
- Utip_8: 0.0787678
- Utip_9: 0.245846
- tcroot: 0.150542

## Operating condition
- angle of attack (aoa, deg): 9.71953
- Mach number: 0.81449

The wing was simulated with a RANS solver (ADflow). Estimate the integrated aerodynamic coefficients.

Respond with a single JSON object of the form {"cl": <lift coefficient>, "cd": <drag coefficient>, "cm": <pitching moment coefficient>} and nothing else. Values must be finite numbers within physical ranges (cl in [-0.5, 1.2], cd in [0, 0.2], cm in [-0.5, 1.5]).
