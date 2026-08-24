# Build the gusset, trim it, and cut both holes

Complete the CAD task below in Autodesk Fusion. You may build the geometry with the normal Fusion user interface, or by writing Fusion 360 Python API (adsk) code and executing it in Fusion's Text Commands palette (open it from the View menu if hidden, and make sure the input mode toggle at the bottom right of the palette is set to Py, not Txt), or any combination of both. Work in the root component and use millimetres. Do not use a terminal outside Fusion and do not open or import any external CAD file.

This is a multi-stage build with 4 stages completed in one episode. Work strictly in the document that is already open: do not create a new document and do not open or import any file—work done in a different document scores zero. Complete the stages in order; each stage builds on the result of the previous one. Do not add solid features beyond those specified.

## Required result

### Stage 1 of 4

Starting from the supplied joined lower support, create a fully constrained sketch on the support's axial end face at global X = 70 mm, perpendicular to the main X axis. Use the existing straight support edge between the exposed upper housing/support corner and the exposed lower support corner as the closing chord; do not assign an invented chord length. From the upper corner, draw a 25 mm top segment in the support-face horizontal direction, then connect its far endpoint to the existing lower corner with a minor R55 mm arc bulging outward. Finish the resulting closed curved gusset profile, then extrude that profile 40 mm in the negative X direction using a one-sided −40 mm distance, 0° taper, and Join. Stop before the trimming cut (that is the next stage), with exactly one new sketch, one new extrusion feature, and one solid body.

### Stage 2 of 4

Trim the lower support region outside the curved gusset: reuse the gusset sketch from the previous stage—select the remaining closed region between the gusset arc and the support outline (the lower region you did not extrude)—and extrude-cut it 40 mm in the negative X direction, one-sided −40 mm distance, 0° taper, operation Cut. Do not create a new sketch. The cut removes the support material outside the curved gusset so the support's end matches the gusset profile. This stage adds exactly one new cut feature and no sketch, keeping a single solid body.

### Stage 3 of 4

With the side disk and trimmed support complete, create a fully constrained sketch on the positive-Z outer planar face of the Ø85 mm side disk at global Z = 48 mm. Draw exactly one Ø30 mm circle concentric with the disk at global X = 50 mm and Y = −45 mm. Finish the sketch, then extrude-cut that profile 20 mm in the negative Z direction using a one-sided −20 mm distance and 0° taper. Do not use Through All and do not create the axial end-flange hole yet—that is the final stage. This stage adds exactly one new sketch and one new cut feature, keeping a single solid body.

### Stage 4 of 4

With the side-disk cut complete, create a fully constrained sketch on the exposed axial end face of the final Ø62 mm flange at global X = 296 mm. Draw exactly one Ø30 mm circle concentric with the main X axis and coincident with the end-face center. Finish the sketch, then extrude-cut that profile 20 mm in the negative X direction using a one-sided −20 mm distance and 0° taper. This must create the separate axial end-flange hole; do not add a second sketch or cut on the side disk. This stage adds exactly one new sketch and one new cut feature, keeping a single solid body.

End state across all stages: exactly 3 new sketches, 4 new extrusion or cut features, and one solid body.

## Completion requirements

Finish the sketch and feature operations, leave the completed design open in Fusion, and do not add geometry or features not requested above. Do not use Save or Save As. Do not open or import any external CAD file, including another task seed or answer. The environment exports the open design automatically; use the finish action when the task is complete.
