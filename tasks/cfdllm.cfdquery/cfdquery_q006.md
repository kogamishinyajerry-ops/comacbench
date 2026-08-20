Consider the compact finite difference scheme: $$\alpha f'_{i-1} + f'_i + \alpha f'_{i+1} = \frac{a}{2h}(f_{i+1} - f_{i-1})$$. Under periodic boundary conditions and Fourier mode $$f_j = e^{ikx_j}$$, the modified wavenumber becomes: $$k^* = \frac{a \sin(kh)}{1 + 2\alpha \cos(kh)}$$. What conditions on $$a$$ and $$\alpha$$ make this a fourth-order accurate scheme?

1. $$a = 1, \quad \alpha = \frac{1}{4}$$
2. $$a = \frac{4}{3}, \quad \alpha = \frac{1}{3}$$
3. $$a = \frac{3}{2}, \quad \alpha = \frac{1}{4}$$
4. $$a = \frac{2}{3}, \quad \alpha = \frac{1}{6}$$

Answer with only the number (1, 2, 3, or 4).
