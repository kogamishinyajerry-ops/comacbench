You are given the following partial differential equation (PDE) problem:

**Equation:**
\[
\frac{\partial u}{\partial t} + u \frac{\partial u}{\partial x} + v \frac{\partial u}{\partial y} = -\frac{1}{\rho} \frac{\partial p}{\partial x} + \nu \left( \frac{\partial^2 u}{\partial x^2} + \frac{\partial^2 u}{\partial y^2} \right) + F
\]
\[
\frac{\partial v}{\partial t} + u \frac{\partial v}{\partial x} + v \frac{\partial v}{\partial y} = -\frac{1}{\rho} \frac{\partial p}{\partial y} + \nu \left( \frac{\partial^2 v}{\partial x^2} + \frac{\partial^2 v}{\partial y^2} \right)
\]
\[
\frac{\partial^2 p}{\partial x^2} + \frac{\partial^2 p}{\partial y^2} = -\rho \left( \frac{\partial u}{\partial x}^2 + 2 \frac{\partial u}{\partial y} \frac{\partial v}{\partial x} + \frac{\partial v}{\partial y}^2 \right)
\]

where:
- \( u(x,y,t) \), \( v(x,y,t) \): velocity components
- \( p(x,y,t) \): pressure field
- \( \rho = 1 \): fluid density
- \( \nu = 0.1 \): kinematic viscosity
- \( F = 1 \): external force in the x-direction

**Boundary Conditions:**
- Periodic boundary conditions in x-direction for \( u, v, p \)
- No-slip boundary conditions in y-direction: \( u = 0, v = 0 \)
- \( \frac{\partial p}{\partial y} = 0 \) at \( y = 0, 2 \)

**Initial Conditions:**
\[
  u = 0, \quad v = 0, \quad p = 0 \text{ everywhere in the domain}
\]

**Domain:**
- Spatial domain: \( x, y \in [0, 2] \), Temporal domain: (t \in [0, 5.0])

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
