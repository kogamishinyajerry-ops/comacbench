A high-order split-form entropy-stable DG method is used to solve the compressible Navier–Stokes equations augmented with multiple passive scalars \( Z_i \) representing species mass fractions. The scalar fluxes are discretized using central fluxes, while the main system uses entropy-conservative fluxes. The mesh is curved and moving, with a time-dependent geometric mapping \( \mathbf{x}(\xi, \eta, t) \), and the Jacobian \( J \in \mathbb{P}^{p-1} \), while \( \mathbf{U}, Z_i \in \mathbb{P}^{p} \). The total entropy includes contributions from both the thermal and scalar components. A slow increase in entropy is observed over long-time simulations. What is the most plausible dominant source of this entropy growth?

1. Passive scalars do contribute to the total entropy, but central fluxes lack numerical dissipation or entropy-conservative symmetry, allowing unbalanced entropy production when coupled with geometric drift
2. Geometric under-resolution introduces \( \mathcal{O}(h^p) \) aliasing in the scalar–Jacobian interaction terms, particularly in \( J \cdot Z_i \ln Z_i \), producing a non-canceling entropy residual in the volume
3. The fluxes for \( \mathbf{U} \) are entropy-conservative, so the system entropy must be preserved if the quadrature is exact and mapping is smooth
4. Entropy variable projection for \( Z_i \) is mismatched in degree due to central flux interpolation, and without symmetric flux formulation or flux–Jacobian commutation, this leads to nonzero residuals that scale as \( \mathcal{O}(h^p) \)

Answer with only the number (1, 2, 3, or 4).
