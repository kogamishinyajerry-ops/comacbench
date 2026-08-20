You are given the following partial differential equation (PDE) problem:

**Equation:**
\[
\text{Poisson equation (in polar coordinates):} \\
\nabla^2 \psi = -\omega \\
\text{Vorticity transport equation:} \\
\frac{\partial \omega}{\partial t} + u_r \frac{\partial \omega}{\partial r} + \frac{u_\theta}{r} \frac{\partial \omega}{\partial \theta} = \nu \nabla^2 \omega
\]

where:
- \( \psi(r, \theta, t) \): streamfunction
- \( \omega(r, \theta, t) \): vorticity
- \( u_r = \frac{1}{r} \frac{\partial \psi}{\partial \theta} \), \( u_\theta = -\frac{\partial \psi}{\partial r} \): velocity components in polar coordinates
- \( \nu = 0.005 \): kinematic viscosity, and \(v_\infty = 1\)

**Boundary Conditions:**
- Inner boundary (cylinder surface): \( \psi = 20 \), \( \omega = 2(\psi_0 - \psi_1)/\Delta r^2 \)
- Outer boundary: \( \psi = v_\infty \cdot y + 20 \), \( \omega = 0 \)
- Periodic boundary in \( \theta \)-direction for both \( \psi \) and \( \omega \)

**Initial Conditions:**
\[
  \psi(r, \theta, 0) = 0, \quad \omega(r, \theta, 0) = 0
\]
Velocity field is initialized based on boundary conditions.

**Domain:**
- Spatial domain: \( r \in [0.5, 10] \), \( \theta \in [0, 2\pi] \)
- 2D flow around a fixed circular cylinder using polar coordinates 
 - Time domain: \( t \in [0, 10] \)

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
