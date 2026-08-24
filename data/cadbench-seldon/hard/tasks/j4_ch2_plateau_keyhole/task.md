# Build the offset plateaus and keyhole cut

Using only Autodesk Fusion's visible user interface, complete the CAD task below. Work in the root component and use millimetres. Do not use scripts, add-ins, the Fusion API, a terminal, or another CAD program.

This is a multi-stage build with 6 stages completed in one episode. Work strictly in the document that is already open: do not create a new document and do not open or import any file—work done in a different document scores zero. Complete the stages in order; each stage builds on the result of the previous one. Do not add solid features beyond those specified.

## Required result

### Stage 1 of 6

Starting from the supplied plate, create a sketch on its lower face at Z = −27.5. Chain-select the outer plate contour and offset it 2.5 mm inward, producing an inner closed loop and two profiles. Finish the sketch without extruding it.

### Stage 2 of 6

Continuing from the previous stage, using the offset sketch, extrude only the inner region by 1 mm in the global negative-Z direction, to Z = −28.5. Use a one-sided extrusion, 0° taper, and Join. Do not extrude the outer rim region and do not add any other feature.

### Stage 3 of 6

Continuing from the previous stage, using the 1 mm plateau, create a sketch on its face at Z = −28.5 and offset the boundary 2.5 mm outward using a −2.5 mm sketch offset. Finish the sketch without extruding it.

### Stage 4 of 6

Continuing from the previous stage, using the stacked plateau, select the plateau face and extrude it 6.5 mm in the global negative-Z direction, to Z = −40, with a taper angle of −65° and Join. Do not add any other feature.

### Stage 5 of 6

Continuing from the previous stage, using the body, create a sketch on the tapered plateau face at Z = −40 containing a keyhole slot profile: one Ø8 mm circle and connecting straight segments dimensioned 5mm going horizontally into the negative X-direction from the top and bottom of the circle. Connect the horizontal lines with a vertical line of length 8mm. The finished sketch must contain two profiles. Finish the sketch without cutting it.

### Stage 6 of 6

Continuing from the previous stage, using the keyhole sketch, select both keyhole profiles and extrude-cut them 6.5 mm into the material (from Z = −40 toward positive Z, recess floor at Z = −33.5) using a one-sided −6.5 mm distance with 0° taper. Use a fixed Distance extent, not Through All, and add no other feature.

End state across all stages: exactly 3 new sketches, 4 new extrusion or revolve features, and one solid body.

## Completion requirements

Finish the sketch and feature operations, leave the completed design open in Fusion, and do not add geometry or features not requested above. Do not use Save or Save As. Do not open or import any external CAD file, including another task seed or answer. The environment exports the open design automatically; use the finish action when the task is complete.
