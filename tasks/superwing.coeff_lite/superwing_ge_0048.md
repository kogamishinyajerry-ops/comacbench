You are given the parametric geometry of a transonic kinked wing and a single operating condition, and must predict its aerodynamic coefficients.

## Wing geometry parameters
- SA: 35.4739
- DA: 5.84462
- DA_kink: 3.99008
- AR: 10.5462
- TR: 0.330027
- kink: 0.398367
- rootadj: 0.424933
- rtcs_0: 0.674374
- rtcs_1: 0.948816
- rtcs_2: 0.971507
- cambers_0: 0.698793
- cambers_1: 0.501531
- cambers_2: 0.143402
- twists_0: -2.72381
- twists_1: -3.32943
- twists_2: -2.68075
- twists_3: -1.6021
- Uroot_0: 0.192751
- Uroot_1: 0.108874
- Uroot_2: 0.237163
- Uroot_3: 0.0808459
- Uroot_4: 0.26569
- Uroot_5: 0.103508
- Uroot_6: 0.280756
- Uroot_7: 0.176151
- Uroot_8: 0.282356
- Uroot_9: 0.320136
- Utip_0: -0.150139
- Utip_1: -0.0447922
- Utip_2: -0.257944
- Utip_3: 0.0602844
- Utip_4: -0.373052
- Utip_5: 0.0204414
- Utip_6: -0.225273
- Utip_7: -0.103377
- Utip_8: 0.0859285
- Utip_9: 0.269842
- tcroot: 0.1559

## Operating condition
- angle of attack (aoa, deg): 7.8441
- Mach number: 0.791226

The wing was simulated with a RANS solver (ADflow). Estimate the integrated aerodynamic coefficients.

Respond with a single JSON object of the form {"cl": <lift coefficient>, "cd": <drag coefficient>, "cm": <pitching moment coefficient>} and nothing else. Values must be finite numbers within physical ranges (cl in [-0.5, 1.2], cd in [0, 0.2], cm in [-0.5, 1.5]).
