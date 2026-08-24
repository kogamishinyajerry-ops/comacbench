# Build the end block and mirror the features

Using only Autodesk Fusion's visible user interface, complete the CAD task below. Work in the root component and use millimetres. Do not use scripts, add-ins, the Fusion API, a terminal, or another CAD program.

This is a multi-stage build with 7 stages completed in one episode. Work strictly in the document that is already open: do not create a new document and do not open or import any file—work done in a different document scores zero. Complete the stages in order; each stage builds on the result of the previous one. Do not add solid features beyond those specified.

## Required result

### Stage 1 of 7

Starting from the supplied body, create exactly one construction plane using the Midplane method between the two parallel flat faces at Z = −27.5 and Z = +27.5 (55 mm apart), giving a plane at Z = 0. Do not create a sketch or solid feature.

### Stage 2 of 7

Continuing from the previous stage, using the mirrored body, create a second Mirror feature with Object Type set to Faces. Select the 2 counterbore faces on the wavy edge and the same midplane as the mirror plane. Add no other feature.

### Stage 3 of 7

Continuing from the previous stage, using the body, create a sketch on the disc outer face at X = +5. Draw exactly one Ø30 mm circle centered on the global X axis at (5, 0, 0). Finish the sketch without extruding it.

### Stage 4 of 7

Continuing from the previous stage, using the Ø30 mm circle sketch, extrude its single profile by 20 mm in the global positive-X direction, so the stub spans X = 5 to X = 25. Use a one-sided extrusion, 0° taper, and Join. Add no other feature.

### Stage 5 of 7

Continuing from the previous stage, using the body, create a sketch on the disc outer face at X = +5. Draw exactly one Ø30 mm circle centered on the global X axis at (5, 0, 0). Finish the sketch without extruding it.

### Stage 6 of 7

Continuing from the previous stage, using the body, create exactly one construction plane using the Midplane method between the two clevis inner faces at Z = −12.5 and Z = +12.5 (25 mm apart), giving a plane at Z = 0. Do not create a sketch or solid feature.

### Stage 7 of 7

Continuing from the previous stage, using the body and clevis midplane, create a Mirror feature with Object Type set to Features. Select the single Ø20 mm hole-cut feature and the clevis midplane (Z = 0) as the mirror plane, with Identical compute type, so a matching hole spans Z = +12.5 to Z = +22.5 in the opposite clevis face. This completes the Jaw_4 geometry: 31 timeline features, exactly one body, bounding box X −149.8..25, Y ±39.7, Z ±40. Add no other feature.

---

## Part 2 — Jaw_5 (Tasks 29–52)

End state across all stages: exactly 2 new sketches, 2 new extrusion or revolve features, 3 mirror features, 2 construction plane features, and one solid body.

## Completion requirements

Finish the sketch and feature operations, leave the completed design open in Fusion, and do not add geometry or features not requested above. Do not use Save or Save As. Do not open or import any external CAD file, including another task seed or answer. The environment exports the open design automatically; use the finish action when the task is complete.
