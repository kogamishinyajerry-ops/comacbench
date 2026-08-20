You are given the parametric geometry of a transonic kinked wing and a single operating condition, and must predict its aerodynamic coefficients.

## Wing geometry parameters
- SA: 28.4781
- DA: 6.98643
- DA_kink: 5.30629
- AR: 10.9333
- TR: 0.398668
- kink: 0.362181
- rootadj: 0.743424
- rtcs_0: 0.673164
- rtcs_1: 0.968491
- rtcs_2: 0.981676
- cambers_0: 0.463739
- cambers_1: 0.747194
- cambers_2: 0.59214
- twists_0: -2.53884
- twists_1: -3.09983
- twists_2: -2.99305
- twists_3: -2.63637
- Uroot_0: 0.21788
- Uroot_1: 0.122677
- Uroot_2: 0.26036
- Uroot_3: 0.0909931
- Uroot_4: 0.252947
- Uroot_5: 0.164121
- Uroot_6: 0.27654
- Uroot_7: 0.222315
- Uroot_8: 0.31604
- Uroot_9: 0.355747
- Utip_0: -0.162651
- Utip_1: -0.0485249
- Utip_2: -0.27944
- Utip_3: 0.0650286
- Utip_4: -0.40373
- Utip_5: 0.0229849
- Utip_6: -0.24409
- Utip_7: -0.111992
- Utip_8: 0.0930892
- Utip_9: 0.292329
- tcroot: 0.165081

## Operating condition
- angle of attack (aoa, deg): 7.48432
- Mach number: 0.769914

The wing was simulated with a RANS solver (ADflow). Estimate the integrated aerodynamic coefficients.

Respond with a single JSON object of the form {"cl": <lift coefficient>, "cd": <drag coefficient>, "cm": <pitching moment coefficient>} and nothing else. Values must be finite numbers within physical ranges (cl in [-0.5, 1.2], cd in [0, 0.2], cm in [-0.5, 1.5]).
