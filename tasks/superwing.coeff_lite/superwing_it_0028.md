You are given the parametric geometry of a transonic kinked wing and a single operating condition, and must predict its aerodynamic coefficients.

## Wing geometry parameters
- SA: 31.6394
- DA: 4.46009
- DA_kink: 1.41773
- AR: 9.1375
- TR: 0.304244
- kink: 0.369559
- rootadj: 0.259229
- rtcs_0: 0.632147
- rtcs_1: 0.976104
- rtcs_2: 0.981048
- cambers_0: 0.43693
- cambers_1: 0.828781
- cambers_2: 0.717197
- twists_0: -2.17599
- twists_1: -2.89997
- twists_2: -2.15614
- twists_3: -2.46212
- Uroot_0: 0.115714
- Uroot_1: 0.143983
- Uroot_2: 0.200147
- Uroot_3: -0.1435
- Uroot_4: 0.775821
- Uroot_5: -0.396645
- Uroot_6: 0.405864
- Uroot_7: 0.307371
- Uroot_8: 0.322242
- Uroot_9: 0.0995369
- Utip_0: -0.142917
- Utip_1: -0.201431
- Utip_2: -0.111072
- Utip_3: -0.242902
- Utip_4: -0.117295
- Utip_5: -0.215098
- Utip_6: -0.0606438
- Utip_7: -0.0684533
- Utip_8: -0.093035
- Utip_9: 0.00322681
- tcroot: 0.163116

## Operating condition
- angle of attack (aoa, deg): 9.25216
- Mach number: 0.861044

The wing was simulated with a RANS solver (ADflow). Estimate the integrated aerodynamic coefficients.

Respond with a single JSON object of the form {"cl": <lift coefficient>, "cd": <drag coefficient>, "cm": <pitching moment coefficient>} and nothing else. Values must be finite numbers within physical ranges (cl in [-0.5, 1.2], cd in [0, 0.2], cm in [-0.5, 1.5]).
