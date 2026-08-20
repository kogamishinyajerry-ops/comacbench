You are given the parametric geometry of a transonic kinked wing and a single operating condition, and must predict its aerodynamic coefficients.

## Wing geometry parameters
- SA: 33.0865
- DA: 5.4037
- DA_kink: 2.1106
- AR: 10.1634
- TR: 0.200928
- kink: 0.40174
- rootadj: 0.630955
- rtcs_0: 0.634655
- rtcs_1: 0.904599
- rtcs_2: 0.97673
- cambers_0: 0.790598
- cambers_1: 0.545667
- cambers_2: 0.0580941
- twists_0: -3.61995
- twists_1: -3.36479
- twists_2: -1.98726
- twists_3: -2.49838
- Uroot_0: 0.16698
- Uroot_1: 0.155508
- Uroot_2: 0.211426
- Uroot_3: -0.0659916
- Uroot_4: 0.516812
- Uroot_5: -0.271597
- Uroot_6: 0.521454
- Uroot_7: 0.00245662
- Uroot_8: 0.2721
- Uroot_9: 0.244973
- Utip_0: -0.123729
- Utip_1: -0.0408544
- Utip_2: -0.215008
- Utip_3: 0.0502496
- Utip_4: -0.31064
- Utip_5: 0.0212417
- Utip_6: -0.187809
- Utip_7: -0.0946678
- Utip_8: 0.071625
- Utip_9: 0.21855
- tcroot: 0.145388

## Operating condition
- angle of attack (aoa, deg): 9.00912
- Mach number: 0.857672

The wing was simulated with a RANS solver (ADflow). Estimate the integrated aerodynamic coefficients.

Respond with a single JSON object of the form {"cl": <lift coefficient>, "cd": <drag coefficient>, "cm": <pitching moment coefficient>} and nothing else. Values must be finite numbers within physical ranges (cl in [-0.5, 1.2], cd in [0, 0.2], cm in [-0.5, 1.5]).
