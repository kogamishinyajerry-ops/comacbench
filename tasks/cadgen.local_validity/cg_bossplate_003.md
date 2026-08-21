# Base plate with central boss and bolt holes

Model a base plate with a central cylindrical boss as a single solid in cadquery with these exact dimensions (mm):
- Base plate: 80 (X) x 80 (Y) x 8 (Z), centered on the origin in XY, base face at z=0.
- Cylindrical boss on the top face of the plate: diameter 25, height 15, axis along Z centered at the plate center (boss top face at z=23).
- Four through holes in the plate of diameter 7, axes parallel to Z, through the plate thickness only, centered at (+/-28, +/-28).
- No fillets, chamfers or other features.

Hard-code all parameters (no randomness), use only the cadquery library, and export the final single solid to the current working directory as part.step (e.g. cq.exporters.export(shape, "part.step")).

Grading is fully local and reproducible: part.step must parse and yield a B-Rep valid solid with positive volume; re-running your script must reproduce the same artifact (volume/bounding box within 1e-6 relative); volume and the three bounding-box edge lengths must match the reference within 1% relative; interface checks: exactly 4 cylindrical faces of radius 3.5 (bolt holes) and exactly 1 cylindrical face of radius 12.5 (boss); total face count must match exactly.

Respond with a single ```python code block and nothing else.
