You are given the parametric geometry of a transonic kinked wing and a single operating condition, and must predict its aerodynamic coefficients.

## Wing geometry parameters
- SA: 37.6292
- DA: 9.28782
- DA_kink: 9.03535
- AR: 8.40781
- TR: 0.348057
- kink: 0.385891
- rootadj: 0.826175
- rtcs_0: 0.643008
- rtcs_1: 0.932583
- rtcs_2: 0.953491
- cambers_0: 0.551241
- cambers_1: 0.807357
- cambers_2: 0.509029
- twists_0: -3.67686
- twists_1: -2.28487
- twists_2: -1.35513
- twists_3: -1.21282
- Uroot_0: 0.27349
- Uroot_1: 0.0574368
- Uroot_2: 0.269973
- Uroot_3: 0.21619
- Uroot_4: -0.100258
- Uroot_5: 0.606793
- Uroot_6: -0.195279
- Uroot_7: 0.463367
- Uroot_8: 0.289123
- Uroot_9: 0.495626
- Utip_0: -0.150139
- Utip_1: -0.0447922
- Utip_2: -0.257944
- Utip_3: 0.0602844
- Utip_4: -0.372674
- Utip_5: 0.0212169
- Utip_6: -0.225314
- Utip_7: -0.103377
- Utip_8: 0.0859285
- Utip_9: 0.269842
- tcroot: 0.160604

## Operating condition
- angle of attack (aoa, deg): 2.16358
- Mach number: 0.819119

The wing was simulated with a RANS solver (ADflow). Estimate the integrated aerodynamic coefficients.

Respond with a single JSON object of the form {"cl": <lift coefficient>, "cd": <drag coefficient>, "cm": <pitching moment coefficient>} and nothing else. Values must be finite numbers within physical ranges (cl in [-0.5, 1.2], cd in [0, 0.2], cm in [-0.5, 1.5]).
