# Complete the back half of the jaw housing

Using only Autodesk Fusion's visible user interface, complete the CAD task below. Work in the root component and use millimetres. Do not use scripts, add-ins, the Fusion API, a terminal, or another CAD program.

This is a multi-stage build with 9 stages completed in one episode. Work strictly in the document that is already open: do not create a new document and do not open or import any file—work done in a different document scores zero. Complete the stages in order; each stage builds on the result of the previous one. Do not add solid features beyond those specified.

## Required result

### Stage 1 of 9

Starting from the supplied Ø62 mm flange whose earlier sketch already contains the corrected inward Ø60 mm offset, create a new fully constrained sketch on the flange's exposed terminal face. Offset the Ø62 mm circular perimeter inward by 1 mm using a −1 mm sketch offset, producing exactly one centered Ø60 mm profile. Finish the sketch, then extrude the central Ø60 mm disk—not the surrounding annulus—1 mm outward in the positive X direction with a one-sided 0° Join extrusion. The result must be a solid raised Ø60 mm disk with no enclosed cavity, exactly one new sketch, one new extrusion feature, and one solid body.

### Stage 2 of 9

On the raised Ø60 mm end face from the previous stage, create a fully constrained sketch on that face. Draw exactly one Ø62 mm circle concentric with the main X axis and coincident with the sketch origin. Finish the sketch. Select both regions inside the Ø62 mm boundary—the central Ø60 mm face and the surrounding Ø60-to-Ø62 mm annulus—and extrude them together 10 mm outward in the positive X direction, one-sided, with 0° taper and Join. The result must be a complete Ø62 mm circular end flange, exactly one new sketch, one new extrusion feature, and one solid body.

### Stage 3 of 9

Create a construction plane coincident with the flat positive-Z side face of the original untapered housing—the plane at global Z = 37.5 mm that contains the housing's two long parallel longitudinal edges. Any construction-plane method that produces a plane exactly coincident with that face is acceptable. Add nothing else in this stage: no sketch and no solid feature.

### Stage 4 of 9

On the construction plane you just created, make a fully constrained sketch. Draw exactly one Ø85 mm circle centered at the midpoint of the lower longitudinal edge of the original 100 mm housing section: global X = 50 mm, Y = −45 mm, Z = 37.5 mm. Finish the sketch, then extrude the circular profile symmetrically about that plane by 10.5 mm on each side, for 21 mm total thickness, with 0° taper and Join. The disk must span global Z = 27 mm to Z = 48 mm and remain part of the single body. This stage adds exactly one new sketch and one new extrusion feature.

### Stage 5 of 9

On the Ø85 mm side disk from the previous stage, create a fully constrained sketch on its negative-Z planar face at global Z = 27 mm. Use the existing straight lower housing edge to close the top of one support profile. Place two vertical sketch lines at global X = 30 mm and X = 70 mm, start both on the housing edge at Y = −45 mm, and extend each 30 mm toward negative Y to Y = −75 mm. Connect their lower endpoints with a minor R30 mm arc bulging toward negative Y. Finish the sketch, then extrude that one closed profile 35 mm from Z = 27 mm toward negative Z, ending at Z = −8 mm, with 0° taper and Join. This stage adds exactly one new sketch and one new extrusion feature, keeping a single solid body.

### Stage 6 of 9

On the joined lower support from the previous stage, create a fully constrained sketch on the support's axial end face at global X = 70 mm, perpendicular to the main X axis. Use the existing straight support edge between the exposed upper housing/support corner and the exposed lower support corner as the closing chord; do not assign an invented chord length. From the upper corner, draw a 25 mm top segment in the support-face horizontal direction, then connect its far endpoint to the existing lower corner with a minor R55 mm arc bulging outward. Finish the resulting closed curved gusset profile, then extrude that profile 40 mm in the negative X direction using a one-sided −40 mm distance, 0° taper, and Join. Stop before the trimming cut (that is the next stage), with exactly one new sketch, one new extrusion feature, and one solid body.

### Stage 7 of 9

Trim the lower support region outside the curved gusset: reuse the gusset sketch from the previous stage—select the remaining closed region between the gusset arc and the support outline (the lower region you did not extrude)—and extrude-cut it 40 mm in the negative X direction, one-sided −40 mm distance, 0° taper, operation Cut. Do not create a new sketch. The cut removes the support material outside the curved gusset so the support's end matches the gusset profile. This stage adds exactly one new cut feature and no sketch, keeping a single solid body.

### Stage 8 of 9

With the side disk and trimmed support complete, create a fully constrained sketch on the positive-Z outer planar face of the Ø85 mm side disk at global Z = 48 mm. Draw exactly one Ø30 mm circle concentric with the disk at global X = 50 mm and Y = −45 mm. Finish the sketch, then extrude-cut that profile 20 mm in the negative Z direction using a one-sided −20 mm distance and 0° taper. Do not use Through All and do not create the axial end-flange hole yet—that is the final stage. This stage adds exactly one new sketch and one new cut feature, keeping a single solid body.

### Stage 9 of 9

With the side-disk cut complete, create a fully constrained sketch on the exposed axial end face of the final Ø62 mm flange at global X = 296 mm. Draw exactly one Ø30 mm circle concentric with the main X axis and coincident with the end-face center. Finish the sketch, then extrude-cut that profile 20 mm in the negative X direction using a one-sided −20 mm distance and 0° taper. This must create the separate axial end-flange hole; do not add a second sketch or cut on the side disk. This stage adds exactly one new sketch and one new cut feature, keeping a single solid body.

End state across all stages: exactly 7 new sketches, 8 new extrusion or cut features, one construction plane, and one solid body.

## Completion requirements

Finish the sketch and feature operations, leave the completed design open in Fusion, and do not add geometry or features not requested above. Do not use Save or Save As. Do not open or import any external CAD file, including another task seed or answer. The environment exports the open design automatically; use the finish action when the task is complete.
