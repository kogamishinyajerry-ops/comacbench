You are given the parametric geometry of a transonic kinked wing and a single operating condition, and must predict its aerodynamic coefficients.

## Wing geometry parameters
- SA: 26.5679
- DA: 5.85732
- DA_kink: 3.71859
- AR: 8.40956
- TR: 0.371175
- kink: 0.36574
- rootadj: 0.417577
- rtcs_0: 0.612478
- rtcs_1: 0.949938
- rtcs_2: 0.996849
- cambers_0: 0.523571
- cambers_1: 0.542137
- cambers_2: 0.146642
- twists_0: -2.03876
- twists_1: -3.56639
- twists_2: -2.3953
- twists_3: -1.92797
- Uroot_0: 0.156045
- Uroot_1: 0.0864121
- Uroot_2: 0.201274
- Uroot_3: 0.0437335
- Uroot_4: 0.26737
- Uroot_5: 0.0416937
- Uroot_6: 0.261822
- Uroot_7: 0.142466
- Uroot_8: 0.226444
- Uroot_9: 0.258315
- Utip_0: -0.125156
- Utip_1: -0.0373388
- Utip_2: -0.215034
- Utip_3: 0.0502431
- Utip_4: -0.310661
- Utip_5: 0.0176912
- Utip_6: -0.187822
- Utip_7: -0.0861752
- Utip_8: 0.0716302
- Utip_9: 0.224941
- tcroot: 0.155491

## Operating condition
- angle of attack (aoa, deg): 8.18505
- Mach number: 0.894917

The wing was simulated with a RANS solver (ADflow). Estimate the integrated aerodynamic coefficients.

Respond with a single JSON object of the form {"cl": <lift coefficient>, "cd": <drag coefficient>, "cm": <pitching moment coefficient>} and nothing else. Values must be finite numbers within physical ranges (cl in [-0.5, 1.2], cd in [0, 0.2], cm in [-0.5, 1.5]).
