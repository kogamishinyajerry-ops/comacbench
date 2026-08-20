You are given the parametric geometry of a transonic kinked wing and a single operating condition, and must predict its aerodynamic coefficients.

## Wing geometry parameters
- SA: 29.1658
- DA: 7.25437
- DA_kink: 6.98338
- AR: 8.29721
- TR: 0.381353
- kink: 0.412613
- rootadj: 0.819385
- rtcs_0: 0.669998
- rtcs_1: 0.966841
- rtcs_2: 0.977178
- cambers_0: 0.362802
- cambers_1: 0.901668
- cambers_2: 0.646264
- twists_0: -3.96619
- twists_1: -2.16496
- twists_2: -2.75519
- twists_3: -2.43987
- Uroot_0: 0.148999
- Uroot_1: 0.0968837
- Uroot_2: 0.233213
- Uroot_3: 0.000684938
- Uroot_4: 0.355943
- Uroot_5: -0.0197187
- Uroot_6: 0.374684
- Uroot_7: 0.0960411
- Uroot_8: 0.282914
- Uroot_9: 0.305703
- Utip_0: -0.136958
- Utip_1: -0.0406534
- Utip_2: -0.236802
- Utip_3: 0.0576431
- Utip_4: -0.344758
- Utip_5: 0.0271557
- Utip_6: -0.210685
- Utip_7: -0.0881058
- Utip_8: 0.0746798
- Utip_9: 0.251121
- tcroot: 0.149032

## Operating condition
- angle of attack (aoa, deg): 11.0764
- Mach number: 0.816325

The wing was simulated with a RANS solver (ADflow). Estimate the integrated aerodynamic coefficients.

Respond with a single JSON object of the form {"cl": <lift coefficient>, "cd": <drag coefficient>, "cm": <pitching moment coefficient>} and nothing else. Values must be finite numbers within physical ranges (cl in [-0.5, 1.2], cd in [0, 0.2], cm in [-0.5, 1.5]).
