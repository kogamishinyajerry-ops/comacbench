You are given the parametric geometry of a transonic kinked wing and a single operating condition, and must predict its aerodynamic coefficients.

## Wing geometry parameters
- SA: 27.1879
- DA: 4.64178
- DA_kink: 4.65494
- AR: 8.60223
- TR: 0.322232
- kink: 0.374444
- rootadj: 0.402859
- rtcs_0: 0.663294
- rtcs_1: 0.93278
- rtcs_2: 0.991365
- cambers_0: 0.584795
- cambers_1: 0.574063
- cambers_2: 0.197173
- twists_0: -2.99648
- twists_1: -2.32115
- twists_2: -2.85096
- twists_3: -1.27991
- Uroot_0: 0.1566
- Uroot_1: 0.108501
- Uroot_2: 0.199496
- Uroot_3: 0.084879
- Uroot_4: 0.255031
- Uroot_5: 0.220715
- Uroot_6: 0.216253
- Uroot_7: 0.143786
- Uroot_8: 0.275492
- Uroot_9: 0.036261
- Utip_0: -0.150635
- Utip_1: -0.0649088
- Utip_2: -0.231998
- Utip_3: -0.0433163
- Utip_4: -0.144132
- Utip_5: -0.114406
- Utip_6: -0.102528
- Utip_7: -0.206292
- Utip_8: 0.192668
- Utip_9: 0.0721939
- tcroot: 0.142955

## Operating condition
- angle of attack (aoa, deg): 8.76754
- Mach number: 0.874747

The wing was simulated with a RANS solver (ADflow). Estimate the integrated aerodynamic coefficients.

Respond with a single JSON object of the form {"cl": <lift coefficient>, "cd": <drag coefficient>, "cm": <pitching moment coefficient>} and nothing else. Values must be finite numbers within physical ranges (cl in [-0.5, 1.2], cd in [0, 0.2], cm in [-0.5, 1.5]).
