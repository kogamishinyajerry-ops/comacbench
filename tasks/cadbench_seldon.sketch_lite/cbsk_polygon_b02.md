# Regular polygon — 2D sketch (YZ plane, mm)

_Vertex coordinates above are derived from the authoritative parameters: regular polygon, given center, circumradius, side count, first-vertex angle (counterclockwise from local +X)._
All coordinates are LOCAL sketch coordinates in millimetres. Establish exact values numerically (do not approximate on a grid).

## Required entities

1. Line from (-38.615146, -15.721934) to (-14.65608, -33.776385).
2. Line from (-14.65608, -33.776385) to (12.959065, -22.054451).
3. Line from (12.959065, -22.054451) to (16.615146, 7.721934).
4. Line from (16.615146, 7.721934) to (-7.34392, 25.776385).
5. Line from (-7.34392, 25.776385) to (-34.959065, 14.054451).
6. Line from (-34.959065, 14.054451) to (-38.615146, -15.721934).

## Completion requirements
- Exactly 6 curve entities total.
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
