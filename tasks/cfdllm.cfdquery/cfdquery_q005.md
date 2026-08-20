Consider the second-order linear differential equation with a variable coefficient: $$\frac{d}{dx}\left(p(x)\frac{du}{dx}\right) = f(x)$$ with non-uniform grid spacing and the finite difference approximation: $$\left.\frac{d}{dx}\left(p(x)\frac{du}{dx}\right)\right|_{x_i} \approx \frac{1}{h_i^*}\left[ p_{i+1/2} \frac{u_{i+1} - u_i}{h_i} - p_{i-1/2} \frac{u_i - u_{i-1}}{h_{i-1}} \right]$$ where $$h_i^* = \frac{1}{2}(h_i + h_{i-1})$$. What is the order of the **leading truncation error**?

1. $$\mathcal{O}(h_i - h_{i-1})$$
2. $$\mathcal{O}(h_i^2 + h_{i-1}^2)$$
3. $$\mathcal{O}(\max(h_i, h_{i-1})^2)$$
4. $$\mathcal{O}(\frac{h_i - h_{i-1}}{h_i + h_{i-1}})$$

Answer with only the number (1, 2, 3, or 4).
