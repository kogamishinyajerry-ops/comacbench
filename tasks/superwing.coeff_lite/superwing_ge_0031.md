You are given the parametric geometry of a transonic kinked wing and a single operating condition, and must predict its aerodynamic coefficients.

## Wing geometry parameters
- SA: 25.2944
- DA: 4.54123
- DA_kink: 4.10751
- AR: 10.0858
- TR: 0.24727
- kink: 0.419758
- rootadj: 0.21817
- rtcs_0: 0.698657
- rtcs_1: 0.917546
- rtcs_2: 0.99855
- cambers_0: 0.340923
- cambers_1: 0.627249
- cambers_2: 0.167128
- twists_0: -3.66182
- twists_1: -3.91688
- twists_2: -2.53919
- twists_3: -2.45779
- Uroot_0: 0.16711
- Uroot_1: 0.123
- Uroot_2: 0.201597
- Uroot_3: 0.0950154
- Uroot_4: 0.308335
- Uroot_5: 0.0707196
- Uroot_6: 0.225677
- Uroot_7: 0.206477
- Uroot_8: 0.331156
- Uroot_9: 0.266076
- Utip_0: -0.150024
- Utip_1: -0.0447922
- Utip_2: -0.257944
- Utip_3: 0.0602844
- Utip_4: -0.372674
- Utip_5: 0.0212169
- Utip_6: -0.225314
- Utip_7: -0.103377
- Utip_8: 0.0859285
- Utip_9: 0.269842
- tcroot: 0.151662

## Operating condition
- angle of attack (aoa, deg): 7.34574
- Mach number: 0.834529

The wing was simulated with a RANS solver (ADflow). Estimate the integrated aerodynamic coefficients.

Respond with a single JSON object of the form {"cl": <lift coefficient>, "cd": <drag coefficient>, "cm": <pitching moment coefficient>} and nothing else. Values must be finite numbers within physical ranges (cl in [-0.5, 1.2], cd in [0, 0.2], cm in [-0.5, 1.5]).
