You are solving the scalar conservation law:

\[ \frac{\partial u}{\partial t} + \frac{\partial f(u)}{\partial x} = 0 \quad \text{with} \quad f(u) = \frac{1}{2} u^2 \]

The entropy pair is:

\[ U(u) = \frac{1}{2} u^2, \quad F(u) = \frac{1}{3} u^3 \]

You use a finite volume method with a second-order MUSCL reconstruction and a minmod TVD limiter applied to the slope. The numerical flux at interface \( i+1/2 \) is:

\[ f_{i+1/2} = \frac{1}{2} (f(u_i^+) + f(u_{i+1}^-)) - \frac{1}{2} a_{i+1/2} (u_{i+1}^- - u_i^+) \]

where \( a_{i+1/2} = \max(|u_i^+|, |u_{i+1}^-|) \), and \( u_i^+, u_{i+1}^- \) are the limited values at the left and right sides.

At a shock, you observe that the limiter reduces the slope to zero in one cell. The shock moves left to right.

Which of the following best describes the entropy behavior across the shock?

1. The scheme is entropy stable because the limiter suppresses oscillations and prevents nonphysical values.
2. The scheme violates the discrete entropy inequality because the limiter disrupts flux symmetry and absorbs entropy.
3. Entropy remains conserved because the numerical flux is consistent and satisfies Lax-Friedrichs form.
4. Entropy error is negligible because the limiter only acts locally and does not affect integral quantities.

Answer with only the number (1, 2, 3, or 4).
