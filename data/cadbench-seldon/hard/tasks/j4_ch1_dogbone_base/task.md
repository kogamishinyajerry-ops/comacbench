# Build the disc base and dogbone link

Using only Autodesk Fusion's visible user interface, complete the CAD task below. Work in the root component and use millimetres. Do not use scripts, add-ins, the Fusion API, a terminal, or another CAD program.

This is a multi-stage build with 5 stages completed in one episode. Work strictly in the document that is already open: do not create a new document and do not open or import any file—work done in a different document scores zero. Complete the stages in order; each stage builds on the result of the previous one. Do not add solid features beyond those specified.

## Required result

### Stage 1 of 5

In the empty millimetre design that is already open (do not create a new document), create and finish one fully constrained sketch on the YZ origin plane. Draw exactly one circle with its center coincident with the sketch origin at global (0, 0, 0) and set its diameter to 55 mm. Finish the sketch without creating a solid.

### Stage 2 of 5

Continuing from the previous stage, using the Ø55 mm circle sketch, extrude its single circular profile 5 mm in the global positive-X direction so the disc spans X = 0 to X = 5. Use a one-sided extrusion, 0° taper, and New Body. Do not add any other feature.

### Stage 3 of 5

Continuing from the previous stage, using the Ø55 × 5 mm disc, create exactly one construction plane using the Offset method with the XY origin plane as reference and an offset distance of −27.5 mm, so the plane lies at global Z = −27.5. Do not create a sketch or solid feature.

### Stage 4 of 5

Continuing from the previous stage, using the disc and offset plane, create a sketch on the offset plane at Z = −27.5 containing a closed dogbone/link profile whose axis runs along the global X axis at Y = 0, built in the following sub-steps. Finish the sketch without extruding it.

#### Step 4.1 — Link Outline and Anchor Dimensions

*(video 235.8–355 s)*

Create the sketch on the plane at Z = −27.5. Draw the link outline segments along the X axis and apply the anchor dimensions: 150 mm overall length from the origin to the far end at X = −150, 23 mm from the origin to the left circle center at (−23, 0), and 40 mm for the right end radius about (−110, 0). An auxiliary 27.5 mm dimension is also placed.

#### Step 4.2 — End Circles

*(video 355–448 s)*

Draw the two end circles of the link: the left circle centered at global (−23, 0) over the disc, whose diameter is left undimensioned and resolves to approximately Ø71.7, and the right circle of radius 40 mm centered at global (−110, 0) at the far end.

#### Step 4.3 — Upper Tangent Arc

*(video 448–490 s)*

Using the Three-Point Arc tool, draw one arc of radius 85 mm along the positive-Y side connecting the two ends, and dimension it to R85. Its center resolves to global (−60.64, +114.84).

#### Step 4.4 — Tangent Constraint and Mirror

*(video 537–572 s)*

Apply the tangent constraint, then mirror the R85 arc across the link axis with the sketch Mirror command so a matching arc (center (−60.64, −114.84)) closes the negative-Y side.

#### Step 4.5 — Cleanup and Finish

*(video 585–762.9 s)*

Delete the leftover arc segments so only the closed dogbone boundary remains, and finish the sketch. The finished profile is bounded by X = −150 to X ≈ +12.9, with the R40 right end at (−110, 0) and the ~Ø71.7 left end at (−23, 0).

### Stage 5 of 5

Continuing from the previous stage, using the dogbone sketch, select all 6 profiles and extrude them together 15 mm in the global positive-Z direction, so the plate spans Z = −27.5 to Z = −12.5. Use a one-sided extrusion, 0° taper, and Join. Do not add any other feature.

End state across all stages: exactly 2 new sketches, 2 new extrusion or revolve features, 1 construction plane feature, and one solid body.

## Completion requirements

Finish the sketch and feature operations, leave the completed design open in Fusion, and do not add geometry or features not requested above. Do not use Save or Save As. Do not open or import any external CAD file, including another task seed or answer. The environment exports the open design automatically; use the finish action when the task is complete.
