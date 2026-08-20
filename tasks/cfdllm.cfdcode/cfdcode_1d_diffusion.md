You are given the following partial differential equation (PDE) problem:

**Equation:**
\[
  \frac{\partial u}{\partial t} = \nu \frac{\partial^2 u}{\partial x^2}
\]

where:
- \( u(x,t) \) is the diffused quantity (e.g., temperature, concentration)
- \( \nu = 0.3 \) is the diffusion coefficient
- \( x \) is the spatial coordinate
- \( t \) is time

**Boundary Conditions:**
 

**Initial Conditions:**
\[ u(x, 0) = \begin{cases} 2, & \text{if } 0.5 \leq x \leq 1 \\ 1, & \text{elsewhere} \end{cases} \]

**Domain:**
- Spatial domain: \( x \in [0, 2] \),  Temporal domain: (t \in [0, 0.0333])

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
