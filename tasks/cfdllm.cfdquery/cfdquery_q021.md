In a 1D finite volume simulation of \( \partial_t u + \partial_x u = 0 \) on a non-uniform grid, the numerical flux at each interface is computed using a Godunov method. At interface \( x_{i+1/2} \), the left state \( u^- \) is computed via second-order reconstruction (limited), while the right state \( u^+ \) uses the raw cell average (no reconstruction).

Although each interface flux appears well-defined, over time, the total mass (\( \int u dx \)) drifts. What is the most likely explanation?

1. The asymmetric reconstruction leads to numerical flux imbalance and violates global conservation.
2. The time integrator is unstable on non-uniform meshes without matching reconstruction.
3. The scheme is second-order accurate, but numerical dispersion mimics mass loss.
4. Godunov fluxes are dissipative and require entropy corrections on non-uniform meshes.

Answer with only the number (1, 2, 3, or 4).
