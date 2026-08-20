A fifth-order WENO scheme is used to simulate a 2D inviscid shear layer with initial velocity profile \( u(y) = U_0 \tanh(y/\delta) \) and \( v = 0 \), perturbed slightly to trigger Kelvin–Helmholtz instability. The grid is uniform, and WENO reconstruction is applied dimension-by-dimension. What is the most likely source of error that causes under-prediction of vortex roll-up and slower growth of instability when compared to spectral DNS data?

1. WENO is too dissipative near discontinuities, reducing vortex strength uniformly
2. Nonlinear weights suppress high-order accuracy near extrema, reducing convergence rate
3. Dimension-by-dimension WENO introduces numerical anisotropy, smearing shear in non-grid-aligned directions
4. Shear layer instability is not resolvable without explicit subgrid-scale modeling

Answer with only the number (1, 2, 3, or 4).
