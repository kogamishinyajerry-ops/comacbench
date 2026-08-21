# Stepped shaft with central bore

Model a stepped shaft as a single solid in cadquery with these exact dimensions (mm):
- Three coaxial cylindrical segments stacked along +Z, all centered on the Z axis:
- Segment 1: diameter 60, from z=0 to z=40
- Segment 2: diameter 44, from z=40 to z=68
- Segment 3: diameter 30, from z=68 to z=93
- Central through bore of diameter 12, coaxial along Z, through the full length.
- No chamfers, fillets or other features.

Hard-code all parameters (no randomness), use only the cadquery library, and export the final single solid to the current working directory as part.step (e.g. cq.exporters.export(shape, "part.step")).

Grading is fully local and reproducible: part.step must parse and yield a B-Rep valid solid with positive volume; re-running your script must reproduce the same artifact (volume/bounding box within 1e-6 relative); volume and the three bounding-box edge lengths must match the reference within 1% relative; interface checks: exactly 1 cylindrical face of radius 6 (bore)  and exactly 1 cylindrical face of each radius 30, 22, 15 (shaft steps); total face count must match exactly.

Respond with a single ```python code block and nothing else.
