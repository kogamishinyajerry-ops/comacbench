You are given the following partial differential equation (PDE) problem:

**Equation:**
\[
\text{Momentum equation:} \\
\frac{\partial \mathbf{u}}{\partial t} + (\mathbf{u} \cdot \nabla)\mathbf{u} = - \frac{1}{\rho} \nabla p + \nu \nabla^2 \mathbf{u} \\
\text{Incompressibility constraint:} \\
\nabla \cdot \mathbf{u} = 0 \\
\text{Pressure Poisson equation:} \\
\nabla^2 p = \frac{\rho}{\Delta t} (\nabla \cdot \mathbf{u}^*)
\]

where:
- \( \mathbf{u} = [u(x, y, t), v(x, y, t)] \): velocity vector
- \( p(x, y, t) \): pressure
- \( \rho = 1.0 \): fluid density
- \( \nu = 0.1 \): kinematic viscosity
- \( \mathbf{u}^* \): intermediate velocity (before pressure correction)

**Boundary Conditions:**
- Velocity boundary conditions:
  - \( u = 1 \), \( v = 0 \) on the **top lid** (driven wall)
  - \( u = 0 \), \( v = 0 \) on **all other walls** (no-slip)
- Pressure boundary conditions:
  - Homogeneous Neumann \( \partial p/\partial n = 0 \) on all walls
  - Homogeneous Dirichlet \( p = 0 \) optionally at one reference point (to make pressure unique)

**Initial Conditions:**
\[
  u(x, y, 0) = 0, \quad v(x, y, 0) = 0, \quad p(x, y, 0) = 0
\]
(velocity and pressure fields are initialized to zero)

**Domain:**
- Spatial domain: \( x, y \in [0, 1] \)
- 2D square cavity with time evolution until steady state
 - Time domain \( t \in [0, 0.5] \)

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
