# Build the revolved disks and face steps

Using only Autodesk Fusion's visible user interface, complete the CAD task below. Work in the root component and use millimetres. Do not use scripts, add-ins, the Fusion API, a terminal, or another CAD program.

This is a multi-stage build with 9 stages completed in one episode. Work strictly in the document that is already open: do not create a new document and do not open or import any file—work done in a different document scores zero. Complete the stages in order; each stage builds on the result of the previous one. Do not add solid features beyond those specified.

## Required result

### Stage 1 of 9

In the empty millimetre design that is already open (do not create a new document), create and finish one fully constrained sketch on the XZ origin plane. Draw a closed profile whose axis edge lies on the global Z axis from Z = 0 to Z = 20: a 42 mm bottom edge at Z = 0 extending to X = 42, a 35 mm top edge at Z = 20 extending to X = 35, and the outer side closed by a tangent arc of R25 mm. Apply Fix constraints as needed. Finish the sketch without creating a solid.

### Stage 2 of 9

Continuing from the previous stage, using the trapezoid sketch, create a Revolve of its single profile, selecting the profile edge on the global Z axis as the revolve axis. Use Partial extent with a 360° angle, One Side direction, and New Body. The result is a disk of Ø84 spanning Z = 0 to Z = 20 with an R25 rounded rim. Add no other feature.

### Stage 3 of 9

Continuing from the previous stage, using the disk, create a sketch on its top face at Z = 20. Draw exactly one circle of Ø79 mm centered on the Z axis at (0, 0, 20). Finish the sketch without extruding it.

### Stage 4 of 9

Continuing from the previous stage, using the Ø79 mm circle sketch, extrude its single profile by 1 mm in the global positive-Z direction, to Z = 21. Use a one-sided extrusion, 0° taper, and Join. Add no other feature.

### Stage 5 of 9

Continuing from the previous stage, using the disk, create a sketch on its top face at Z = 20. Draw exactly one circle of Ø79 mm centered on the Z axis at (0, 0, 20). Finish the sketch without extruding it.

### Stage 6 of 9

Continuing from the previous stage, using the body, create a sketch on the XZ origin plane containing the profile of a second disk stacked above the first: height 20 mm, radial extents 42 mm and 40 mm, with the outer side closed by a tangent arc of R37 mm. The profile spans Z = 21 to Z = 41 against the existing step. Finish the sketch without creating a solid.

### Stage 7 of 9

Continuing from the previous stage, using the second profile sketch, create a Revolve of its single profile through 360° about the global Z axis with New Body, producing a second Ø84 disk spanning Z = 21 to Z = 41 with an R37 rounded rim, separated from the first disk by the recessed Ø79 step at Z = 20–21. Add no other feature.

### Stage 8 of 9

Continuing from the previous stage, using the twin-disk body, create a sketch on the second disk's top face at Z = 41. Draw exactly one circle of Ø82.5 mm centered on the Z axis. Finish the sketch without extruding it.

### Stage 9 of 9

Continuing from the previous stage, using the Ø82.5 mm circle sketch, extrude its single profile by 1 mm in the global positive-Z direction, to Z = 42. Use a one-sided extrusion, 0° taper, and Join. Add no other feature.

End state across all stages: exactly 5 new sketches, 4 new extrusion or revolve features, and one solid body.

## Completion requirements

Finish the sketch and feature operations, leave the completed design open in Fusion, and do not add geometry or features not requested above. Do not use Save or Save As. Do not open or import any external CAD file, including another task seed or answer. The environment exports the open design automatically; use the finish action when the task is complete.
