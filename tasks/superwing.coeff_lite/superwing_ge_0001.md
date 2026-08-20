You are given the parametric geometry of a transonic kinked wing and a single operating condition, and must predict its aerodynamic coefficients.

## Wing geometry parameters
- SA: 31.9647
- DA: 5.46749
- DA_kink: 1.45641
- AR: 8.49178
- TR: 0.392238
- kink: 0.362839
- rootadj: 0.55699
- rtcs_0: 0.666639
- rtcs_1: 0.930219
- rtcs_2: 0.992042
- cambers_0: 0.395777
- cambers_1: 0.752712
- cambers_2: 0.543462
- twists_0: -3.83615
- twists_1: -2.56711
- twists_2: -2.10853
- twists_3: -2.19188
- Uroot_0: 0.193491
- Uroot_1: 0.122622
- Uroot_2: 0.095939
- Uroot_3: 0.246983
- Uroot_4: 0.0777049
- Uroot_5: 0.0328916
- Uroot_6: 0.500538
- Uroot_7: -0.142379
- Uroot_8: 0.444773
- Uroot_9: 0.262459
- Utip_0: -0.125477
- Utip_1: -0.0374326
- Utip_2: -0.215233
- Utip_3: 0.0501938
- Utip_4: -0.311169
- Utip_5: 0.0170724
- Utip_6: -0.187956
- Utip_7: -0.0849846
- Utip_8: 0.0722945
- Utip_9: 0.225691
- tcroot: 0.166362

## Operating condition
- angle of attack (aoa, deg): 4.12012
- Mach number: 0.842716

The wing was simulated with a RANS solver (ADflow). Estimate the integrated aerodynamic coefficients.

Respond with a single JSON object of the form {"cl": <lift coefficient>, "cd": <drag coefficient>, "cm": <pitching moment coefficient>} and nothing else. Values must be finite numbers within physical ranges (cl in [-0.5, 1.2], cd in [0, 0.2], cm in [-0.5, 1.5]).
