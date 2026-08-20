You are given the parametric geometry of a transonic kinked wing and a single operating condition, and must predict its aerodynamic coefficients.

## Wing geometry parameters
- SA: 28.0387
- DA: 4.86369
- DA_kink: 1.35635
- AR: 10.2247
- TR: 0.240361
- kink: 0.419165
- rootadj: 0.633654
- rtcs_0: 0.635417
- rtcs_1: 0.97683
- rtcs_2: 0.970592
- cambers_0: 0.494672
- cambers_1: 0.780972
- cambers_2: 0.25705
- twists_0: -2.08142
- twists_1: -3.8355
- twists_2: -2.29083
- twists_3: -1.36028
- Uroot_0: 0.0980607
- Uroot_1: 0.112163
- Uroot_2: 0.278477
- Uroot_3: -0.156681
- Uroot_4: 0.774925
- Uroot_5: -0.572429
- Uroot_6: 0.87724
- Uroot_7: -0.0934736
- Uroot_8: 0.414745
- Uroot_9: 0.226471
- Utip_0: -0.150304
- Utip_1: -0.0449987
- Utip_2: -0.258061
- Utip_3: 0.0601015
- Utip_4: -0.372674
- Utip_5: 0.0211572
- Utip_6: -0.225314
- Utip_7: -0.10335
- Utip_8: 0.0853901
- Utip_9: 0.269849
- tcroot: 0.16733

## Operating condition
- angle of attack (aoa, deg): 2.2833
- Mach number: 0.767168

The wing was simulated with a RANS solver (ADflow). Estimate the integrated aerodynamic coefficients.

Respond with a single JSON object of the form {"cl": <lift coefficient>, "cd": <drag coefficient>, "cm": <pitching moment coefficient>} and nothing else. Values must be finite numbers within physical ranges (cl in [-0.5, 1.2], cd in [0, 0.2], cm in [-0.5, 1.5]).
