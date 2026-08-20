Consider a reacting compressible Navier–Stokes solver using high-order split-form DG on a curved, moving mesh. The solution includes \( \mathbf{U} = [\rho, \rho u, \rho E, Y_i] \) with source terms \( \omega_i = A_i Y_i \exp(-E_i/T) \), and geometry mapping Jacobian \( J \in \mathbb{P}^{p-1} \). The entropy variable for species is \( W_i = \ln Y_i \). No modal projection is applied to source terms. At the flame-shock interaction zone, entropy drift and aliasing-induced overshoots are observed. Which of the following most accurately quantifies the dominant source of entropy production and its underlying mechanics?

1. Modal mismatch of \( \omega_i \in \mathbb{P}^p \) and \( W_i = \ln Y_i \in \mathbb{P}^{2p} \) causes non-orthogonal residual \( \epsilon \sim \mathcal{O}(h^p) \), amplified in high-curvature regions where \( J \cdot W_i \cdot \omega_i \notin \mathbb{P}^{3p-1} \)
2. Shock misalignment with element edges generates geometric non-conservativity, leading to entropy leakage at interfaces through misestimated flux Jacobians
3. The exponential source \( \omega_i \) dominates entropy evolution, but if the shock is aligned, the split-form structure fully cancels out entropy flux imbalances
4. Post-shock relaxation delay from insufficient artificial viscosity delays energy dissipation, but entropy balance remains formally closed if quadrature is exact

Answer with only the number (1, 2, 3, or 4).
