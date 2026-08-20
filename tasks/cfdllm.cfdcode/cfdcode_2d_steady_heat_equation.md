You are given the following partial differential equation (PDE) problem:

**Equation:**
\[
\frac{\partial^2 T}{\partial x^2} + \frac{\partial^2 T}{\partial y^2} = 0
\]

where:
- \( T(x, y) \): temperature field over the domain

**Boundary Conditions:**
- Dirichlet boundary conditions applied on all boundaries of a rectangular domain (width = 5, height = 4):
  - Left boundary (AB, at x = 0): \( T = 10^\circ C \)
  - Right boundary (EF, at x = 5): \( T = 40^\circ C \)
  - Top boundary (CD, at y = 4): \( T = 0^\circ C \)
  - Bottom boundary (G, at y = 0): \( T = 20^\circ C \)

**Initial Conditions:**
\[
  T(x, y) = 0 \text{ everywhere except at the boundaries}
\]

**Domain:**
- Spatial domain: \( x \in [0, 5], y \in [0, 4] \)

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
