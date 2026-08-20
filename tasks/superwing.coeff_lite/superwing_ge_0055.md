You are given the parametric geometry of a transonic kinked wing and a single operating condition, and must predict its aerodynamic coefficients.

## Wing geometry parameters
- SA: 32.1615
- DA: 5.15434
- DA_kink: 5.57455
- AR: 9.55933
- TR: 0.27295
- kink: 0.363168
- rootadj: 0.236606
- rtcs_0: 0.673707
- rtcs_1: 0.975479
- rtcs_2: 0.931559
- cambers_0: 0.632863
- cambers_1: 0.7978
- cambers_2: 0.541841
- twists_0: -2.05618
- twists_1: -2.67994
- twists_2: -2.8951
- twists_3: -1.15188
- Uroot_0: 0.164868
- Uroot_1: 0.0898872
- Uroot_2: 0.202131
- Uroot_3: 0.0707086
- Uroot_4: 0.278549
- Uroot_5: 0.0565205
- Uroot_6: 0.288594
- Uroot_7: 0.134512
- Uroot_8: 0.2481
- Uroot_9: 0.268971
- Utip_0: -0.136092
- Utip_1: -0.041702
- Utip_2: -0.236449
- Utip_3: 0.0554369
- Utip_4: -0.343327
- Utip_5: 0.0206886
- Utip_6: -0.206953
- Utip_7: -0.0947622
- Utip_8: 0.0777803
- Utip_9: 0.247355
- tcroot: 0.155856

## Operating condition
- angle of attack (aoa, deg): 9.52985
- Mach number: 0.780469

The wing was simulated with a RANS solver (ADflow). Estimate the integrated aerodynamic coefficients.

Respond with a single JSON object of the form {"cl": <lift coefficient>, "cd": <drag coefficient>, "cm": <pitching moment coefficient>} and nothing else. Values must be finite numbers within physical ranges (cl in [-0.5, 1.2], cd in [0, 0.2], cm in [-0.5, 1.5]).
