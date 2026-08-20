You are given the high-lift geometry parameters of a NASA CRM-HL aircraft (CRM with slats and flaps deployed) and an angle of attack, and must predict its aerodynamic force/moment coefficients.

## High-lift geometry parameters
- IB_Flap_Deflection: 24.8061
- OB_Flap_Deflection: 25.2208
- IB_Flap_Gap_Multiplier: 0.93305
- OB_Flap_Gap_Multiplier: 1.08604
- IB_Slat_Deflection: 18.2263
- OB_Slat_Deflection: 13.4423
- IB_Slat_Gap_Multiplier: 1.34893
- OB_Slat_Gap_Multiplier: 1.02488

## Operating condition
- angle of attack (deg): 4

The flow was simulated with wall-modeled LES (Fidelity Charles, 300-500M cell adaptive grids). Estimate the integrated coefficients.

Respond with a single JSON object of the form {"cl": <lift coefficient>, "cd": <drag coefficient>, "cm": <pitching moment coefficient>} and nothing else. Values must be finite numbers within physical ranges (cl in [0, 5], cd in [0.05, 0.8], cm in [-2, 0.5]).
