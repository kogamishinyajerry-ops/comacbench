# Regular polygon — 2D sketch (YZ plane, mm)

_Vertex coordinates above are derived from the authoritative parameters: regular polygon, given center, circumradius, side count, first-vertex angle (counterclockwise from local +X)._
All coordinates are LOCAL sketch coordinates in millimetres. Establish exact values numerically (do not approximate on a grid).

## Required entities

1. Line from (17.840885, -5.320644) to (22.182779, 1.116478).
2. Line from (22.182779, 1.116478) to (22.724408, 8.862135).
3. Line from (22.724408, 8.862135) to (19.320644, 15.840885).
4. Line from (19.320644, 15.840885) to (12.883522, 20.182779).
5. Line from (12.883522, 20.182779) to (5.137865, 20.724408).
6. Line from (5.137865, 20.724408) to (-1.840885, 17.320644).
7. Line from (-1.840885, 17.320644) to (-6.182779, 10.883522).
8. Line from (-6.182779, 10.883522) to (-6.724408, 3.137865).
9. Line from (-6.724408, 3.137865) to (-3.320644, -3.840885).
10. Line from (-3.320644, -3.840885) to (3.116478, -8.182779).
11. Line from (3.116478, -8.182779) to (10.862135, -8.724408).
12. Line from (10.862135, -8.724408) to (17.840885, -5.320644).

## Completion requirements
- Exactly 12 curve entities total.
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
