You are given the parametric geometry of a transonic kinked wing and a single operating condition, and must predict its aerodynamic coefficients.

## Wing geometry parameters
- SA: 29.8227
- DA: 5.887
- DA_kink: 1.09237
- AR: 10.4555
- TR: 0.179569
- kink: 0.376841
- rootadj: 0.329069
- rtcs_0: 0.640478
- rtcs_1: 0.936124
- rtcs_2: 0.936147
- cambers_0: 0.344704
- cambers_1: 0.569596
- cambers_2: 0.28658
- twists_0: -2.91582
- twists_1: -2.33045
- twists_2: -1.02867
- twists_3: -2.10846
- Uroot_0: 0.128921
- Uroot_1: 0.13011
- Uroot_2: 0.196102
- Uroot_3: 0.0860362
- Uroot_4: 0.268106
- Uroot_5: 0.166467
- Uroot_6: 0.0971067
- Uroot_7: 0.150976
- Uroot_8: 0.20471
- Uroot_9: 0.0511775
- Utip_0: -0.159858
- Utip_1: -0.0325571
- Utip_2: -0.214483
- Utip_3: -0.0398055
- Utip_4: -0.146669
- Utip_5: -0.0997357
- Utip_6: -0.0986057
- Utip_7: -0.199968
- Utip_8: 0.199751
- Utip_9: 0.0860522
- tcroot: 0.141458

## Operating condition
- angle of attack (aoa, deg): 9.40491
- Mach number: 0.755263

The wing was simulated with a RANS solver (ADflow). Estimate the integrated aerodynamic coefficients.

Respond with a single JSON object of the form {"cl": <lift coefficient>, "cd": <drag coefficient>, "cm": <pitching moment coefficient>} and nothing else. Values must be finite numbers within physical ranges (cl in [-0.5, 1.2], cd in [0, 0.2], cm in [-0.5, 1.5]).
