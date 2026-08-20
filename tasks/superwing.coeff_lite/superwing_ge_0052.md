You are given the parametric geometry of a transonic kinked wing and a single operating condition, and must predict its aerodynamic coefficients.

## Wing geometry parameters
- SA: 33.1768
- DA: 5.47665
- DA_kink: 1.8846
- AR: 9.41677
- TR: 0.177917
- kink: 0.388821
- rootadj: 0.209485
- rtcs_0: 0.659408
- rtcs_1: 0.929307
- rtcs_2: 0.97723
- cambers_0: 0.395757
- cambers_1: 0.913754
- cambers_2: 0.747342
- twists_0: -2.862
- twists_1: -2.09829
- twists_2: -1.07196
- twists_3: -2.86525
- Uroot_0: 0.205653
- Uroot_1: 0.133226
- Uroot_2: 0.332131
- Uroot_3: -0.153698
- Uroot_4: 0.654843
- Uroot_5: -0.186469
- Uroot_6: 0.402708
- Uroot_7: 0.159465
- Uroot_8: 0.404557
- Uroot_9: 0.41592
- Utip_0: -0.162027
- Utip_1: -0.0488558
- Utip_2: -0.281306
- Utip_3: 0.0663113
- Utip_4: -0.406335
- Utip_5: 0.0223818
- Utip_6: -0.245789
- Utip_7: -0.112635
- Utip_8: 0.0940688
- Utip_9: 0.29548
- tcroot: 0.167758

## Operating condition
- angle of attack (aoa, deg): 11.1822
- Mach number: 0.780151

The wing was simulated with a RANS solver (ADflow). Estimate the integrated aerodynamic coefficients.

Respond with a single JSON object of the form {"cl": <lift coefficient>, "cd": <drag coefficient>, "cm": <pitching moment coefficient>} and nothing else. Values must be finite numbers within physical ranges (cl in [-0.5, 1.2], cd in [0, 0.2], cm in [-0.5, 1.5]).
