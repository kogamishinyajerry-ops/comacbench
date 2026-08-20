You are given the high-lift geometry parameters of a NASA CRM-HL aircraft (CRM with slats and flaps deployed) and an angle of attack, and must predict its aerodynamic force/moment coefficients.

## High-lift geometry parameters
- IB_Flap_Deflection: 18.5975
- OB_Flap_Deflection: 10.9762
- IB_Flap_Gap_Multiplier: 1.06945
- OB_Flap_Gap_Multiplier: 0.612608
- IB_Slat_Deflection: 28.4016
- OB_Slat_Deflection: 29.8778
- IB_Slat_Gap_Multiplier: 1.45451
- OB_Slat_Gap_Multiplier: 1.48192

## Operating condition
- angle of attack (deg): 18

The flow was simulated with wall-modeled LES (Fidelity Charles, 300-500M cell adaptive grids). Estimate the integrated coefficients.

Respond with a single JSON object of the form {"cl": <lift coefficient>, "cd": <drag coefficient>, "cm": <pitching moment coefficient>} and nothing else. Values must be finite numbers within physical ranges (cl in [0, 5], cd in [0.05, 0.8], cm in [-2, 0.5]).
