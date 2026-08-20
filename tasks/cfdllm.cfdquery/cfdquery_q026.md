A high-order compact finite difference scheme approximates \( \nabla u \) on a smooth but non-orthogonal curvilinear mesh defined by mappings \( x = x(\xi, \eta), y = y(\xi, \eta) \). The transformed gradient is expressed as:

\[ \nabla u = \frac{\partial u}{\partial \xi} \nabla \xi + \frac{\partial u}{\partial \eta} \nabla \eta \]

Although the grid metrics \( \nabla \xi, \nabla \eta \) are smooth, the mesh is not orthogonal: \( \nabla \xi \cdot \nabla \eta \ne 0 \). Derivatives \( \partial u/\partial \xi, \partial u/\partial \eta \) are computed using fourth-order compact stencils.

Which of the following best characterizes the **leading-order numerical anisotropy error** introduced by this mesh?

1. $$\mathcal{O}(h^2 \cdot \nabla \xi \cdot \nabla \eta)$$ — cross-metric induced anisotropic error due to mesh non-orthogonality
2. $$\mathcal{O}(h^4)$$ — dominant compact stencil truncation error due to even-order accuracy
3. $$\mathcal{O}(J^{-1})$$ — error amplification due to inverse Jacobian in transformation
4. Negligible, as the smoothness of \( \nabla \xi, \nabla \eta \) cancels grid-induced anisotropy

Answer with only the number (1, 2, 3, or 4).
