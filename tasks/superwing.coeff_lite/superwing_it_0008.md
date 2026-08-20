You are given the parametric geometry of a transonic kinked wing and a single operating condition, and must predict its aerodynamic coefficients.

## Wing geometry parameters
- SA: 39.4828
- DA: 6.79057
- DA_kink: 4.31399
- AR: 8.21789
- TR: 0.276194
- kink: 0.407676
- rootadj: 0.639841
- rtcs_0: 0.608238
- rtcs_1: 0.969332
- rtcs_2: 0.963135
- cambers_0: 0.572063
- cambers_1: 0.928172
- cambers_2: 0.585006
- twists_0: -3.03522
- twists_1: -3.17806
- twists_2: -2.39833
- twists_3: -1.36584
- Uroot_0: 0.204689
- Uroot_1: 0.0934361
- Uroot_2: 0.188365
- Uroot_3: 0.0794729
- Uroot_4: 0.20705
- Uroot_5: 0.0627789
- Uroot_6: 0.354841
- Uroot_7: 0.00139853
- Uroot_8: 0.486086
- Uroot_9: 0.310279
- Utip_0: -0.126399
- Utip_1: -0.0363531
- Utip_2: -0.217674
- Utip_3: 0.0523334
- Utip_4: -0.301427
- Utip_5: 0.0167018
- Utip_6: -0.187983
- Utip_7: -0.086443
- Utip_8: 0.0718751
- Utip_9: 0.226709
- tcroot: 0.163565

## Operating condition
- angle of attack (aoa, deg): 7.09056
- Mach number: 0.856147

The wing was simulated with a RANS solver (ADflow). Estimate the integrated aerodynamic coefficients.

Respond with a single JSON object of the form {"cl": <lift coefficient>, "cd": <drag coefficient>, "cm": <pitching moment coefficient>} and nothing else. Values must be finite numbers within physical ranges (cl in [-0.5, 1.2], cd in [0, 0.2], cm in [-0.5, 1.5]).
