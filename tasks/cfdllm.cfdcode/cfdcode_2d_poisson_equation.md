You are given the following partial differential equation (PDE) problem:

**Equation:**
\[
\frac{\partial^2 p}{\partial x^2} + \frac{\partial^2 p}{\partial y^2} = b(x, y)
\]

where:
- \( p(x, y) \): scalar potential (e.g., pressure)
- \( b(x, y) \): source term defined as:
  - \( b = 100 \) at \( x = \frac{1}{4}L_x, y = \frac{1}{4}L_y \)
  - \( b = -100 \) at \( x = \frac{3}{4}L_x, y = \frac{3}{4}L_y \)
  - \( b = 0 \) elsewhere

**Boundary Conditions:**
- Dirichlet boundary conditions:
  \( p = 0 \) at \( x = 0, 2 \) and \( y = 0, 1 \)

**Initial Conditions:**
\[
  p(x, y) = 0 \text{ everywhere in the domain}
\]

**Domain:**
- Spatial domain: \( x \in [0, 2], y \in [0, 1] \)

**Numerical Method:**
finite difference method

### Task:
- Write Python code to numerically solve the given CFD problem. Choose an appropriate numerical method based on the problem characteristics.
- If the problem is **unsteady**, only compute and save the **solution at the final time step**.
- For each specified variable, save the final solution as a separate `.npy` file using NumPy:
  - For **1D problems**, save each variable as a 1D NumPy array.
  - For **2D problems**, save each variable as a 2D NumPy array.
- The `.npy` files should contain only the final solution field (not intermediate steps) for each of the specified variables.
- **Save the following variables** at the final time step:
the relevant variables specified for the problem
(Each variable should be saved separately in its own `.npy` file, using the same name as provided in `save_values`).
- Ensure the generated code properly handles the solution for each specified variable and saves it correctly in `.npy` format.
- **Return only the complete, runnable Python code** that implements the above tasks, ensuring no extra explanations or information is included.
