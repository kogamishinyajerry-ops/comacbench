You are given the parametric geometry of a transonic kinked wing and a single operating condition, and must predict its aerodynamic coefficients.

## Wing geometry parameters
- SA: 27.6701
- DA: 6.95094
- DA_kink: 3.87732
- AR: 9.67296
- TR: 0.207989
- kink: 0.376927
- rootadj: 0.518518
- rtcs_0: 0.603312
- rtcs_1: 0.902268
- rtcs_2: 0.923483
- cambers_0: 0.486973
- cambers_1: 0.585703
- cambers_2: 0.558957
- twists_0: -3.23728
- twists_1: -3.47768
- twists_2: -1.84168
- twists_3: -2.6736
- Uroot_0: 0.0812547
- Uroot_1: 0.112542
- Uroot_2: 0.290415
- Uroot_3: -0.217271
- Uroot_4: 0.910554
- Uroot_5: -0.753591
- Uroot_6: 1
- Uroot_7: -0.155985
- Uroot_8: 0.435672
- Uroot_9: 0.215747
- Utip_0: -0.150139
- Utip_1: -0.0447922
- Utip_2: -0.257944
- Utip_3: 0.0602877
- Utip_4: -0.372674
- Utip_5: 0.0216952
- Utip_6: -0.225314
- Utip_7: -0.103377
- Utip_8: 0.0856041
- Utip_9: 0.270656
- tcroot: 0.151852

## Operating condition
- angle of attack (aoa, deg): 7.01264
- Mach number: 0.796692

The wing was simulated with a RANS solver (ADflow). Estimate the integrated aerodynamic coefficients.

Respond with a single JSON object of the form {"cl": <lift coefficient>, "cd": <drag coefficient>, "cm": <pitching moment coefficient>} and nothing else. Values must be finite numbers within physical ranges (cl in [-0.5, 1.2], cd in [0, 0.2], cm in [-0.5, 1.5]).
