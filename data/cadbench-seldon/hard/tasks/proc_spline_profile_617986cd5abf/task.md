# Draw a closed profile with a 4-point fitted spline

Using only Autodesk Fusion's visible user interface, complete the sketch task below. Work in the root component and use millimetres. Do not use scripts, add-ins, the API, or any external CAD program.

## Starting state

The supplied design is a clean parametric design in millimetres. It contains only the root component and Origin; it has no sketches, components, features, construction planes, or bodies.

## Required result

Create exactly one new 2D sketch on the YZ origin plane. Select that plane directly from the Origin folder when Fusion asks for the sketch plane.

All coordinates below are local sketch coordinates in millimetres. X and Y refer to the axes displayed while editing the sketch, viewed normal to the selected sketch plane. They describe the required final geometry: establish them with dimensions and geometric constraints rather than relying on visual grid placement. Unless a requirement names a particular operation or constraint, any visible-UI construction sequence that produces the same final geometry is acceptable.

1. Draw a regular, non-construction fitted spline through these fit points in order: (-34, 0) mm, (-11.333333, 17) mm, (11.333333, 32) mm, (34, 0) mm. Use Fusion's default fitted-spline shape and do not add tangent handles.
2. Draw a regular, non-construction line from (34, 0) mm to (6, -20) mm.
3. Draw a regular, non-construction line from (6, -20) mm to (-34, 0) mm.

## Constraints and design intent

- Create exactly one fitted spline by placing these 4 fit points once and in order: (-34, 0) mm, (-11.333333, 17) mm, (11.333333, 32) mm, (34, 0) mm.
- From the final spline point draw one line to (6, -20) mm and a second line back to the first spline point.
- Do not edit tangent handles, convert the spline type, insert fit points, or drag the generated curve after placement.
- Make the three curve junctions coincident so there is exactly one closed profile.
- Full constraint is not required for this task; do not alter the requested geometry merely to force a fully-constrained status.

## Completion requirements

- The final design must contain exactly 1 sketch and 0 solid or surface bodies.
- The requested geometry must produce exactly 1 closed sketch profile.
- Use regular sketch geometry unless an entity is explicitly described as construction geometry.
- Do not add extra sketches, curves, points, projected geometry, text, components, features, or bodies.
- Finish the sketch and leave the completed design open in Fusion.

Recommended interaction budget: 95 steps and 300 seconds.

Do not use Save or Save As. Do not open or import any external CAD file, including another task seed or answer. The environment exports the open design automatically; use the finish action when the task is complete.
