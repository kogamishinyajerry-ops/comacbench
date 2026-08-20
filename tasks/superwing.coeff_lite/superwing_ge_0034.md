You are given the parametric geometry of a transonic kinked wing and a single operating condition, and must predict its aerodynamic coefficients.

## Wing geometry parameters
- SA: 30.3598
- DA: 5.29778
- DA_kink: 4.08913
- AR: 9.19799
- TR: 0.185586
- kink: 0.387602
- rootadj: 0.335912
- rtcs_0: 0.635485
- rtcs_1: 0.966719
- rtcs_2: 0.966524
- cambers_0: 0.359284
- cambers_1: 0.834904
- cambers_2: 0.180848
- twists_0: -2.07872
- twists_1: -2.51653
- twists_2: -2.83277
- twists_3: -1.23055
- Uroot_0: 0.193149
- Uroot_1: 0.110624
- Uroot_2: 0.112796
- Uroot_3: 0.21777
- Uroot_4: 0.100096
- Uroot_5: 0.047516
- Uroot_6: 0.452057
- Uroot_7: -0.0954074
- Uroot_8: 0.441873
- Uroot_9: 0.270436
- Utip_0: -0.124876
- Utip_1: -0.0373433
- Utip_2: -0.215048
- Utip_3: 0.0502589
- Utip_4: -0.310698
- Utip_5: 0.0187194
- Utip_6: -0.187844
- Utip_7: -0.0861854
- Utip_8: 0.0716387
- Utip_9: 0.224968
- tcroot: 0.156348

## Operating condition
- angle of attack (aoa, deg): 5.27683
- Mach number: 0.891754

The wing was simulated with a RANS solver (ADflow). Estimate the integrated aerodynamic coefficients.

Respond with a single JSON object of the form {"cl": <lift coefficient>, "cd": <drag coefficient>, "cm": <pitching moment coefficient>} and nothing else. Values must be finite numbers within physical ranges (cl in [-0.5, 1.2], cd in [0, 0.2], cm in [-0.5, 1.5]).
