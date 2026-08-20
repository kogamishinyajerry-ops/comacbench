You are given the parametric geometry of a transonic kinked wing and a single operating condition, and must predict its aerodynamic coefficients.

## Wing geometry parameters
- SA: 36.8743
- DA: 7.10149
- DA_kink: 4.06827
- AR: 8.96193
- TR: 0.317489
- kink: 0.380157
- rootadj: 1.09877
- rtcs_0: 0.665133
- rtcs_1: 0.977746
- rtcs_2: 0.956242
- cambers_0: 0.483617
- cambers_1: 0.699235
- cambers_2: 0.462242
- twists_0: -2.45723
- twists_1: -2.38819
- twists_2: -2.68582
- twists_3: -2.19439
- Uroot_0: 0.249382
- Uroot_1: 0.0931186
- Uroot_2: 0.248641
- Uroot_3: 0.0789599
- Uroot_4: 0.232634
- Uroot_5: 0.212399
- Uroot_6: 0.144607
- Uroot_7: 0.274171
- Uroot_8: 0.279246
- Uroot_9: 0.384152
- Utip_0: -0.151295
- Utip_1: -0.0438336
- Utip_2: -0.257944
- Utip_3: 0.0438901
- Utip_4: -0.371977
- Utip_5: 0.0178202
- Utip_6: -0.237706
- Utip_7: -0.10236
- Utip_8: 0.0836347
- Utip_9: 0.278481
- tcroot: 0.168337

## Operating condition
- angle of attack (aoa, deg): 8.14489
- Mach number: 0.819144

The wing was simulated with a RANS solver (ADflow). Estimate the integrated aerodynamic coefficients.

Respond with a single JSON object of the form {"cl": <lift coefficient>, "cd": <drag coefficient>, "cm": <pitching moment coefficient>} and nothing else. Values must be finite numbers within physical ranges (cl in [-0.5, 1.2], cd in [0, 0.2], cm in [-0.5, 1.5]).
