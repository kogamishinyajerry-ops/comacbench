You are given the parametric geometry of a transonic kinked wing and a single operating condition, and must predict its aerodynamic coefficients.

## Wing geometry parameters
- SA: 30.2356
- DA: 5.67598
- DA_kink: 4.38159
- AR: 10.3028
- TR: 0.224485
- kink: 0.38402
- rootadj: 0.529806
- rtcs_0: 0.638787
- rtcs_1: 0.949043
- rtcs_2: 0.956232
- cambers_0: 0.599222
- cambers_1: 0.672957
- cambers_2: 0.421362
- twists_0: -2.54514
- twists_1: -2.89364
- twists_2: -1.00824
- twists_3: -2.20987
- Uroot_0: 0.147377
- Uroot_1: 0.137853
- Uroot_2: 0.296917
- Uroot_3: -0.0238938
- Uroot_4: 0.447468
- Uroot_5: -0.0558095
- Uroot_6: 0.34015
- Uroot_7: 0.0875748
- Uroot_8: 0.338159
- Uroot_9: 0.245461
- Utip_0: -0.154138
- Utip_1: -0.0587718
- Utip_2: -0.278434
- Utip_3: 0.0184054
- Utip_4: -0.389879
- Utip_5: 0.0212487
- Utip_6: -0.229972
- Utip_7: -0.114456
- Utip_8: 0.086206
- Utip_9: 0.276212
- tcroot: 0.153956

## Operating condition
- angle of attack (aoa, deg): 2.14915
- Mach number: 0.864004

The wing was simulated with a RANS solver (ADflow). Estimate the integrated aerodynamic coefficients.

Respond with a single JSON object of the form {"cl": <lift coefficient>, "cd": <drag coefficient>, "cm": <pitching moment coefficient>} and nothing else. Values must be finite numbers within physical ranges (cl in [-0.5, 1.2], cd in [0, 0.2], cm in [-0.5, 1.5]).
