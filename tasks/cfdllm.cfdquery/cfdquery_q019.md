We discretize the operator \( \frac{d}{dx} \left( p(x) \frac{du}{dx} \right) \) on a non-uniform 1D grid using the formula:

\[ \left. \frac{d}{dx}\left( p(x)\frac{du}{dx} \right) \right|_{x_i} \approx \frac{1}{h_i^*}\left[ p_{i+1/2} \frac{u_{i+1} - u_i}{h_i} - p_{i-1/2} \frac{u_i - u_{i-1}}{h_{i-1}} \right] \]

with \( h_i^* = \frac{1}{2}(h_i + h_{i-1}) \). Suppose \( u(x), p(x) \) are smooth. When \( h_i \ne h_{i-1} \), what is the **leading-order behavior of the truncation error** at node \( x_i \)?

1. $$\mathcal{O}(h_i - h_{i-1})$$
2. $$\mathcal{O}(h_i^2 + h_{i-1}^2)$$
3. $$\mathcal{O}(\max(h_i, h_{i-1})^2)$$
4. $$\mathcal{O}\left(\frac{h_i - h_{i-1}}{h_i + h_{i-1}}\right)$$

Answer with only the number (1, 2, 3, or 4).
