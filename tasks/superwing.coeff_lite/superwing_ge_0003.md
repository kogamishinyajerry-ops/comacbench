You are given the parametric geometry of a transonic kinked wing and a single operating condition, and must predict its aerodynamic coefficients.

## Wing geometry parameters
- SA: 33.2484
- DA: 4.52559
- DA_kink: 3.60793
- AR: 10.9163
- TR: 0.353939
- kink: 0.369941
- rootadj: 0.65841
- rtcs_0: 0.663983
- rtcs_1: 0.922907
- rtcs_2: 0.96647
- cambers_0: 0.341266
- cambers_1: 0.571881
- cambers_2: 0.609931
- twists_0: -2.9195
- twists_1: -3.66198
- twists_2: -1.30451
- twists_3: -1.08748
- Uroot_0: 0.148399
- Uroot_1: 0.0965733
- Uroot_2: 0.232617
- Uroot_3: 0.00161419
- Uroot_4: 0.353185
- Uroot_5: -0.013727
- Uroot_6: 0.370204
- Uroot_7: 0.0960123
- Uroot_8: 0.281542
- Uroot_9: 0.296835
- Utip_0: -0.137627
- Utip_1: -0.0410595
- Utip_2: -0.236449
- Utip_3: 0.0552607
- Utip_4: -0.341618
- Utip_5: 0.0193069
- Utip_6: -0.206538
- Utip_7: -0.0947622
- Utip_8: 0.0787678
- Utip_9: 0.247355
- tcroot: 0.154359

## Operating condition
- angle of attack (aoa, deg): 9.13528
- Mach number: 0.783026

The wing was simulated with a RANS solver (ADflow). Estimate the integrated aerodynamic coefficients.

Respond with a single JSON object of the form {"cl": <lift coefficient>, "cd": <drag coefficient>, "cm": <pitching moment coefficient>} and nothing else. Values must be finite numbers within physical ranges (cl in [-0.5, 1.2], cd in [0, 0.2], cm in [-0.5, 1.5]).
