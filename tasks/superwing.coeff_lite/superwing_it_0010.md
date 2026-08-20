You are given the parametric geometry of a transonic kinked wing and a single operating condition, and must predict its aerodynamic coefficients.

## Wing geometry parameters
- SA: 25.403
- DA: 4.23571
- DA_kink: 5.88741
- AR: 9.72094
- TR: 0.219555
- kink: 0.383404
- rootadj: 0.100058
- rtcs_0: 0.621631
- rtcs_1: 0.920128
- rtcs_2: 0.937781
- cambers_0: 0.384965
- cambers_1: 0.829683
- cambers_2: 0.111823
- twists_0: -3.72635
- twists_1: -2.97729
- twists_2: -1.88456
- twists_3: -1.18262
- Uroot_0: 0.136396
- Uroot_1: 0.140346
- Uroot_2: 0.267158
- Uroot_3: -0.0442724
- Uroot_4: 0.497547
- Uroot_5: -0.114476
- Uroot_6: 0.371698
- Uroot_7: 0.0304603
- Uroot_8: 0.309003
- Uroot_9: 0.215133
- Utip_0: -0.149932
- Utip_1: -0.04501
- Utip_2: -0.257769
- Utip_3: 0.0605456
- Utip_4: -0.372342
- Utip_5: 0.0207538
- Utip_6: -0.225204
- Utip_7: -0.103199
- Utip_8: 0.0856789
- Utip_9: 0.269498
- tcroot: 0.155635

## Operating condition
- angle of attack (aoa, deg): 6.70324
- Mach number: 0.899511

The wing was simulated with a RANS solver (ADflow). Estimate the integrated aerodynamic coefficients.

Respond with a single JSON object of the form {"cl": <lift coefficient>, "cd": <drag coefficient>, "cm": <pitching moment coefficient>} and nothing else. Values must be finite numbers within physical ranges (cl in [-0.5, 1.2], cd in [0, 0.2], cm in [-0.5, 1.5]).
