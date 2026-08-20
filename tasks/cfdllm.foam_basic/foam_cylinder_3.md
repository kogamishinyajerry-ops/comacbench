do a laminar offsetcylinder simulation. Use PIMPLE algorithm with a generalized Newtonian model and Cross-Power-Law viscosity for momentum transport, characterized by specific parameters nuInf=10, m=0.4, n=3. Boundary conditions specify a fixed velocity of 1.5m/s at the inlet (left),zero gradient pressure at the outlet (right), and no-slip conditions for walls, including the cylinder surface. Use timestep of 0.0025 and output every 0.05. Finaltime is 0.5. use constant viscosity model with nu value of 1e-02 in physical properties.

## Output contract

Write a single Python 3 script that creates the complete OpenFOAM case in the current working directory. The script must create (with os.makedirs / open().write(), plain string contents):

- system/blockMeshDict, system/controlDict, system/fvSchemes, system/fvSolution
- constant/ ... (all dictionaries the solver needs, e.g. momentumTransport, physicalProperties, turbulenceProperties, etc.)
- 0/ ... (initial fields the solver needs)
- Allrun  (shell script: source $WM_PROJECT_DIR/bin/tools/RunFunctions, then runApplication blockMesh and runApplication <solver>)

Requirements:
- OpenFOAM version 10 (Foundation) dict syntax.
- endTime / writeInterval chosen so the run finishes quickly (a few seconds to ~1 min) and writes at least one time directory.
- The solver name in controlDict (application) must match the Allrun invocation.
- Use only os, math and built-ins in the script. Do not execute OpenFOAM commands from the script — only write files.

Respond with a single ```python code block and nothing else.

