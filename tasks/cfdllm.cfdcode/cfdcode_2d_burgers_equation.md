You are given the following partial differential equation (PDE) problem:

**Equation:**
\[
\begin{align*}
\frac{\partial u}{\partial t} + u \frac{\partial u}{\partial x} + v \frac{\partial u}{\partial y} &= \nu \left( \frac{\partial^2 u}{\partial x^2} + \frac{\partial^2 u}{\partial y^2} \right) \\
\frac{\partial v}{\partial t} + u \frac{\partial v}{\partial x} + v \frac{\partial v}{\partial y} &= \nu \left( \frac{\partial^2 v}{\partial x^2} + \frac{\partial^2 v}{\partial y^2} \right)
\end{align*}
\]

where:
- \( u(x,y,t) \), \( v(x,y,t) \): velocity components in x and y
- \( \nu = 0.01 \): kinematic viscosity

**Boundary Conditions:**
Dirichlet boundary conditions:
\[
  u = 1, \quad v = 1 \text{ on all boundaries}
\]

**Initial Conditions:**
Set \( u = 1 \), \( v = 1 \) throughout the domain, except:
\[
  u = v = 2 \quad \text{for } 0.5 \leq x, y \leq 1
\]

**Domain:**
- Spatial domain: \( x, y \in [0, 2] \), Temporal domain: (t \in [0, 0.027])

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
