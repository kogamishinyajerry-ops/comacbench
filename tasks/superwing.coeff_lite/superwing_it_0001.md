You are given the parametric geometry of a transonic kinked wing and a single operating condition, and must predict its aerodynamic coefficients.

## Wing geometry parameters
- SA: 36.3076
- DA: 5.65587
- DA_kink: 4.05959
- AR: 9.82657
- TR: 0.260773
- kink: 0.390967
- rootadj: 0.34668
- rtcs_0: 0.629333
- rtcs_1: 0.929514
- rtcs_2: 0.928137
- cambers_0: 0.715453
- cambers_1: 0.796176
- cambers_2: 0.0317369
- twists_0: -2.14283
- twists_1: -3.65814
- twists_2: -1.90582
- twists_3: -1.59802
- Uroot_0: 0.142229
- Uroot_1: 0.122935
- Uroot_2: 0.163312
- Uroot_3: 0.147217
- Uroot_4: 0.152982
- Uroot_5: 0.238619
- Uroot_6: 0.0919913
- Uroot_7: 0.403385
- Uroot_8: 0.0537168
- Uroot_9: 0.450777
- Utip_0: -0.143848
- Utip_1: 0.0120541
- Utip_2: -0.584575
- Utip_3: 1.04384
- Utip_4: -1.84808
- Utip_5: 1.58226
- Utip_6: -1.3789
- Utip_7: 0.630731
- Utip_8: -0.309116
- Utip_9: 0.3619
- tcroot: 0.155881

## Operating condition
- angle of attack (aoa, deg): 5.60455
- Mach number: 0.844868

The wing was simulated with a RANS solver (ADflow). Estimate the integrated aerodynamic coefficients.

Respond with a single JSON object of the form {"cl": <lift coefficient>, "cd": <drag coefficient>, "cm": <pitching moment coefficient>} and nothing else. Values must be finite numbers within physical ranges (cl in [-0.5, 1.2], cd in [0, 0.2], cm in [-0.5, 1.5]).
