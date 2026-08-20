In a high-order DG method for reactive flow on a curved, moving mesh, the solution \( U = [\rho, \rho u, \rho E, Y_1, ..., Y_N] \) evolves with split-form entropy-conservative fluxes and central source terms \( \omega_i(Y,T) \) for species reactions. The Jacobian \( J(x,y,t) \in \mathbb{P}^{p-1} \), while the species \( Y_i, T \in \mathbb{P}^{p} \). Suppose no entropy projection is applied to the source terms. Entropy growth is observed. Which mechanism most likely dominates the observed entropy imbalance?

1. The use of central discretization for source terms fails to match the entropy-variable projection space, leading to unresolved \( \ln Y_i \cdot \omega_i \) product aliasing that scales as \( \mathcal{O}(h^p) \)
2. Temporal integration scheme introduces entropy leakage due to Runge-Kutta substep drift, which dominates in unsteady stiff regimes regardless of source structure
3. Jacobian under-resolution creates geometric aliasing in \( J \cdot \ln Y_i \) and \( J \cdot T \) terms, which results in entropy oscillations at interfaces but not volume growth
4. Split-form fluxes eliminate aliasing from convective terms, but introduce higher-order cross-mode interaction between \( U \) and \( Y_i \), resulting in kinetic-entropy mode transfer

Answer with only the number (1, 2, 3, or 4).
