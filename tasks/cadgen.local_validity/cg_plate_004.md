# Rectangular plate with corner fillets and bolt holes

Model a rectangular plate as a single solid in cadquery with these exact dimensions (mm):
- Plate: 90 (X) x 70 (Y) x 6 (Z), centered on the origin in XY, base face at z=0, thickness along Z.
- All four vertical (Z-parallel) edges filleted with radius 9.
- Four through holes of diameter 7, axes parallel to Z, through the full thickness, centered at (+/-29, +/-19).
- No other features.

Hard-code all parameters (no randomness), use only the cadquery library, and export the final single solid to the current working directory as part.step (e.g. cq.exporters.export(shape, "part.step")).

Grading is fully local and reproducible: part.step must parse and yield a B-Rep valid solid with positive volume; re-running your script must reproduce the same artifact (volume/bounding box within 1e-6 relative); volume and the three bounding-box edge lengths must match the reference within 1% relative; interface checks: exactly 4 cylindrical faces of radius 3.5 (holes) and exactly 4 cylindrical faces of radius 9 (edge fillets); total face count must match exactly.

Respond with a single ```python code block and nothing else.
