You are given the parametric geometry of a transonic kinked wing and a single operating condition, and must predict its aerodynamic coefficients.

## Wing geometry parameters
- SA: 38.5858
- DA: 6.18224
- DA_kink: 4.7764
- AR: 10.3021
- TR: 0.354506
- kink: 0.363399
- rootadj: 0.62787
- rtcs_0: 0.624806
- rtcs_1: 0.975835
- rtcs_2: 0.921756
- cambers_0: 0.664208
- cambers_1: 0.758162
- cambers_2: 0.794075
- twists_0: -2.00957
- twists_1: -3.20394
- twists_2: -2.71697
- twists_3: -1.86687
- Uroot_0: 0.133239
- Uroot_1: 0.0784609
- Uroot_2: 0.20153
- Uroot_3: -0.0249447
- Uroot_4: 0.402548
- Uroot_5: -0.182711
- Uroot_6: 0.573573
- Uroot_7: -0.0496421
- Uroot_8: 0.321055
- Uroot_9: 0.250562
- Utip_0: -0.115883
- Utip_1: -0.0366918
- Utip_2: -0.221589
- Utip_3: 0.0615227
- Utip_4: -0.317955
- Utip_5: 0.0268723
- Utip_6: -0.193828
- Utip_7: -0.0723914
- Utip_8: 0.0569309
- Utip_9: 0.232337
- tcroot: 0.146375

## Operating condition
- angle of attack (aoa, deg): 7.11669
- Mach number: 0.791041

The wing was simulated with a RANS solver (ADflow). Estimate the integrated aerodynamic coefficients.

Respond with a single JSON object of the form {"cl": <lift coefficient>, "cd": <drag coefficient>, "cm": <pitching moment coefficient>} and nothing else. Values must be finite numbers within physical ranges (cl in [-0.5, 1.2], cd in [0, 0.2], cm in [-0.5, 1.5]).
