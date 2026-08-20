A finite volume scheme solves the conservation law \( \partial_t u + \partial_x f(u) = s(u,x) \) on a non-uniform mesh. Fluxes \( f(u) \) are reconstructed using MUSCL with interface-centered integration. The source term \( s(u,x) = u \cos(10x) \) is evaluated only at cell centers. Over time, global conservation deteriorates despite local accuracy.

Which explanation best accounts for this behavior?

1. The source term is not integrated over the volume, breaking flux–source balance across cells.
2. The MUSCL reconstruction introduces anti-symmetric dispersion, accumulating over non-uniform grids.
3. The nonlinearity in \( s(u,x) \) induces stiffness and instability that appears as drift.
4. High-frequency cosine terms require interface quadrature to remain conservative.

Answer with only the number (1, 2, 3, or 4).
