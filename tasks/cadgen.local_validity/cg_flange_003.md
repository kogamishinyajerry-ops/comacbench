# Circular flange with bolt-hole ring

Model a circular flange as a single solid in cadquery with these exact dimensions (mm):
- Flange disc: outer diameter 140, thickness 10, axis along Z, centered on the origin in the XY plane, base face at z=0.
- Bolt holes: 12 through holes of diameter 8 on a bolt-circle diameter (PCD) of 116, evenly spaced with the first hole on the +X axis, hole axes parallel to Z, through the full thickness.
- No fillets, chamfers, counterbores or any other features.

Hard-code all parameters (no randomness), use only the cadquery library, and export the final single solid to the current working directory as part.step (e.g. cq.exporters.export(shape, "part.step")).

Grading is fully local and reproducible: part.step must parse and yield a B-Rep valid solid with positive volume; re-running your script must reproduce the same artifact (volume/bounding box within 1e-6 relative); volume and the three bounding-box edge lengths must match the reference within 1% relative; interface checks: exactly 12 cylindrical faces of radius 4 (bolt holes) and exactly 1 cylindrical face of radius 70 (rim); total face count must match exactly.

Respond with a single ```python code block and nothing else.
