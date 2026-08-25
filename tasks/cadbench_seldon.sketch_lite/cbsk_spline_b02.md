# Closed profile with fitted spline — 2D sketch (XZ plane, mm)

All coordinates are LOCAL sketch coordinates in millimetres. Establish exact values numerically (do not approximate on a grid).

## Required entities

1. Line from (32, 0) to (2, -17).
2. Line from (2, -17) to (-32, 0).
3. Fitted spline through these fit points in order: (-32, 0), (-19, 24), (-4, 31), (12, 26), (24, 12), (32, 0). Use a smooth interpolation through the points (no kinks); a cadquery `cq.Edge.makeSpline([...])` through the mapped points is acceptable.

## Completion requirements
- Exactly 3 curve entities total.
- The entities must form exactly 1 closed profile(s) (closed loop).
- All entities coplanar on the specified plane.
- Junctions coincident so the profile closes exactly once.

## Deliverable contract

Respond with ONE complete ```python code block (cadquery only, deterministic,
self-contained, no randomness, no other files). The script must:

1. Build the sketch on cadquery plane "XZ" — construct points via
   `P = cq.Plane.named("XZ"); P.toWorldCoords((u, v))` so the LOCAL sketch
   coordinates below map to global (x, y, z) = (u, 0, v)  [local u -> global +X, v -> global +Z].
2. Create EXACTLY the listed curve entities and nothing else (no extra curves,
   points, construction geometry, solids, or bodies).
3. Export the curves as a compound of edges to a file named exactly
   `sketch.step` in the current directory:
   `cq.exporters.export(cq.Compound.makeCompound(edges), "sketch.step")`.
