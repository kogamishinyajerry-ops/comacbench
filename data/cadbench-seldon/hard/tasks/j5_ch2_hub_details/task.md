# Build the hub, bolt bosses, tang, and pins

Using only Autodesk Fusion's visible user interface, complete the CAD task below. Work in the root component and use millimetres. Do not use scripts, add-ins, the Fusion API, a terminal, or another CAD program.

This is a multi-stage build with 15 stages completed in one episode. Work strictly in the document that is already open: do not create a new document and do not open or import any file—work done in a different document scores zero. Complete the stages in order; each stage builds on the result of the previous one. Do not add solid features beyond those specified.

## Required result

### Stage 1 of 15

Starting from the supplied body, hide the bodies in the browser and create a sketch on the lip face plane at Z = 42. Draw exactly one circle dimensioned to Ø84 mm centered on the Z axis. The finished sketch must yield two selectable profiles. Finish the sketch without extruding it.

### Stage 2 of 15

Continuing from the previous stage, using the Ø70 mm circle sketch, extrude its single profile by 3 mm in the global positive-Z direction, so the hub spans Z = 49 to Z = 52. Use a one-sided extrusion, 0° taper, and Join. Add no other feature.

### Stage 3 of 15

Continuing from the previous stage, using the body, create a sketch on the top disk face at Z = 49. Draw exactly one circle dimensioned to Ø70 mm centered on the Z axis. Finish the sketch without extruding it.

### Stage 4 of 15

Continuing from the previous stage, using the Ø70 mm circle sketch, extrude its single profile by 3 mm in the global positive-Z direction, so the hub spans Z = 49 to Z = 52. Use a one-sided extrusion, 0° taper, and Join. Add no other feature.

### Stage 5 of 15

Continuing from the previous stage, using the body, create a sketch on the top disk face at Z = 49. Draw exactly one circle dimensioned to Ø70 mm centered on the Z axis. Finish the sketch without extruding it.

### Stage 6 of 15

Continuing from the previous stage, using the bolt-boss sketch, select the annular region between the Ø3 mm and Ø4.5 mm circles — the radial line splits it into two half-ring profiles, so select both — and extrude it 1 mm in the global positive-Z direction, to Z = 50. Use a one-sided extrusion, 0° taper, and Join. Add no other feature.

### Stage 7 of 15

Continuing from the previous stage, using the single bolt-boss detail, create a Circular Pattern of that extrusion feature around the global Z axis. Use Full distribution over 360°, quantity 16, and Identical compute type, placing bosses every 22.5° on the Ø77 bolt circle (radius 38.5). Pattern the feature, not sketch geometry or faces, and add no other feature.

### Stage 8 of 15

Continuing from the previous stage, using the body, create a sketch on the bottom disk face at Z = 0. Draw a center rectangle with diagonals, centered on the origin, dimensioned 24 mm along X and 40 mm along Y (corners at X = ±12, Y = ±20). Finish the sketch without extruding it.

### Stage 9 of 15

Continuing from the previous stage, using the 24 × 40 mm rectangle sketch, extrude its single profile by 42 mm in the global negative-Z direction, so the tang spans Z = 0 to Z = −42. Use a one-sided extrusion, 0° taper, and Join. Add no other feature.

### Stage 10 of 15

Continuing from the previous stage, using the body, create a sketch on the tang side face at X = −12. Draw exactly one circle dimensioned to Ø40 mm centered at global (−12, 0, −42), the tang end. Finish the sketch without extruding it.

### Stage 11 of 15

Continuing from the previous stage, using the Ø40 mm circle sketch, extrude its single profile −24 mm through the tang (from X = −12 to X = +12) with 0° taper and Join, forming the rounded Ø40 knob at the tang end. Add no other feature.

### Stage 12 of 15

Continuing from the previous stage, using the body, create a sketch on the tang side face at X = −12. Draw exactly one circle dimensioned to Ø20 mm, placed near the knob center — its final center is at global (−12, 0, −40), 2 mm above the Ø40 knob center. Finish the sketch without extruding it.

### Stage 13 of 15

Continuing from the previous stage, using the Ø20 mm circle sketch, extrude its single profile by 10 mm in the global negative-X direction, so the pin spans X = −12 to X = −22. Use a one-sided extrusion, 0° taper, and Join. Add no other feature.

### Stage 14 of 15

Continuing from the previous stage, using the body, create a sketch on the hub face at Z = 52. Draw exactly one circle at the face center (0, 0, 52) and type its diameter as 20 mm. Finish the sketch without extruding it.

### Stage 15 of 15

Continuing from the previous stage, using the Ø20 mm circle sketch, extrude its single profile by 10 mm in the global positive-Z direction, so the stud spans Z = 52 to Z = 62. Use a one-sided extrusion, 0° taper, and Join. This completes the Jaw_5 geometry: 24 timeline features, one solid body, bounding box X ±42, Y ±37, Z −62..+62. Add no other feature.

End state across all stages: exactly 7 new sketches, 7 new extrusion or revolve features, 1 circular pattern feature, and one solid body.

## Completion requirements

Finish the sketch and feature operations, leave the completed design open in Fusion, and do not add geometry or features not requested above. Do not use Save or Save As. Do not open or import any external CAD file, including another task seed or answer. The environment exports the open design automatically; use the finish action when the task is complete.
