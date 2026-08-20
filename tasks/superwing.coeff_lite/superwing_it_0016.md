You are given the parametric geometry of a transonic kinked wing and a single operating condition, and must predict its aerodynamic coefficients.

## Wing geometry parameters
- SA: 39.2128
- DA: 4.76035
- DA_kink: 3.54395
- AR: 8.57994
- TR: 0.212121
- kink: 0.399373
- rootadj: 0.277504
- rtcs_0: 0.638787
- rtcs_1: 0.972869
- rtcs_2: 0.961105
- cambers_0: 0.346749
- cambers_1: 0.694513
- cambers_2: 0.543954
- twists_0: -3.60662
- twists_1: -3.52692
- twists_2: -2.32909
- twists_3: -1.85868
- Uroot_0: 0.128379
- Uroot_1: 0.124026
- Uroot_2: 0.195181
- Uroot_3: 0.088888
- Uroot_4: 0.280824
- Uroot_5: 0.174373
- Uroot_6: 0.231823
- Uroot_7: 0.159181
- Uroot_8: 0.296829
- Uroot_9: 0.0592755
- Utip_0: -0.13934
- Utip_1: -0.0514313
- Utip_2: -0.229498
- Utip_3: -0.0354873
- Utip_4: -0.167692
- Utip_5: -0.108019
- Utip_6: -0.0928686
- Utip_7: -0.19248
- Utip_8: 0.2
- Utip_9: 0.0883161
- tcroot: 0.151

## Operating condition
- angle of attack (aoa, deg): 9.20573
- Mach number: 0.795059

The wing was simulated with a RANS solver (ADflow). Estimate the integrated aerodynamic coefficients.

Respond with a single JSON object of the form {"cl": <lift coefficient>, "cd": <drag coefficient>, "cm": <pitching moment coefficient>} and nothing else. Values must be finite numbers within physical ranges (cl in [-0.5, 1.2], cd in [0, 0.2], cm in [-0.5, 1.5]).
