# Draw a regular 8-sided polygon

Using only Autodesk Fusion's visible user interface, complete the sketch task below. Work in the root component and use millimetres. Do not use scripts, add-ins, the API, or any external CAD program.

## Starting state

The supplied design is a clean parametric design in millimetres. It contains only the root component and Origin; it has no sketches, components, features, construction planes, or bodies.

## Required result

Create exactly one new 2D sketch on the YZ origin plane. Select that plane directly from the Origin folder when Fusion asks for the sketch plane.

All coordinates below are local sketch coordinates in millimetres. X and Y refer to the axes displayed while editing the sketch, viewed normal to the selected sketch plane. They describe the required final geometry: establish them with dimensions and geometric constraints rather than relying on visual grid placement. Unless a requirement names a particular operation or constraint, any visible-UI construction sequence that produces the same final geometry is acceptable.

1. Draw a regular, non-construction line from (3.520908, -10.571057) mm to (15.692446, 3.186364) mm.
2. Draw a regular, non-construction line from (15.692446, 3.186364) mm to (14.571057, 21.520908) mm.
3. Draw a regular, non-construction line from (14.571057, 21.520908) mm to (0.813636, 33.692446) mm.
4. Draw a regular, non-construction line from (0.813636, 33.692446) mm to (-17.520908, 32.571057) mm.
5. Draw a regular, non-construction line from (-17.520908, 32.571057) mm to (-29.692446, 18.813636) mm.
6. Draw a regular, non-construction line from (-29.692446, 18.813636) mm to (-28.571057, 0.479092) mm.
7. Draw a regular, non-construction line from (-28.571057, 0.479092) mm to (-14.813636, -11.692446) mm.
8. Draw a regular, non-construction line from (-14.813636, -11.692446) mm to (3.520908, -10.571057) mm.

## Constraints and design intent

- Use Fusion's regular polygon geometry with exactly 8 perimeter sides.
- Make the center exactly (-7, 11) mm and the circumradius exactly 24 mm.
- Place the first radial vertex at an angle of exactly 296 degrees counterclockwise from the positive sketch X axis.
- The center, circumradius, side count, and orientation are authoritative; displayed vertex decimals are derived values.
- The finished sketch must report that it is fully constrained. Use dimensions and geometric constraints as needed while preserving the exact geometry above.

## Completion requirements

- The final design must contain exactly 1 sketch and 0 solid or surface bodies.
- The requested geometry must produce exactly 1 closed sketch profile.
- Use regular sketch geometry unless an entity is explicitly described as construction geometry.
- Do not add extra sketches, curves, points, projected geometry, text, components, features, or bodies.
- Finish the sketch and leave the completed design open in Fusion.

Recommended interaction budget: 103 steps and 300 seconds.

Do not use Save or Save As. Do not open or import any external CAD file, including another task seed or answer. The environment exports the open design automatically; use the finish action when the task is complete.
