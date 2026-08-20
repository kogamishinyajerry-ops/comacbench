You are given the parametric geometry of a transonic kinked wing and a single operating condition, and must predict its aerodynamic coefficients.

## Wing geometry parameters
- SA: 27.6811
- DA: 4.57827
- DA_kink: 2.757
- AR: 9.8769
- TR: 0.279361
- kink: 0.396739
- rootadj: 0.248861
- rtcs_0: 0.617765
- rtcs_1: 0.916634
- rtcs_2: 0.932753
- cambers_0: 0.400293
- cambers_1: 0.610357
- cambers_2: 0.0739059
- twists_0: -2.95142
- twists_1: -2.47691
- twists_2: -2.50929
- twists_3: -2.29735
- Uroot_0: 0.111344
- Uroot_1: 0.104239
- Uroot_2: 0.204084
- Uroot_3: 0.0553205
- Uroot_4: 0.280959
- Uroot_5: 0.0434081
- Uroot_6: 0.297127
- Uroot_7: 0.139051
- Uroot_8: 0.247682
- Uroot_9: 0.279618
- Utip_0: -0.146423
- Utip_1: -0.055174
- Utip_2: -0.269809
- Utip_3: 0.0505075
- Utip_4: -0.343124
- Utip_5: 0.0195364
- Utip_6: -0.209599
- Utip_7: -0.0951865
- Utip_8: 0.0790324
- Utip_9: 0.227247
- tcroot: 0.166135

## Operating condition
- angle of attack (aoa, deg): 7.22448
- Mach number: 0.815969

The wing was simulated with a RANS solver (ADflow). Estimate the integrated aerodynamic coefficients.

Respond with a single JSON object of the form {"cl": <lift coefficient>, "cd": <drag coefficient>, "cm": <pitching moment coefficient>} and nothing else. Values must be finite numbers within physical ranges (cl in [-0.5, 1.2], cd in [0, 0.2], cm in [-0.5, 1.5]).
