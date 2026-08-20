You are analyzing the dissipative behavior of a finite difference scheme for the 1D linear advection equation $$\frac{\partial u}{\partial t} + a \frac{\partial u}{\partial x} = 0$$ using the Lax-Friedrichs method: $$u_j^{n+1} = \frac{1}{2}(u_{j+1}^n + u_{j-1}^n) - \frac{a \Delta t}{2\Delta x}(u_{j+1}^n - u_{j-1}^n)$$. Which of the following modified PDEs correctly captures the leading-order numerical dissipation introduced by this scheme?

1. $$\frac{\partial u}{\partial t} + a \frac{\partial u}{\partial x} = \frac{a^2 \Delta t^2}{6} \frac{\partial^3 u}{\partial x^3}$$
2. $$\frac{\partial u}{\partial t} + a \frac{\partial u}{\partial x} = \frac{\Delta x^2}{2\Delta t} \frac{\partial^2 u}{\partial x^2}$$
3. $$\frac{\partial u}{\partial t} + a \frac{\partial u}{\partial x} = \frac{a \Delta x^2}{6} \frac{\partial^3 u}{\partial x^3}$$
4. $$\frac{\partial u}{\partial t} + a \frac{\partial u}{\partial x} = -\frac{a^2 \Delta t}{2} \frac{\partial^2 u}{\partial x^2}$$

Answer with only the number (1, 2, 3, or 4).
