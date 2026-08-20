do a counterflow flame simulation using OpenFOAM reactingFoam solver, employing a compressible flow solver for detailed combustion modeling. Define the computational domain as a 2D rectangular region with a width of 0.02 meters and a height of 0.02 meters. Use CH4, O2 and N2 as species. Include chemical kinetics using the reaction mechanism. velocity of fuel is 0.4 m/s and velocity of air is -0.2 m/s. Set the simulation runtime from 0 to 0.5 seconds with a write interval of 0.05 seconds and deltaT of 1e-6.

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

