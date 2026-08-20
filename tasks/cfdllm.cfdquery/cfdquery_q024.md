A 6th-order compact finite difference is used to approximate \( u''(x) \) on a nearly uniform grid. However, for \( h_{i-1} = 0.01 \), \( h_i = 0.1 \), the result shows only first-order convergence. Why?

1. The format degenerates to first order when step ratios differ significantly.
2. Floating-point cancellation dominates at small \( h \).
3. Even-order stencils generate spurious oscillations in asymmetric grids.
4. The scheme is unstable when \( h_{i}/h_{i-1} > 5 \).

Answer with only the number (1, 2, 3, or 4).
