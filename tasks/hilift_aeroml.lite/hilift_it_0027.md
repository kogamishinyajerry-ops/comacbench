You are given the high-lift geometry parameters of a NASA CRM-HL aircraft (CRM with slats and flaps deployed) and an angle of attack, and must predict its aerodynamic force/moment coefficients.

## High-lift geometry parameters
- IB_Flap_Deflection: 23.6388
- OB_Flap_Deflection: 35.3867
- IB_Flap_Gap_Multiplier: 0.858584
- OB_Flap_Gap_Multiplier: 0.890382
- IB_Slat_Deflection: 22.0839
- OB_Slat_Deflection: 24.608
- IB_Slat_Gap_Multiplier: 1.16358
- OB_Slat_Gap_Multiplier: 1.32205

## Operating condition
- angle of attack (deg): 14

The flow was simulated with wall-modeled LES (Fidelity Charles, 300-500M cell adaptive grids). Estimate the integrated coefficients.

Respond with a single JSON object of the form {"cl": <lift coefficient>, "cd": <drag coefficient>, "cm": <pitching moment coefficient>} and nothing else. Values must be finite numbers within physical ranges (cl in [0, 5], cd in [0.05, 0.8], cm in [-2, 0.5]).
