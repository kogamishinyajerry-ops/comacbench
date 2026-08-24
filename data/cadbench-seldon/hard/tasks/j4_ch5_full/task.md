# Build the complete Jaw_4 link from a blank design

Using only Autodesk Fusion's visible user interface, complete the CAD task below. Work in the root component and use millimetres. Do not use scripts, add-ins, the Fusion API, a terminal, or another CAD program.

This is a multi-stage build with 28 stages completed in one episode. Work strictly in the document that is already open: do not create a new document and do not open or import any file—work done in a different document scores zero. Complete the stages in order; each stage builds on the result of the previous one. Do not add solid features beyond those specified.

## Required result

### Stage 1 of 28

In the empty millimetre design that is already open (do not create a new document), create and finish one fully constrained sketch on the YZ origin plane. Draw exactly one circle with its center coincident with the sketch origin at global (0, 0, 0) and set its diameter to 55 mm. Finish the sketch without creating a solid.

### Stage 2 of 28

Continuing from the previous stage, using the Ø55 mm circle sketch, extrude its single circular profile 5 mm in the global positive-X direction so the disc spans X = 0 to X = 5. Use a one-sided extrusion, 0° taper, and New Body. Do not add any other feature.

### Stage 3 of 28

Continuing from the previous stage, using the Ø55 × 5 mm disc, create exactly one construction plane using the Offset method with the XY origin plane as reference and an offset distance of −27.5 mm, so the plane lies at global Z = −27.5. Do not create a sketch or solid feature.

### Stage 4 of 28

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

### Stage 5 of 28

Continuing from the previous stage, using the dogbone sketch, select all 6 profiles and extrude them together 15 mm in the global positive-Z direction, so the plate spans Z = −27.5 to Z = −12.5. Use a one-sided extrusion, 0° taper, and Join. Do not add any other feature.

### Stage 6 of 28

Continuing from the previous stage, using the plate, create a sketch on its lower face at Z = −27.5. Chain-select the outer plate contour and offset it 2.5 mm inward, producing an inner closed loop and two profiles. Finish the sketch without extruding it.

### Stage 7 of 28

Continuing from the previous stage, using the offset sketch, extrude only the inner region by 1 mm in the global negative-Z direction, to Z = −28.5. Use a one-sided extrusion, 0° taper, and Join. Do not extrude the outer rim region and do not add any other feature.

### Stage 8 of 28

Continuing from the previous stage, using the 1 mm plateau, create a sketch on its face at Z = −28.5 and offset the boundary 2.5 mm outward using a −2.5 mm sketch offset. Finish the sketch without extruding it.

### Stage 9 of 28

Continuing from the previous stage, using the stacked plateau, select the plateau face and extrude it 6.5 mm in the global negative-Z direction, to Z = −40, with a taper angle of −65° and Join. Do not add any other feature.

### Stage 10 of 28

Continuing from the previous stage, using the body, create a sketch on the tapered plateau face at Z = −40 containing a keyhole slot profile: one Ø8 mm circle and connecting straight segments dimensioned 5mm going horizontally into the negative X-direction from the top and bottom of the circle. Connect the horizontal lines with a vertical line of length 8mm. The finished sketch must contain two profiles. Finish the sketch without cutting it.

### Stage 11 of 28

Continuing from the previous stage, using the keyhole sketch, select both keyhole profiles and extrude-cut them 6.5 mm into the material (from Z = −40 toward positive Z, recess floor at Z = −33.5) using a one-sided −6.5 mm distance with 0° taper. Use a fixed Distance extent, not Through All, and add no other feature.

### Stage 12 of 28

Continuing from the previous stage, using the keyhole recess, create a sketch on the recess floor at Z = −33.5. Draw one Ø2.5 mm circle centered on the 8mm circle midpoint and offset it 1 mm outward, producing a concentric Ø4.5 mm circle and an annular profile. Finish the sketch without extruding it.

### Stage 13 of 28

Continuing from the previous stage, using the two-circle sketch, select only the annular region between the Ø2.5 mm and Ø4.5 mm circles and extrude it 0.5 mm in the global negative-Z direction, to Z = −34. Use a one-sided extrusion, 0° taper, and Join. Leave the inner disk unextruded and add no other feature.

### Stage 14 of 28

Continuing from the previous stage, using the single keyhole-and-annulus detail, create a Circular Pattern of the two features — the keyhole cut and the annulus extrusion — around the global Z axis through (−110, 0). Use Full distribution over 360°, quantity 7, Identical compute type, and suppress the 2 left-most    instances so 5 remain, centered at (−146, 0), (−132.45, ±28.15) and (−101.99, ±35.10). Pattern the features, not sketch geometry or faces, and add no other feature.

### Stage 15 of 28

Continuing from the previous stage, using the patterned details, create a Pattern on Path. Set Object Type to Faces and select the 8 faces of the boss detail at (−101.99, +35.10), select the positive-Y wavy plate edge as the path, and use quantity 4, distance 89 mm, start point 0, Extent distribution, One Direction, and Path Direction orientation. The added instances land at (−72.70, 26.41), (−41.73, 27.61) and (−15.16, 30.90). Add no other feature.

### Stage 16 of 28

Continuing from the previous stage, using the body, create a sketch on the plate top face at Z = −12.5 containing one straight line across the part that isolates the disc-end region (X greater than −34) as a closed profile against the existing plate boundary. Finish the sketch without extruding it.

### Stage 17 of 28

Continuing from the previous stage, using the body, create exactly one construction plane using the Midplane method between the two parallel flat faces at Z = −27.5 and Z = +27.5 (55 mm apart), giving a plane at Z = 0. Do not create a sketch or solid feature.

### Stage 18 of 28

Continuing from the previous stage, using the body, create a sketch on the plate top face at Z = −12.5 containing one straight line across the part that isolates the disc-end region (X greater than −34) as a closed profile against the existing plate boundary. Finish the sketch without extruding it.

### Stage 19 of 28

Continuing from the previous stage, using the patterned details, create a Pattern on Path. Set Object Type to Faces and select the 8 faces of the boss detail at (−101.99, +35.10), select the positive-Y wavy plate edge as the path, and use quantity 4, distance 89 mm, start point 0, Extent distribution, One Direction, and Path Direction orientation. The added instances land at (−72.70, 26.41), (−41.73, 27.61) and (−15.16, 30.90). Add no other feature.

### Stage 20 of 28

Continuing from the previous stage, using the body, create a sketch on the plate top face at Z = −12.5 containing one straight line across the part that isolates the disc-end region (X greater than −34) as a closed profile against the existing plate boundary. Finish the sketch without extruding it.

### Stage 21 of 28

Continuing from the previous stage, using the boundary sketch, select the single disc-end region and extrude it 40 mm in the global positive-Z direction, so the block spans Z = −12.5 to Z = +27.5. Use a one-sided extrusion, 0° taper, and Join. Add no other feature.

### Stage 22 of 28

Continuing from the previous stage, using the body, create exactly one construction plane using the Midplane method between the two parallel flat faces at Z = −27.5 and Z = +27.5 (55 mm apart), giving a plane at Z = 0. Do not create a sketch or solid feature.

### Stage 23 of 28

Continuing from the previous stage, using the mirrored body, create a second Mirror feature with Object Type set to Faces. Select the 2 counterbore faces on the wavy edge and the same midplane as the mirror plane. Add no other feature.

### Stage 24 of 28

Continuing from the previous stage, using the body, create a sketch on the disc outer face at X = +5. Draw exactly one Ø30 mm circle centered on the global X axis at (5, 0, 0). Finish the sketch without extruding it.

### Stage 25 of 28

Continuing from the previous stage, using the Ø30 mm circle sketch, extrude its single profile by 20 mm in the global positive-X direction, so the stub spans X = 5 to X = 25. Use a one-sided extrusion, 0° taper, and Join. Add no other feature.

### Stage 26 of 28

Continuing from the previous stage, using the body, create a sketch on the disc outer face at X = +5. Draw exactly one Ø30 mm circle centered on the global X axis at (5, 0, 0). Finish the sketch without extruding it.

### Stage 27 of 28

Continuing from the previous stage, using the body, create exactly one construction plane using the Midplane method between the two clevis inner faces at Z = −12.5 and Z = +12.5 (25 mm apart), giving a plane at Z = 0. Do not create a sketch or solid feature.

### Stage 28 of 28

Continuing from the previous stage, using the body and clevis midplane, create a Mirror feature with Object Type set to Features. Select the single Ø20 mm hole-cut feature and the clevis midplane (Z = 0) as the mirror plane, with Identical compute type, so a matching hole spans Z = +12.5 to Z = +22.5 in the opposite clevis face. This completes the Jaw_4 geometry: 31 timeline features, exactly one body, bounding box X −149.8..25, Y ±39.7, Z ±40. Add no other feature.

---

## Part 2 — Jaw_5 (Tasks 29–52)

End state across all stages: exactly 11 new sketches, 10 new extrusion or revolve features, 1 circular pattern feature, 2 path pattern features, 3 mirror features, 4 construction plane features, and one solid body.

## Completion requirements

Finish the sketch and feature operations, leave the completed design open in Fusion, and do not add geometry or features not requested above. Do not use Save or Save As. Do not open or import any external CAD file, including another task seed or answer. The environment exports the open design automatically; use the finish action when the task is complete.
