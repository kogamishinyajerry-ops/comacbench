You are given the parametric geometry of a transonic kinked wing and a single operating condition, and must predict its aerodynamic coefficients.

## Wing geometry parameters
- SA: 32.9298
- DA: 8.36109
- DA_kink: 6.49412
- AR: 8.79615
- TR: 0.3059
- kink: 0.405845
- rootadj: 0.646754
- rtcs_0: 0.687678
- rtcs_1: 0.907631
- rtcs_2: 0.932089
- cambers_0: 0.537848
- cambers_1: 0.567005
- cambers_2: 0.783229
- twists_0: -3.44326
- twists_1: -2.69622
- twists_2: -1.42445
- twists_3: -1.40252
- Uroot_0: 0.13489
- Uroot_1: 0.132568
- Uroot_2: 0.215032
- Uroot_3: 0.0954757
- Uroot_4: 0.285918
- Uroot_5: 0.237112
- Uroot_6: 0.195138
- Uroot_7: 0.138365
- Uroot_8: 0.324958
- Uroot_9: 0.154695
- Utip_0: -0.14654
- Utip_1: -0.0481199
- Utip_2: -0.22523
- Utip_3: -0.0318267
- Utip_4: -0.154362
- Utip_5: -0.110039
- Utip_6: -0.0882526
- Utip_7: -0.21031
- Utip_8: 0.184556
- Utip_9: 0.189888
- tcroot: 0.148481

## Operating condition
- angle of attack (aoa, deg): 6.83146
- Mach number: 0.79571

The wing was simulated with a RANS solver (ADflow). Estimate the integrated aerodynamic coefficients.

Respond with a single JSON object of the form {"cl": <lift coefficient>, "cd": <drag coefficient>, "cm": <pitching moment coefficient>} and nothing else. Values must be finite numbers within physical ranges (cl in [-0.5, 1.2], cd in [0, 0.2], cm in [-0.5, 1.5]).
