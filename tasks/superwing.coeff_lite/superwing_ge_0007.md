You are given the parametric geometry of a transonic kinked wing and a single operating condition, and must predict its aerodynamic coefficients.

## Wing geometry parameters
- SA: 29.0873
- DA: 5.07768
- DA_kink: 5.64211
- AR: 10.1084
- TR: 0.263523
- kink: 0.415131
- rootadj: 0.248752
- rtcs_0: 0.651163
- rtcs_1: 0.938632
- rtcs_2: 0.933792
- cambers_0: 0.785416
- cambers_1: 0.744797
- cambers_2: 0.135213
- twists_0: -2.01992
- twists_1: -2.82368
- twists_2: -2.84504
- twists_3: -2.3477
- Uroot_0: 0.142618
- Uroot_1: 0.0846176
- Uroot_2: 0.193033
- Uroot_3: 0.0259457
- Uroot_4: 0.364838
- Uroot_5: -0.133473
- Uroot_6: 0.49612
- Uroot_7: 0.00102344
- Uroot_8: 0.275678
- Uroot_9: 0.239946
- Utip_0: -0.119206
- Utip_1: -0.035769
- Utip_2: -0.222051
- Utip_3: 0.050237
- Utip_4: -0.307229
- Utip_5: 0.0157435
- Utip_6: -0.190914
- Utip_7: -0.0761185
- Utip_8: 0.0805046
- Utip_9: 0.213089
- tcroot: 0.151212

## Operating condition
- angle of attack (aoa, deg): 2.60521
- Mach number: 0.862418

The wing was simulated with a RANS solver (ADflow). Estimate the integrated aerodynamic coefficients.

Respond with a single JSON object of the form {"cl": <lift coefficient>, "cd": <drag coefficient>, "cm": <pitching moment coefficient>} and nothing else. Values must be finite numbers within physical ranges (cl in [-0.5, 1.2], cd in [0, 0.2], cm in [-0.5, 1.5]).
