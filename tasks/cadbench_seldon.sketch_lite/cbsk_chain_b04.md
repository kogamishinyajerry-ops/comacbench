# Open orthogonal line chain — 2D sketch (YZ plane, mm)

All coordinates are LOCAL sketch coordinates in millimetres. Establish exact values numerically (do not approximate on a grid).

## Required entities

1. Line from (-8, -12) to (21, -12).
2. Line from (21, -12) to (21, 5).
3. Line from (21, 5) to (9, 5).
4. Line from (9, 5) to (9, 26).
5. Line from (9, 26) to (31, 26).
6. Line from (31, 26) to (31, 44).
7. Line from (31, 44) to (-3, 44).

## Completion requirements
- Exactly 7 curve entities total.
- The entities must form exactly 0 closed profile(s) (open chain).
- All entities coplanar on the specified plane.
- Consecutive segments share truly coincident endpoints; leave the chain open.

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
