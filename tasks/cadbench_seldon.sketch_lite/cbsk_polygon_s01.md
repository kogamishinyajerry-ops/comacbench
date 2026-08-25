# Regular polygon — 2D sketch (YZ plane, mm)

_Vertex coordinates above are derived from the authoritative parameters: regular polygon, given center, circumradius, side count, first-vertex angle (counterclockwise from local +X)._
All coordinates are LOCAL sketch coordinates in millimetres. Establish exact values numerically (do not approximate on a grid).

## Required entities

1. Line from (3.520908, -10.571057) to (15.692446, 3.186364).
2. Line from (15.692446, 3.186364) to (14.571057, 21.520908).
3. Line from (14.571057, 21.520908) to (0.813636, 33.692446).
4. Line from (0.813636, 33.692446) to (-17.520908, 32.571057).
5. Line from (-17.520908, 32.571057) to (-29.692446, 18.813636).
6. Line from (-29.692446, 18.813636) to (-28.571057, 0.479092).
7. Line from (-28.571057, 0.479092) to (-14.813636, -11.692446).
8. Line from (-14.813636, -11.692446) to (3.520908, -10.571057).

## Completion requirements
- Exactly 8 curve entities total.
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
