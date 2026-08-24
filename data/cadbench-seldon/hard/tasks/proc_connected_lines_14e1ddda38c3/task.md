# Draw an open 4-segment orthogonal chain

Using only Autodesk Fusion's visible user interface, complete the sketch task below. Work in the root component and use millimetres. Do not use scripts, add-ins, the API, or any external CAD program.

## Starting state

The supplied design is a clean parametric design in millimetres. It contains only the root component and Origin; it has no sketches, components, features, construction planes, or bodies.

## Required result

Create exactly one new 2D sketch on the YZ origin plane. Select that plane directly from the Origin folder when Fusion asks for the sketch plane.

All coordinates below are local sketch coordinates in millimetres. X and Y refer to the axes displayed while editing the sketch, viewed normal to the selected sketch plane. They describe the required final geometry: establish them with dimensions and geometric constraints rather than relying on visual grid placement. Unless a requirement names a particular operation or constraint, any visible-UI construction sequence that produces the same final geometry is acceptable.

1. Draw a regular, non-construction line from (-13, -19) mm to (-32, -19) mm.
2. Draw a regular, non-construction line from (-32, -19) mm to (-32, -37) mm.
3. Draw a regular, non-construction line from (-32, -37) mm to (-43, -37) mm.
4. Draw a regular, non-construction line from (-43, -37) mm to (-43, -49) mm.

## Constraints and design intent

- Connect these points in order: (-13, -19) mm, (-32, -19) mm, (-32, -37) mm, (-43, -37) mm, (-43, -49) mm.
- Every consecutive pair must share one truly coincident endpoint.
- Keep exactly 4 regular line entities and leave the chain open.
- The finished sketch must report that it is fully constrained. Use dimensions and geometric constraints as needed while preserving the exact geometry above.

## Completion requirements

- The final design must contain exactly 1 sketch and 0 solid or surface bodies.
- The requested geometry must produce exactly 0 closed sketch profiles.
- Use regular sketch geometry unless an entity is explicitly described as construction geometry.
- Do not add extra sketches, curves, points, projected geometry, text, components, features, or bodies.
- Finish the sketch and leave the completed design open in Fusion.

Recommended interaction budget: 82 steps and 300 seconds.

Do not use Save or Save As. Do not open or import any external CAD file, including another task seed or answer. The environment exports the open design automatically; use the finish action when the task is complete.
