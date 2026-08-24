# Pattern the bolt detail and build the keyed shaft

Complete the CAD task below in Autodesk Fusion. You may build the geometry with the normal Fusion user interface, or by writing Fusion 360 Python API (adsk) code and executing it in Fusion's Text Commands palette (open it from the View menu if hidden, and make sure the input mode toggle at the bottom right of the palette is set to Py, not Txt), or any combination of both. Work in the root component and use millimetres. Do not use a terminal outside Fusion and do not open or import any external CAD file.

This is a multi-stage build with 3 stages completed in one episode. Work strictly in the document that is already open: do not create a new document and do not open or import any file—work done in a different document scores zero. Complete the stages in order; each stage builds on the result of the previous one. Do not add solid features beyond those specified.

## Required result

### Stage 1 of 3

Starting from the supplied Ø62 mm terminal face, create a fully constrained sketch on that face. On the positive horizontal sketch axis, place the center of a Ø5 mm circle exactly 27 mm from the shaft center. Offset that circle inward by 1 mm using a −1 mm sketch offset, producing a concentric Ø3 mm circle. Finish the sketch, then select only the annulus between Ø3 mm and Ø5 mm and extrude it 1 mm outward in the positive X direction with a one-sided 0° Join extrusion. Do not extrude the inner disk and do not create a pattern in this stage—the circular pattern is the next stage. This stage adds exactly one new sketch and one new extrusion feature, keeping a single solid body.

### Stage 2 of 3

Create a circular pattern of the raised annular bolt detail: use a feature circular pattern (pattern the extrusion feature itself, not sketch geometry or faces), select the 1 mm annular pad from the previous stage, set the pattern axis to the main shaft axis (the X axis), quantity 12, full 360° distribution with equal spacing. The result is twelve identical raised annular details arranged around the shaft's terminal face. This stage adds exactly one circular pattern feature and nothing else, keeping a single solid body.

### Stage 3 of 3

On the patterned terminal face from the previous stage, create one fully constrained, centered shaft-profile sketch. In global YZ coordinates, draw straight side segments at Z = −16 mm and Z = +16 mm, each extending from Y = −17 mm to Y = +17 mm. Connect the upper endpoints with a minor R22 mm arc bulging toward positive Y and the lower endpoints with a separate minor R22 mm arc bulging toward negative Y. Keep one closed profile with no center divider. Finish the sketch, then extrude that profile 100 mm outward in the positive X direction, one-sided, with 0° taper and Join. This stage ends with two distinct R22 curved shaft faces, adding exactly one new sketch and one new extrusion feature, keeping a single solid body.

End state across all stages: exactly 2 new sketches, 2 new extrusion or cut features, one circular pattern feature, and one solid body.

## Completion requirements

Finish the sketch and feature operations, leave the completed design open in Fusion, and do not add geometry or features not requested above. Do not use Save or Save As. Do not open or import any external CAD file, including another task seed or answer. The environment exports the open design automatically; use the finish action when the task is complete.
