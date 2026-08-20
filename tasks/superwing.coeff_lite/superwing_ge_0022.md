You are given the parametric geometry of a transonic kinked wing and a single operating condition, and must predict its aerodynamic coefficients.

## Wing geometry parameters
- SA: 35.6298
- DA: 5.07928
- DA_kink: 2.02461
- AR: 9.18658
- TR: 0.334712
- kink: 0.377675
- rootadj: 0.463635
- rtcs_0: 0.688508
- rtcs_1: 0.91702
- rtcs_2: 0.997287
- cambers_0: 0.728099
- cambers_1: 0.943587
- cambers_2: 0.241137
- twists_0: -2.97645
- twists_1: -2.29616
- twists_2: -2.30356
- twists_3: -2.64071
- Uroot_0: 0.142644
- Uroot_1: 0.131189
- Uroot_2: 0.181182
- Uroot_3: -0.100345
- Uroot_4: 0.639544
- Uroot_5: -0.298467
- Uroot_6: 0.456471
- Uroot_7: 0.238541
- Uroot_8: 0.266018
- Uroot_9: 0.108144
- Utip_0: -0.126444
- Utip_1: -0.14522
- Utip_2: -0.125408
- Utip_3: -0.183915
- Utip_4: -0.162799
- Utip_5: -0.169556
- Utip_6: -0.0880851
- Utip_7: -0.056827
- Utip_8: -0.0640111
- Utip_9: 0.0564299
- tcroot: 0.14324

## Operating condition
- angle of attack (aoa, deg): 11.4375
- Mach number: 0.884786

The wing was simulated with a RANS solver (ADflow). Estimate the integrated aerodynamic coefficients.

Respond with a single JSON object of the form {"cl": <lift coefficient>, "cd": <drag coefficient>, "cm": <pitching moment coefficient>} and nothing else. Values must be finite numbers within physical ranges (cl in [-0.5, 1.2], cd in [0, 0.2], cm in [-0.5, 1.5]).
