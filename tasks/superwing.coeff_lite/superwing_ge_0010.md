You are given the parametric geometry of a transonic kinked wing and a single operating condition, and must predict its aerodynamic coefficients.

## Wing geometry parameters
- SA: 31.161
- DA: 9.71611
- DA_kink: 6.30576
- AR: 10.1527
- TR: 0.307951
- kink: 0.371125
- rootadj: 0.877902
- rtcs_0: 0.665207
- rtcs_1: 0.936694
- rtcs_2: 0.96017
- cambers_0: 0.796085
- cambers_1: 0.543539
- cambers_2: 0.0345948
- twists_0: -2.97934
- twists_1: -3.63281
- twists_2: -2.02006
- twists_3: -1.49814
- Uroot_0: 0.179121
- Uroot_1: 0.0780971
- Uroot_2: 0.33432
- Uroot_3: -0.0826033
- Uroot_4: 0.452121
- Uroot_5: -0.04899
- Uroot_6: 0.375168
- Uroot_7: 0.144896
- Uroot_8: 0.264776
- Uroot_9: 0.250635
- Utip_0: -0.15025
- Utip_1: -0.044792
- Utip_2: -0.258621
- Utip_3: 0.0606399
- Utip_4: -0.373652
- Utip_5: 0.0214573
- Utip_6: -0.226101
- Utip_7: -0.10333
- Utip_8: 0.086154
- Utip_9: 0.271779
- tcroot: 0.166936

## Operating condition
- angle of attack (aoa, deg): 3.05187
- Mach number: 0.802836

The wing was simulated with a RANS solver (ADflow). Estimate the integrated aerodynamic coefficients.

Respond with a single JSON object of the form {"cl": <lift coefficient>, "cd": <drag coefficient>, "cm": <pitching moment coefficient>} and nothing else. Values must be finite numbers within physical ranges (cl in [-0.5, 1.2], cd in [0, 0.2], cm in [-0.5, 1.5]).
