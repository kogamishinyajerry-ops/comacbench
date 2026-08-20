You are given the parametric geometry of a transonic kinked wing and a single operating condition, and must predict its aerodynamic coefficients.

## Wing geometry parameters
- SA: 27.262
- DA: 5.68892
- DA_kink: 2.38678
- AR: 10.7072
- TR: 0.16363
- kink: 0.397731
- rootadj: 0.495091
- rtcs_0: 0.686694
- rtcs_1: 0.945286
- rtcs_2: 0.995025
- cambers_0: 0.332828
- cambers_1: 0.757291
- cambers_2: 0.585047
- twists_0: -3.40752
- twists_1: -2.28715
- twists_2: -1.8459
- twists_3: -1.70584
- Uroot_0: 0.193647
- Uroot_1: 0.107642
- Uroot_2: 0.239085
- Uroot_3: 0.0808459
- Uroot_4: 0.264238
- Uroot_5: 0.103508
- Uroot_6: 0.280756
- Uroot_7: 0.176151
- Uroot_8: 0.282356
- Uroot_9: 0.320908
- Utip_0: -0.150139
- Utip_1: -0.0453747
- Utip_2: -0.258129
- Utip_3: 0.0602844
- Utip_4: -0.373052
- Utip_5: 0.0229541
- Utip_6: -0.225273
- Utip_7: -0.103377
- Utip_8: 0.0859285
- Utip_9: 0.269842
- tcroot: 0.158178

## Operating condition
- angle of attack (aoa, deg): 8.60009
- Mach number: 0.767904

The wing was simulated with a RANS solver (ADflow). Estimate the integrated aerodynamic coefficients.

Respond with a single JSON object of the form {"cl": <lift coefficient>, "cd": <drag coefficient>, "cm": <pitching moment coefficient>} and nothing else. Values must be finite numbers within physical ranges (cl in [-0.5, 1.2], cd in [0, 0.2], cm in [-0.5, 1.5]).
