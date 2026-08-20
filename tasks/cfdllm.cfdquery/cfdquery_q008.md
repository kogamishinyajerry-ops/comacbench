In solving the compressible 2D Euler equations on a smooth but non-orthogonal curvilinear grid using a finite-difference scheme based on primitive (non-conservative) variables and central differencing, an unexpected entropy generation is observed in the absence of physical dissipation. Assuming a symmetric initial condition and ideal gas law, what is the most probable leading-order mechanism responsible for the observed non-physical entropy growth?

1. Discretization error is \( \mathcal{O}(h^2) \) and cancels out due to symmetry; entropy growth must be due to round-off
2. Violation of geometric conservation law introduces \( \mathcal{O}(h^2) \) spurious kinetic energy sources
3. Loss of discrete compatibility between pressure gradient and velocity divergence introduces \( \mathcal{O}(h) \) entropy-generating pseudo-compression waves
4. The use of primitive variables inherently causes \( \mathcal{O}(h^3) \) anisotropic pressure-velocity decoupling on non-orthogonal grids

Answer with only the number (1, 2, 3, or 4).
