# Build the bolt details and edge patterns

Using only Autodesk Fusion's visible user interface, complete the CAD task below. Work in the root component and use millimetres. Do not use scripts, add-ins, the Fusion API, a terminal, or another CAD program.

This is a multi-stage build with 10 stages completed in one episode. Work strictly in the document that is already open: do not create a new document and do not open or import any file—work done in a different document scores zero. Complete the stages in order; each stage builds on the result of the previous one. Do not add solid features beyond those specified.

## Required result

### Stage 1 of 10

Starting from the supplied keyhole recess, create a sketch on the recess floor at Z = −33.5. Draw one Ø2.5 mm circle centered on the 8mm circle midpoint and offset it 1 mm outward, producing a concentric Ø4.5 mm circle and an annular profile. Finish the sketch without extruding it.

### Stage 2 of 10

Continuing from the previous stage, using the two-circle sketch, select only the annular region between the Ø2.5 mm and Ø4.5 mm circles and extrude it 0.5 mm in the global negative-Z direction, to Z = −34. Use a one-sided extrusion, 0° taper, and Join. Leave the inner disk unextruded and add no other feature.

### Stage 3 of 10

Continuing from the previous stage, using the single keyhole-and-annulus detail, create a Circular Pattern of the two features — the keyhole cut and the annulus extrusion — around the global Z axis through (−110, 0). Use Full distribution over 360°, quantity 7, Identical compute type, and suppress the 2 left-most    instances so 5 remain, centered at (−146, 0), (−132.45, ±28.15) and (−101.99, ±35.10). Pattern the features, not sketch geometry or faces, and add no other feature.

### Stage 4 of 10

Continuing from the previous stage, using the patterned details, create a Pattern on Path. Set Object Type to Faces and select the 8 faces of the boss detail at (−101.99, +35.10), select the positive-Y wavy plate edge as the path, and use quantity 4, distance 89 mm, start point 0, Extent distribution, One Direction, and Path Direction orientation. The added instances land at (−72.70, 26.41), (−41.73, 27.61) and (−15.16, 30.90). Add no other feature.

### Stage 5 of 10

Continuing from the previous stage, using the body, create a sketch on the plate top face at Z = −12.5 containing one straight line across the part that isolates the disc-end region (X greater than −34) as a closed profile against the existing plate boundary. Finish the sketch without extruding it.

### Stage 6 of 10

Continuing from the previous stage, using the body, create exactly one construction plane using the Midplane method between the two parallel flat faces at Z = −27.5 and Z = +27.5 (55 mm apart), giving a plane at Z = 0. Do not create a sketch or solid feature.

### Stage 7 of 10

Continuing from the previous stage, using the body, create a sketch on the plate top face at Z = −12.5 containing one straight line across the part that isolates the disc-end region (X greater than −34) as a closed profile against the existing plate boundary. Finish the sketch without extruding it.

### Stage 8 of 10

Continuing from the previous stage, using the patterned details, create a Pattern on Path. Set Object Type to Faces and select the 8 faces of the boss detail at (−101.99, +35.10), select the positive-Y wavy plate edge as the path, and use quantity 4, distance 89 mm, start point 0, Extent distribution, One Direction, and Path Direction orientation. The added instances land at (−72.70, 26.41), (−41.73, 27.61) and (−15.16, 30.90). Add no other feature.

### Stage 9 of 10

Continuing from the previous stage, using the body, create a sketch on the plate top face at Z = −12.5 containing one straight line across the part that isolates the disc-end region (X greater than −34) as a closed profile against the existing plate boundary. Finish the sketch without extruding it.

### Stage 10 of 10

Continuing from the previous stage, using the boundary sketch, select the single disc-end region and extrude it 40 mm in the global positive-Z direction, so the block spans Z = −12.5 to Z = +27.5. Use a one-sided extrusion, 0° taper, and Join. Add no other feature.

End state across all stages: exactly 4 new sketches, 2 new extrusion or revolve features, 1 circular pattern feature, 2 path pattern features, 1 construction plane feature, and one solid body.

## Completion requirements

Finish the sketch and feature operations, leave the completed design open in Fusion, and do not add geometry or features not requested above. Do not use Save or Save As. Do not open or import any external CAD file, including another task seed or answer. The environment exports the open design automatically; use the finish action when the task is complete.
