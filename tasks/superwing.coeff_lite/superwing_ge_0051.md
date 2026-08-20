You are given the parametric geometry of a transonic kinked wing and a single operating condition, and must predict its aerodynamic coefficients.

## Wing geometry parameters
- SA: 32.2796
- DA: 5.372
- DA_kink: 3.40815
- AR: 8.64775
- TR: 0.305658
- kink: 0.367005
- rootadj: 0.391838
- rtcs_0: 0.651806
- rtcs_1: 0.920007
- rtcs_2: 0.998149
- cambers_0: 0.488204
- cambers_1: 0.951088
- cambers_2: 0.647018
- twists_0: -3.16603
- twists_1: -2.08473
- twists_2: -1.78458
- twists_3: -1.61163
- Uroot_0: 0.194132
- Uroot_1: 0.111197
- Uroot_2: 0.108901
- Uroot_3: 0.222965
- Uroot_4: 0.0937542
- Uroot_5: 0.0497778
- Uroot_6: 0.454881
- Uroot_7: -0.0939929
- Uroot_8: 0.444284
- Uroot_9: 0.271391
- Utip_0: -0.124248
- Utip_1: -0.0365744
- Utip_2: -0.213365
- Utip_3: 0.0490251
- Utip_4: -0.307835
- Utip_5: 0.0180908
- Utip_6: -0.185576
- Utip_7: -0.0855501
- Utip_8: 0.0699589
- Utip_9: 0.224388
- tcroot: 0.161904

## Operating condition
- angle of attack (aoa, deg): 5.29733
- Mach number: 0.871473

The wing was simulated with a RANS solver (ADflow). Estimate the integrated aerodynamic coefficients.

Respond with a single JSON object of the form {"cl": <lift coefficient>, "cd": <drag coefficient>, "cm": <pitching moment coefficient>} and nothing else. Values must be finite numbers within physical ranges (cl in [-0.5, 1.2], cd in [0, 0.2], cm in [-0.5, 1.5]).
