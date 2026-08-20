You are given the parametric geometry of a transonic kinked wing and a single operating condition, and must predict its aerodynamic coefficients.

## Wing geometry parameters
- SA: 33.7864
- DA: 5.3006
- DA_kink: 0.544428
- AR: 8.77967
- TR: 0.247579
- kink: 0.401865
- rootadj: 0.321359
- rtcs_0: 0.60639
- rtcs_1: 0.93653
- rtcs_2: 0.995657
- cambers_0: 0.41572
- cambers_1: 0.779643
- cambers_2: 0.0666936
- twists_0: -2.26227
- twists_1: -3.19536
- twists_2: -2.4645
- twists_3: -2.92341
- Uroot_0: 0.146216
- Uroot_1: 0.107494
- Uroot_2: 0.23635
- Uroot_3: 0.0498055
- Uroot_4: 0.21881
- Uroot_5: 0.285269
- Uroot_6: 0.0824736
- Uroot_7: 0.157409
- Uroot_8: 0.217401
- Uroot_9: 0.172133
- Utip_0: -0.136999
- Utip_1: -0.0489785
- Utip_2: -0.249467
- Utip_3: -0.00235747
- Utip_4: -0.174268
- Utip_5: -0.0938341
- Utip_6: -0.106576
- Utip_7: -0.201383
- Utip_8: 0.2
- Utip_9: 0.183915
- tcroot: 0.141546

## Operating condition
- angle of attack (aoa, deg): 5.57261
- Mach number: 0.845933

The wing was simulated with a RANS solver (ADflow). Estimate the integrated aerodynamic coefficients.

Respond with a single JSON object of the form {"cl": <lift coefficient>, "cd": <drag coefficient>, "cm": <pitching moment coefficient>} and nothing else. Values must be finite numbers within physical ranges (cl in [-0.5, 1.2], cd in [0, 0.2], cm in [-0.5, 1.5]).
