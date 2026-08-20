Consider a second-order accurate central difference scheme for approximating \(\frac{d^2u}{dx^2}\) on a non-uniform grid where \(h_{i-1} = x_i - x_{i-1}\) and \(h_i = x_{i+1} - x_i\). The second derivative is approximated by a combination of values \(u_{i-1}, u_i, u_{i+1}\) as \(\frac{d^2u}{dx^2}|_{x_i} \approx a u_{i-1} + b u_i + c u_{i+1}\). Which of the following gives the correct expressions for coefficients \(a, b, c\)?

1. $$a = \frac{2}{h_{i-1}(h_{i-1} + h_i)},\quad b = -\frac{2}{h_{i-1} h_i},\quad c = \frac{2}{h_i(h_{i-1} + h_i)}$$
2. $$a = \frac{2}{h_i(h_{i-1} + h_i)},\quad b = -\frac{2}{h_{i-1} h_i},\quad c = \frac{2}{h_{i-1}(h_{i-1} + h_i)}$$
3. $$a = \frac{2}{h_{i-1}h_i},\quad b = -\frac{2}{h_{i-1}(h_{i-1} + h_i)},\quad c = \frac{2}{h_i(h_{i-1} + h_i)}$$
4. $$a = \frac{2}{h_{i-1}(h_i - h_{i-1})},\quad b = -\frac{2}{h_i h_{i-1}},\quad c = \frac{2}{h_i(h_i - h_{i-1})}$$

Answer with only the number (1, 2, 3, or 4).
