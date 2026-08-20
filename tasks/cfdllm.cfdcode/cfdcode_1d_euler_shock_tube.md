You are given the following partial differential equation (PDE) problem:

**Equation:**
\[
  \frac{\partial \mathbf{U}}{\partial t} + \frac{\partial \mathbf{F}}{\partial x} = 0
\]

where:
- \( \rho \): Density  
- \( u \): Velocity  
- \( p \): Pressure  
- \( E = \frac{p}{(\gamma - 1)\rho} + \frac{u^2}{2} \): Total energy per unit mass  
- \( \gamma = 1.4 \): Ratio of specific heats (for air)
- \( \mathbf{U} = [\rho, \rho u, \rho E]^T \): Conservative variables
- \( \mathbf{F} = [\rho u, \rho u^2 + p, u(\rho E + p)]^T \): Flux vector

**Boundary Conditions:**
Reflective (no-flux) boundary conditions at both ends of the tube.

**Initial Conditions:**
Shock tube initially divided at \( x = 0 \):
- Left region (\( x < 0 \)):
  - \( \rho_L = 1.0 \)
  - \( u_L = 0.0 \)
  - \( p_L = 1.0 \)
- Right region (\( x \geq 0 \)):
  - \( \rho_R = 0.125 \)
  - \( u_R = 0.0 \)
  - \( p_R = 0.1 \)

**Domain:**
- Spatial domain: \( x \in [-1, 1] \), Temporal domain: (t \in [0, 0.25])

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
