# Build the complete jaw housing from a blank design

Complete the CAD task below in Autodesk Fusion. You may build the geometry with the normal Fusion user interface, or by writing Fusion 360 Python API (adsk) code and executing it in Fusion's Text Commands palette (open it from the View menu if hidden, and make sure the input mode toggle at the bottom right of the palette is set to Py, not Txt), or any combination of both. Work in the root component and use millimetres. Do not use a terminal outside Fusion and do not open or import any external CAD file.

This is a multi-stage build with 17 stages completed in one episode. Work strictly in the document that is already open: do not create a new document and do not open or import any file—work done in a different document scores zero. Complete the stages in order; each stage builds on the result of the previous one. Do not add solid features beyond those specified.

## Required result

### Stage 1 of 17

In the empty millimetre design that is already open (do not create a new document), create a fully constrained sketch on the YZ (Right) origin plane. Use global coordinates so the horizontal sketch edges lie at Y = +45 mm and Y = −45 mm and extend from Z = −37.5 mm to Z = +37.5 mm. Split each horizontal edge at Z = 0 and keep an ordinary divider along Z = 0 between their midpoints, producing two adjacent closed regions. Connect the two Z = −37.5 mm endpoints with a minor R125 mm arc bulging toward negative Z, and mirror it on the Z = +37.5 mm side. Finish the sketch, then extrude both closed regions together 100 mm in the positive X direction with 0° taper and New Body. This stage produces exactly one fully constrained sketch and one extrusion feature, leaving a single solid body.

### Stage 2 of 17

Extend the housing with a tapered section: select the flat end face of the base extrusion at X = 100 mm and extrude that face directly—without creating any new sketch—35 mm further in the positive X direction with a −15° taper angle, one-sided, Join. The housing must now end at X = 135 mm with inward-sloping side walls. This stage adds exactly one new extrusion feature and no sketch, keeping a single solid body.

### Stage 3 of 17

On the tapered extension you just created, create a fully constrained sketch on the exposed terminal face. Draw exactly one Ø69 mm circle concentric with the main X axis and coincident with the sketch origin. Finish the sketch, then extrude the circle 10 mm outward in the positive X direction, one-sided, with 0° taper and Join. This stage adds exactly one new sketch and one new extrusion feature, keeping a single solid body.

### Stage 4 of 17

On the Ø69 mm boss from the previous stage, create a fully constrained sketch on its exposed terminal face. Draw exactly one Ø62 mm circle concentric with the main X axis and coincident with the sketch origin. Finish the sketch, then extrude the circular profile 30 mm outward in the positive X direction, one-sided, with 0° taper and Join. This stage adds exactly one new sketch and one new extrusion feature, keeping a single solid body.

### Stage 5 of 17

On the exposed Ø62 mm terminal face from the previous stage, create a fully constrained sketch on that face. On the positive horizontal sketch axis, place the center of a Ø5 mm circle exactly 27 mm from the shaft center. Offset that circle inward by 1 mm using a −1 mm sketch offset, producing a concentric Ø3 mm circle. Finish the sketch, then select only the annulus between Ø3 mm and Ø5 mm and extrude it 1 mm outward in the positive X direction with a one-sided 0° Join extrusion. Do not extrude the inner disk and do not create a pattern in this stage—the circular pattern is the next stage. This stage adds exactly one new sketch and one new extrusion feature, keeping a single solid body.

### Stage 6 of 17

Create a circular pattern of the raised annular bolt detail: use a feature circular pattern (pattern the extrusion feature itself, not sketch geometry or faces), select the 1 mm annular pad from the previous stage, set the pattern axis to the main shaft axis (the X axis), quantity 12, full 360° distribution with equal spacing. The result is twelve identical raised annular details arranged around the shaft's terminal face. This stage adds exactly one circular pattern feature and nothing else, keeping a single solid body.

### Stage 7 of 17

On the patterned terminal face from the previous stage, create one fully constrained, centered shaft-profile sketch. In global YZ coordinates, draw straight side segments at Z = −16 mm and Z = +16 mm, each extending from Y = −17 mm to Y = +17 mm. Connect the upper endpoints with a minor R22 mm arc bulging toward positive Y and the lower endpoints with a separate minor R22 mm arc bulging toward negative Y. Keep one closed profile with no center divider. Finish the sketch, then extrude that profile 100 mm outward in the positive X direction, one-sided, with 0° taper and Join. This stage ends with two distinct R22 curved shaft faces, adding exactly one new sketch and one new extrusion feature, keeping a single solid body.

### Stage 8 of 17

On the 100 mm keyed shaft from the previous stage, create a fully constrained sketch on its exposed terminal face. Draw exactly one Ø62 mm circle concentric with the main X axis and coincident with the sketch origin. Finish the sketch. Select both face regions inside the Ø62 mm boundary—the keyed central region and its surrounding region—and extrude them together 10 mm outward in the positive X direction, one-sided, with 0° taper and Join. The result must be one complete Ø62 mm circular flange, one new sketch, one new extrusion feature, and one solid body.

### Stage 9 of 17

On the Ø62 mm flange from the previous stage, create a new fully constrained sketch on the flange's exposed terminal face. Offset the Ø62 mm circular perimeter inward by 1 mm using a −1 mm sketch offset, producing exactly one centered Ø60 mm profile. Finish the sketch, then extrude the central Ø60 mm disk—not the surrounding annulus—1 mm outward in the positive X direction with a one-sided 0° Join extrusion. The result must be a solid raised Ø60 mm disk with no enclosed cavity, exactly one new sketch, one new extrusion feature, and one solid body.

### Stage 10 of 17

On the raised Ø60 mm end face from the previous stage, create a fully constrained sketch on that face. Draw exactly one Ø62 mm circle concentric with the main X axis and coincident with the sketch origin. Finish the sketch. Select both regions inside the Ø62 mm boundary—the central Ø60 mm face and the surrounding Ø60-to-Ø62 mm annulus—and extrude them together 10 mm outward in the positive X direction, one-sided, with 0° taper and Join. The result must be a complete Ø62 mm circular end flange, exactly one new sketch, one new extrusion feature, and one solid body.

### Stage 11 of 17

Create a construction plane coincident with the flat positive-Z side face of the original untapered housing—the plane at global Z = 37.5 mm that contains the housing's two long parallel longitudinal edges. Any construction-plane method that produces a plane exactly coincident with that face is acceptable. Add nothing else in this stage: no sketch and no solid feature.

### Stage 12 of 17

On the construction plane you just created, make a fully constrained sketch. Draw exactly one Ø85 mm circle centered at the midpoint of the lower longitudinal edge of the original 100 mm housing section: global X = 50 mm, Y = −45 mm, Z = 37.5 mm. Finish the sketch, then extrude the circular profile symmetrically about that plane by 10.5 mm on each side, for 21 mm total thickness, with 0° taper and Join. The disk must span global Z = 27 mm to Z = 48 mm and remain part of the single body. This stage adds exactly one new sketch and one new extrusion feature.

### Stage 13 of 17

On the Ø85 mm side disk from the previous stage, create a fully constrained sketch on its negative-Z planar face at global Z = 27 mm. Use the existing straight lower housing edge to close the top of one support profile. Place two vertical sketch lines at global X = 30 mm and X = 70 mm, start both on the housing edge at Y = −45 mm, and extend each 30 mm toward negative Y to Y = −75 mm. Connect their lower endpoints with a minor R30 mm arc bulging toward negative Y. Finish the sketch, then extrude that one closed profile 35 mm from Z = 27 mm toward negative Z, ending at Z = −8 mm, with 0° taper and Join. This stage adds exactly one new sketch and one new extrusion feature, keeping a single solid body.

### Stage 14 of 17

On the joined lower support from the previous stage, create a fully constrained sketch on the support's axial end face at global X = 70 mm, perpendicular to the main X axis. Use the existing straight support edge between the exposed upper housing/support corner and the exposed lower support corner as the closing chord; do not assign an invented chord length. From the upper corner, draw a 25 mm top segment in the support-face horizontal direction, then connect its far endpoint to the existing lower corner with a minor R55 mm arc bulging outward. Finish the resulting closed curved gusset profile, then extrude that profile 40 mm in the negative X direction using a one-sided −40 mm distance, 0° taper, and Join. Stop before the trimming cut (that is the next stage), with exactly one new sketch, one new extrusion feature, and one solid body.

### Stage 15 of 17

Trim the lower support region outside the curved gusset: reuse the gusset sketch from the previous stage—select the remaining closed region between the gusset arc and the support outline (the lower region you did not extrude)—and extrude-cut it 40 mm in the negative X direction, one-sided −40 mm distance, 0° taper, operation Cut. Do not create a new sketch. The cut removes the support material outside the curved gusset so the support's end matches the gusset profile. This stage adds exactly one new cut feature and no sketch, keeping a single solid body.

### Stage 16 of 17

With the side disk and trimmed support complete, create a fully constrained sketch on the positive-Z outer planar face of the Ø85 mm side disk at global Z = 48 mm. Draw exactly one Ø30 mm circle concentric with the disk at global X = 50 mm and Y = −45 mm. Finish the sketch, then extrude-cut that profile 20 mm in the negative Z direction using a one-sided −20 mm distance and 0° taper. Do not use Through All and do not create the axial end-flange hole yet—that is the final stage. This stage adds exactly one new sketch and one new cut feature, keeping a single solid body.

### Stage 17 of 17

With the side-disk cut complete, create a fully constrained sketch on the exposed axial end face of the final Ø62 mm flange at global X = 296 mm. Draw exactly one Ø30 mm circle concentric with the main X axis and coincident with the end-face center. Finish the sketch, then extrude-cut that profile 20 mm in the negative X direction using a one-sided −20 mm distance and 0° taper. This must create the separate axial end-flange hole; do not add a second sketch or cut on the side disk. This stage adds exactly one new sketch and one new cut feature, keeping a single solid body.

End state across all stages: exactly 13 new sketches, 15 new extrusion or cut features, one circular pattern feature, one construction plane, and one solid body.

## Completion requirements

Finish the sketch and feature operations, leave the completed design open in Fusion, and do not add geometry or features not requested above. Do not use Save or Save As. Do not open or import any external CAD file, including another task seed or answer. The environment exports the open design automatically; use the finish action when the task is complete.
