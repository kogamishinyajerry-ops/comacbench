In a reacting flow simulation using a high-order entropy-stable DG method with multiple conserved scalars and a moving, curved mesh, the main system fluxes are entropy-conservative split-form Roe-type, while scalar transport fluxes are handled with entropy-symmetric central fluxes. The scalar entropy variables \( W_{Z_i} = \ln Z_i \) are not explicitly projected into a consistent modal basis. The geometric Jacobian \( J \) is represented with degree \( p - 1 \), while solution fields are degree \( p \), and the time-marching scheme is third-order accurate. Over time, long-wavelength entropy oscillations are observed. What is the most probable combined mechanism for the entropy imbalance?

1. Central fluxes for scalars do not supply dissipation, but with exact quadrature and modal consistency, they would not produce entropy drift in isolation
2. The mismatch between scalar entropy variables and central flux evaluation introduces \( \mathcal{O}(h^p) \) modal aliasing, which leaks entropy into unresolved high-frequency modes
3. Mesh movement modifies the geometric Jacobian in time, breaking the discrete GCL, which is the dominant source of global entropy error even if the fluxes are symmetric
4. The time-marching scheme is not entropy conservative, and thus temporal quadrature errors accumulate entropy residuals regardless of spatial discretization

Answer with only the number (1, 2, 3, or 4).
