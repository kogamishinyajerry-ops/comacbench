You are given the parametric geometry of a transonic kinked wing and a single operating condition, and must predict its aerodynamic coefficients.

## Wing geometry parameters
- SA: 36.8531
- DA: 4.37387
- DA_kink: 1.09935
- AR: 9.89064
- TR: 0.292517
- kink: 0.368115
- rootadj: 0.432599
- rtcs_0: 0.623817
- rtcs_1: 0.956872
- rtcs_2: 0.95734
- cambers_0: 0.386037
- cambers_1: 0.544457
- cambers_2: 0.338881
- twists_0: -3.31454
- twists_1: -3.8477
- twists_2: -2.80725
- twists_3: -1.55717
- Uroot_0: 0.191687
- Uroot_1: 0.0716182
- Uroot_2: 0.172595
- Uroot_3: 0.110947
- Uroot_4: 0.191825
- Uroot_5: 0.0653278
- Uroot_6: 0.326288
- Uroot_7: 0.0153802
- Uroot_8: 0.449002
- Uroot_9: 0.294924
- Utip_0: -0.125116
- Utip_1: -0.0373268
- Utip_2: -0.2139
- Utip_3: 0.050237
- Utip_4: -0.310954
- Utip_5: 0.0176807
- Utip_6: -0.187972
- Utip_7: -0.0861474
- Utip_8: 0.071607
- Utip_9: 0.224868
- tcroot: 0.155674

## Operating condition
- angle of attack (aoa, deg): 8.5071
- Mach number: 0.83009

The wing was simulated with a RANS solver (ADflow). Estimate the integrated aerodynamic coefficients.

Respond with a single JSON object of the form {"cl": <lift coefficient>, "cd": <drag coefficient>, "cm": <pitching moment coefficient>} and nothing else. Values must be finite numbers within physical ranges (cl in [-0.5, 1.2], cd in [0, 0.2], cm in [-0.5, 1.5]).
