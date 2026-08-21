# Stepped shaft with central bore

Model a stepped shaft as a single solid in cadquery with these exact dimensions (mm):
- Three coaxial cylindrical segments stacked along +Z, all centered on the Z axis:
- Segment 1: diameter 36, from z=0 to z=25
- Segment 2: diameter 24, from z=25 to z=55
- Segment 3: diameter 14, from z=55 to z=73
- Central through bore of diameter 6, coaxial along Z, through the full length.
- No chamfers, fillets or other features.

Hard-code all parameters (no randomness), use only the cadquery library, and export the final single solid to the current working directory as part.step (e.g. cq.exporters.export(shape, "part.step")).

Grading is fully local and reproducible: part.step must parse and yield a B-Rep valid solid with positive volume; re-running your script must reproduce the same artifact (volume/bounding box within 1e-6 relative); volume and the three bounding-box edge lengths must match the reference within 1% relative; interface checks: exactly 1 cylindrical face of radius 3 (bore)  and exactly 1 cylindrical face of each radius 18, 12, 7 (shaft steps); total face count must match exactly.

Respond with a single ```python code block and nothing else.
