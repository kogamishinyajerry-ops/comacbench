do a laminar, compressible flow over a forward-facing step using the rhoCentralFoam solver. Boundary conditions include a fixed velocity of 2.5m/s and temperature of 1 K at the inlet and slip conditions on the obstacle. Use timestep of 0.002 and output every 0.1. Finaltime is 4.

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

