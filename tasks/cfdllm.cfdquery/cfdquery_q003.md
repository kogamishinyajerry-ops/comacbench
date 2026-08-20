Consider the general finite difference approximation for the second derivative on a uniform grid:

$$
\frac{\partial^2 u}{\partial x^2} \approx \frac{1}{\Delta x^2}\left( a u_{i-2} + b u_{i-1} + c u_i + b u_{i+1} + a u_{i+2} \right)
$$

where $a$, $b$, and $c$ are constants chosen to achieve fourth-order accuracy. If this scheme is applied to $u(x) = e^{i k x}$, which of the following expressions best represents the numerical dispersion relation and **ensures both fourth-order accuracy and stability on all $k \in [0, \pi/\Delta x]$**?

1. The dispersion relation is exact, i.e., $k_{\text{mod}}^2 = k^2$, for all $k$, indicating zero phase and group error.
2. $k_{\text{mod}}^2 = \frac{1}{\Delta x^2}\left( -2a \cos(2k\Delta x) - 2b \cos(k\Delta x) + c \right)$, and for stability the condition $a < 0,\ b > 0$ must hold.
3. To achieve 4th order accuracy and stability, the coefficients must satisfy: $a = -\frac{1}{12},\ b = \frac{4}{3},\ c = -\frac{5}{2}$, and the amplification factor $G(k)$ must satisfy $|G(k)| \leq 1$ for all $k$.
4. The modified wavenumber is: $k_{\text{mod}} = \frac{\sin(k\Delta x)}{\Delta x}$, so the scheme is inherently first-order accurate.

Answer with only the number (1, 2, 3, or 4).
