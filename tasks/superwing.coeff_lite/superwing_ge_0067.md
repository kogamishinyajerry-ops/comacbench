You are given the parametric geometry of a transonic kinked wing and a single operating condition, and must predict its aerodynamic coefficients.

## Wing geometry parameters
- SA: 35.1437
- DA: 5.34743
- DA_kink: 3.47495
- AR: 9.64905
- TR: 0.387339
- kink: 0.380552
- rootadj: 0.413755
- rtcs_0: 0.68928
- rtcs_1: 0.968909
- rtcs_2: 0.932346
- cambers_0: 0.394495
- cambers_1: 0.933074
- cambers_2: 0.579684
- twists_0: -3.52819
- twists_1: -2.6837
- twists_2: -2.72956
- twists_3: -2.63372
- Uroot_0: 0.188915
- Uroot_1: 0.0656747
- Uroot_2: 0.165185
- Uroot_3: 0.138904
- Uroot_4: 0.155147
- Uroot_5: 0.0762395
- Uroot_6: 0.318166
- Uroot_7: 0.0214381
- Uroot_8: 0.461758
- Uroot_9: 0.293119
- Utip_0: -0.122686
- Utip_1: -0.0366019
- Utip_2: -0.210778
- Utip_3: 0.0492516
- Utip_4: -0.303904
- Utip_5: 0.017286
- Utip_6: -0.184032
- Utip_7: -0.0841584
- Utip_8: 0.0702161
- Utip_9: 0.2205
- tcroot: 0.167664

## Operating condition
- angle of attack (aoa, deg): 4.84036
- Mach number: 0.845189

The wing was simulated with a RANS solver (ADflow). Estimate the integrated aerodynamic coefficients.

Respond with a single JSON object of the form {"cl": <lift coefficient>, "cd": <drag coefficient>, "cm": <pitching moment coefficient>} and nothing else. Values must be finite numbers within physical ranges (cl in [-0.5, 1.2], cd in [0, 0.2], cm in [-0.5, 1.5]).
