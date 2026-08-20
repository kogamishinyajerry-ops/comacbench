Conduct a 3D squarebend flow simulation using OpenFOAM. The computational domain includes multiple regions, with vertices defined as inlet points at (-50, 25, 25) and (-50, 25, -25), outlet points at (-500, -75, 25) and (-500, -75, -25), and mid-bend points like (25, 0, 25) and (25, 0, -25). Follow the same geomtery as the tutorial. Use a start time of 0 seconds, an end time of 500 seconds, a time step of 1 second, and write results every 100 seconds. Use a massflow rate inlet of 0.5 with turbulentBL profile. Outlet is pressureInletOutletVelocity. Temperature has an inlet value of 1000. Pressure inlet has a value of 110000. use kepsilon turbulence model. Use rhoSimpleFoam solver. Use Pr value of 0.71. Use mu value of 1e-4.

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

