You are given the parametric geometry of a transonic kinked wing and a single operating condition, and must predict its aerodynamic coefficients.

## Wing geometry parameters
- SA: 34.9032
- DA: 4.04365
- DA_kink: 1.86701
- AR: 8.1446
- TR: 0.256712
- kink: 0.375354
- rootadj: 0.376469
- rtcs_0: 0.639838
- rtcs_1: 0.957698
- rtcs_2: 0.975121
- cambers_0: 0.46746
- cambers_1: 0.830694
- cambers_2: 0.453906
- twists_0: -2.60957
- twists_1: -2.41076
- twists_2: -1.31705
- twists_3: -2.37757
- Uroot_0: 0.179437
- Uroot_1: 0.101674
- Uroot_2: 0.276086
- Uroot_3: -0.0625884
- Uroot_4: 0.553687
- Uroot_5: -0.300904
- Uroot_6: 0.678895
- Uroot_7: 0.0412844
- Uroot_8: 0.0688795
- Uroot_9: 0.431975
- Utip_0: -0.149764
- Utip_1: -0.0447922
- Utip_2: -0.257941
- Utip_3: 0.0602844
- Utip_4: -0.373689
- Utip_5: 0.0212169
- Utip_6: -0.226123
- Utip_7: -0.103377
- Utip_8: 0.0859285
- Utip_9: 0.269842
- tcroot: 0.147783

## Operating condition
- angle of attack (aoa, deg): 6.17662
- Mach number: 0.833254

The wing was simulated with a RANS solver (ADflow). Estimate the integrated aerodynamic coefficients.

Respond with a single JSON object of the form {"cl": <lift coefficient>, "cd": <drag coefficient>, "cm": <pitching moment coefficient>} and nothing else. Values must be finite numbers within physical ranges (cl in [-0.5, 1.2], cd in [0, 0.2], cm in [-0.5, 1.5]).
