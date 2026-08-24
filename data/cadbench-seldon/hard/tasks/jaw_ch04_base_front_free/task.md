# Build the housing front end from a blank design

Complete the CAD task below in Autodesk Fusion. You may build the geometry with the normal Fusion user interface, or by writing Fusion 360 Python API (adsk) code and executing it in Fusion's Text Commands palette (open it from the View menu if hidden, and make sure the input mode toggle at the bottom right of the palette is set to Py, not Txt), or any combination of both. Work in the root component and use millimetres. Do not use a terminal outside Fusion and do not open or import any external CAD file.

This is a multi-stage build with 5 stages completed in one episode. Work strictly in the document that is already open: do not create a new document and do not open or import any file—work done in a different document scores zero. Complete the stages in order; each stage builds on the result of the previous one. Do not add solid features beyond those specified.

## Required result

### Stage 1 of 5

In the empty millimetre design that is already open (do not create a new document), create a fully constrained sketch on the YZ (Right) origin plane. Use global coordinates so the horizontal sketch edges lie at Y = +45 mm and Y = −45 mm and extend from Z = −37.5 mm to Z = +37.5 mm. Split each horizontal edge at Z = 0 and keep an ordinary divider along Z = 0 between their midpoints, producing two adjacent closed regions. Connect the two Z = −37.5 mm endpoints with a minor R125 mm arc bulging toward negative Z, and mirror it on the Z = +37.5 mm side. Finish the sketch, then extrude both closed regions together 100 mm in the positive X direction with 0° taper and New Body. This stage produces exactly one fully constrained sketch and one extrusion feature, leaving a single solid body.

### Stage 2 of 5

Extend the housing with a tapered section: select the flat end face of the base extrusion at X = 100 mm and extrude that face directly—without creating any new sketch—35 mm further in the positive X direction with a −15° taper angle, one-sided, Join. The housing must now end at X = 135 mm with inward-sloping side walls. This stage adds exactly one new extrusion feature and no sketch, keeping a single solid body.

### Stage 3 of 5

On the tapered extension you just created, create a fully constrained sketch on the exposed terminal face. Draw exactly one Ø69 mm circle concentric with the main X axis and coincident with the sketch origin. Finish the sketch, then extrude the circle 10 mm outward in the positive X direction, one-sided, with 0° taper and Join. This stage adds exactly one new sketch and one new extrusion feature, keeping a single solid body.

### Stage 4 of 5

On the Ø69 mm boss from the previous stage, create a fully constrained sketch on its exposed terminal face. Draw exactly one Ø62 mm circle concentric with the main X axis and coincident with the sketch origin. Finish the sketch, then extrude the circular profile 30 mm outward in the positive X direction, one-sided, with 0° taper and Join. This stage adds exactly one new sketch and one new extrusion feature, keeping a single solid body.

### Stage 5 of 5

On the exposed Ø62 mm terminal face from the previous stage, create a fully constrained sketch on that face. On the positive horizontal sketch axis, place the center of a Ø5 mm circle exactly 27 mm from the shaft center. Offset that circle inward by 1 mm using a −1 mm sketch offset, producing a concentric Ø3 mm circle. Finish the sketch, then select only the annulus between Ø3 mm and Ø5 mm and extrude it 1 mm outward in the positive X direction with a one-sided 0° Join extrusion. Do not extrude the inner disk and do not create a pattern. This stage adds exactly one new sketch and one new extrusion feature, keeping a single solid body.

End state across all stages: exactly 4 new sketches, 5 new extrusion or cut features, and one solid body.

## Completion requirements

Finish the sketch and feature operations, leave the completed design open in Fusion, and do not add geometry or features not requested above. Do not use Save or Save As. Do not open or import any external CAD file, including another task seed or answer. The environment exports the open design automatically; use the finish action when the task is complete.
