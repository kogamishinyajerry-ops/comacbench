# Build the side-disk assembly on a new construction plane

Complete the CAD task below in Autodesk Fusion. You may build the geometry with the normal Fusion user interface, or by writing Fusion 360 Python API (adsk) code and executing it in Fusion's Text Commands palette (open it from the View menu if hidden, and make sure the input mode toggle at the bottom right of the palette is set to Py, not Txt), or any combination of both. Work in the root component and use millimetres. Do not use a terminal outside Fusion and do not open or import any external CAD file.

This is a multi-stage build with 3 stages completed in one episode. Work strictly in the document that is already open: do not create a new document and do not open or import any file—work done in a different document scores zero. Complete the stages in order; each stage builds on the result of the previous one. Do not add solid features beyond those specified.

## Required result

### Stage 1 of 3

Create a construction plane coincident with the flat positive-Z side face of the original untapered housing—the plane at global Z = 37.5 mm that contains the housing's two long parallel longitudinal edges. Any construction-plane method that produces a plane exactly coincident with that face is acceptable. Add nothing else in this stage: no sketch and no solid feature.

### Stage 2 of 3

On the construction plane you just created, make a fully constrained sketch. Draw exactly one Ø85 mm circle centered at the midpoint of the lower longitudinal edge of the original 100 mm housing section: global X = 50 mm, Y = −45 mm, Z = 37.5 mm. Finish the sketch, then extrude the circular profile symmetrically about that plane by 10.5 mm on each side, for 21 mm total thickness, with 0° taper and Join. The disk must span global Z = 27 mm to Z = 48 mm and remain part of the single body. This stage adds exactly one new sketch and one new extrusion feature.

### Stage 3 of 3

On the Ø85 mm side disk from the previous stage, create a fully constrained sketch on its negative-Z planar face at global Z = 27 mm. Use the existing straight lower housing edge to close the top of one support profile. Place two vertical sketch lines at global X = 30 mm and X = 70 mm, start both on the housing edge at Y = −45 mm, and extend each 30 mm toward negative Y to Y = −75 mm. Connect their lower endpoints with a minor R30 mm arc bulging toward negative Y. Finish the sketch, then extrude that one closed profile 35 mm from Z = 27 mm toward negative Z, ending at Z = −8 mm, with 0° taper and Join. This stage adds exactly one new sketch and one new extrusion feature, keeping a single solid body.

End state across all stages: exactly 2 new sketches, 2 new extrusion or cut features, one construction plane, and one solid body.

## Completion requirements

Finish the sketch and feature operations, leave the completed design open in Fusion, and do not add geometry or features not requested above. Do not use Save or Save As. Do not open or import any external CAD file, including another task seed or answer. The environment exports the open design automatically; use the finish action when the task is complete.
