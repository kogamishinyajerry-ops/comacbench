# Regular polygon — 2D sketch (YZ plane, mm)

_Vertex coordinates above are derived from the authoritative parameters: regular polygon, given center, circumradius, side count, first-vertex angle (counterclockwise from local +X)._
All coordinates are LOCAL sketch coordinates in millimetres. Establish exact values numerically (do not approximate on a grid).

## Required entities

1. Line from (22.213486, -3.737309) to (5.314143, 8.997259).
2. Line from (5.314143, 8.997259) to (-12.019334, -3.139773).
3. Line from (-12.019334, -3.139773) to (-5.83267, -23.375439).
4. Line from (-5.83267, -23.375439) to (15.324376, -23.744737).
5. Line from (15.324376, -23.744737) to (22.213486, -3.737309).

## Completion requirements
- Exactly 5 curve entities total.
- The entities must form exactly 1 closed profile(s) (closed loop).
- All entities coplanar on the specified plane.

## Deliverable contract

Respond with ONE complete ```python code block (cadquery only, deterministic,
self-contained, no randomness, no other files). The script must:

1. Build the sketch on cadquery plane "YZ" — construct points via
   `P = cq.Plane.named("YZ"); P.toWorldCoords((u, v))` so the LOCAL sketch
   coordinates below map to global (x, y, z) = (0, u, v)  [local u -> global +Y, v -> global +Z].
2. Create EXACTLY the listed curve entities and nothing else (no extra curves,
   points, construction geometry, solids, or bodies).
3. Export the curves as a compound of edges to a file named exactly
   `sketch.step` in the current directory:
   `cq.exporters.export(cq.Compound.makeCompound(edges), "sketch.step")`.
