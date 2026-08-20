Perform a 2D supersonic flow simulation over a wedge. Create a 3D geometry spanning from -0.15242 m to 0.3048 m in the x-direction, 0 m to 0.1524 m in the y-direction, and -0.005 m to 0.005 m in the z-direction. The simulation starts at 0.0 seconds and runs until 0.2 seconds with a time step (deltaT) of 0.0001 seconds. The results are written every 0.02 seconds. The inlet velocity is 10 m/s, inlet temperature is 2 K and inlet pressure is 1 Pa. The wedge boundary uses slip boundary condition for velocity. Use normalized thermodynamic properties where molWeight is set to 11640.3, Cp is 2.5, Pr is 1.0, and dynamic viscosity mu is 0. This corresponds to a gas constant R of 0.7143 and a specific heat ratio of 1.4. Use rhoCentralFoam solver.

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

