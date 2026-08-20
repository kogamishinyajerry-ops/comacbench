You are given the parametric geometry of a transonic kinked wing and a single operating condition, and must predict its aerodynamic coefficients.

## Wing geometry parameters
- SA: 31.9647
- DA: 4.30007
- DA_kink: 0.800234
- AR: 8.98437
- TR: 0.352881
- kink: 0.380711
- rootadj: 0.673071
- rtcs_0: 0.66528
- rtcs_1: 0.941398
- rtcs_2: 0.934506
- cambers_0: 0.379183
- cambers_1: 0.58844
- cambers_2: 0.533331
- twists_0: -2.55952
- twists_1: -2.18137
- twists_2: -1.60232
- twists_3: -2.3285
- Uroot_0: 0.127137
- Uroot_1: 0.1275
- Uroot_2: 0.196626
- Uroot_3: 0.0884899
- Uroot_4: 0.24768
- Uroot_5: 0.222962
- Uroot_6: 0.188346
- Uroot_7: 0.1575
- Uroot_8: 0.29573
- Uroot_9: 0.0335641
- Utip_0: -0.152142
- Utip_1: -0.0532328
- Utip_2: -0.226922
- Utip_3: -0.0483371
- Utip_4: -0.138607
- Utip_5: -0.112465
- Utip_6: -0.0906998
- Utip_7: -0.211882
- Utip_8: 0.199702
- Utip_9: 0.0766764
- tcroot: 0.15062

## Operating condition
- angle of attack (aoa, deg): 7.34276
- Mach number: 0.848973

The wing was simulated with a RANS solver (ADflow). Estimate the integrated aerodynamic coefficients.

Respond with a single JSON object of the form {"cl": <lift coefficient>, "cd": <drag coefficient>, "cm": <pitching moment coefficient>} and nothing else. Values must be finite numbers within physical ranges (cl in [-0.5, 1.2], cd in [0, 0.2], cm in [-0.5, 1.5]).
