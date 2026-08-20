You are given the parametric geometry of a transonic kinked wing and a single operating condition, and must predict its aerodynamic coefficients.

## Wing geometry parameters
- SA: 32.7035
- DA: 7.71529
- DA_kink: 5.87467
- AR: 10.0637
- TR: 0.375801
- kink: 0.360697
- rootadj: 0.96725
- rtcs_0: 0.6316
- rtcs_1: 0.906185
- rtcs_2: 0.971333
- cambers_0: 0.749635
- cambers_1: 0.868011
- cambers_2: 0.666938
- twists_0: -3.82002
- twists_1: -2.11782
- twists_2: -1.01586
- twists_3: -2.74431
- Uroot_0: 0.194918
- Uroot_1: 0.115179
- Uroot_2: 0.0939454
- Uroot_3: 0.217638
- Uroot_4: 0.147891
- Uroot_5: 0.0283203
- Uroot_6: 0.431648
- Uroot_7: -0.0594417
- Uroot_8: 0.449591
- Uroot_9: 0.277065
- Utip_0: -0.116793
- Utip_1: -0.0424999
- Utip_2: -0.237825
- Utip_3: 0.0413676
- Utip_4: -0.310195
- Utip_5: 0.0387615
- Utip_6: -0.199716
- Utip_7: -0.0781969
- Utip_8: 0.0703468
- Utip_9: 0.214283
- tcroot: 0.16242

## Operating condition
- angle of attack (aoa, deg): 10.1898
- Mach number: 0.807291

The wing was simulated with a RANS solver (ADflow). Estimate the integrated aerodynamic coefficients.

Respond with a single JSON object of the form {"cl": <lift coefficient>, "cd": <drag coefficient>, "cm": <pitching moment coefficient>} and nothing else. Values must be finite numbers within physical ranges (cl in [-0.5, 1.2], cd in [0, 0.2], cm in [-0.5, 1.5]).
