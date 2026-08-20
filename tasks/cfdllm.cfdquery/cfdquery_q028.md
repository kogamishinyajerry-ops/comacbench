Consider the second-order linear differential equation with a variable coefficient:
\[ \frac{d}{dx}\left(p(x)\frac{du}{dx}\right) = f(x) \]
On a non-uniform grid, the following finite difference approximation is used:
\[ \left.\frac{d}{dx}\left(p(x)\frac{du}{dx}\right)\right|_{x_i} \approx \frac{1}{h_i^*}\left[ p_{i+1/2} \frac{u_{i+1} - u_i}{h_i} - p_{i-1/2} \frac{u_i - u_{i-1}}{h_{i-1}} \right] \]
where \( h_i^* = \frac{1}{2}(h_i + h_{i-1}) \), and \( h_i = x_{i+1} - x_i \), \( h_{i-1} = x_i - x_{i-1} \), \( p_{i+1/2} = p\left(\frac{x_i + x_{i+1}}{2}\right) \), \( p_{i-1/2} = p\left(\frac{x_{i-1} + x_i}{2}\right) \).

What is the order of the leading truncation error?

1. $$\mathcal{O}(h_i - h_{i-1})$$
2. $$\mathcal{O}(h_i^2 + h_{i-1}^2)$$
3. $$\mathcal{O}(\max(h_i, h_{i-1})^2)$$
4. $$\mathcal{O}\left(\frac{h_i - h_{i-1}}{h_i + h_{i-1}}\right)$$

Answer with only the number (1, 2, 3, or 4).
