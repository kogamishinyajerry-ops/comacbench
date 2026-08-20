You are given the parametric geometry of a transonic kinked wing and a single operating condition, and must predict its aerodynamic coefficients.

## Wing geometry parameters
- SA: 27.5493
- DA: 5.13925
- DA_kink: 3.48633
- AR: 9.86873
- TR: 0.311658
- kink: 0.406301
- rootadj: 0.331665
- rtcs_0: 0.632732
- rtcs_1: 0.911898
- rtcs_2: 0.923414
- cambers_0: 0.76044
- cambers_1: 0.880839
- cambers_2: 0.790595
- twists_0: -3.69626
- twists_1: -2.08324
- twists_2: -2.66132
- twists_3: -2.5739
- Uroot_0: 0.149953
- Uroot_1: 0.118195
- Uroot_2: 0.168612
- Uroot_3: 0.129043
- Uroot_4: 0.189896
- Uroot_5: 0.198548
- Uroot_6: 0.112289
- Uroot_7: 0.400965
- Uroot_8: 0.00819023
- Uroot_9: 0.455332
- Utip_0: -0.136981
- Utip_1: 0.00268261
- Utip_2: -0.495002
- Utip_3: 0.781378
- Utip_4: -1.76451
- Utip_5: 2.0115
- Utip_6: -2.15636
- Utip_7: 1.16141
- Utip_8: -0.378264
- Utip_9: 0.362052
- tcroot: 0.157416

## Operating condition
- angle of attack (aoa, deg): 5.52916
- Mach number: 0.834951

The wing was simulated with a RANS solver (ADflow). Estimate the integrated aerodynamic coefficients.

Respond with a single JSON object of the form {"cl": <lift coefficient>, "cd": <drag coefficient>, "cm": <pitching moment coefficient>} and nothing else. Values must be finite numbers within physical ranges (cl in [-0.5, 1.2], cd in [0, 0.2], cm in [-0.5, 1.5]).
