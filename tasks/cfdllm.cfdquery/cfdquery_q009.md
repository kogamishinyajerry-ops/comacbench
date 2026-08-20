In solving the compressible Navier-Stokes equations for a low-Mach internal flow (e.g., airfoil at Ma = 0.05) using a preconditioned Roe-type scheme, the preconditioning matrix \( \mathbf{P} \) is applied to rescale acoustic and convective wave speeds. Suppose \( \mathbf{P} \) is only applied in the flux Jacobian but not consistently in the time derivative or residual smoothing terms. What is the dominant effect of this inconsistency on the solution?

1. Residual will stagnate due to ill-conditioning, but steady-state accuracy remains unaffected
2. Preconditioning improves convergence and accuracy regardless of consistency if CFL is low
3. Inconsistency introduces \( \mathcal{O}(1/Ma) \) artificial compression waves that corrupt the pressure field
4. Temporal discretization absorbs the inconsistency if dual time stepping is used with local time stepping

Answer with only the number (1, 2, 3, or 4).
