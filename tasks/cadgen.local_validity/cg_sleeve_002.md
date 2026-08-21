# Plain sleeve (annular ring)

Model a hollow cylindrical sleeve as a single solid in cadquery with these exact dimensions (mm):
- Outer diameter 80, coaxial through bore of diameter 50, height 25 along Z.
- Centered on the origin in the XY plane, base face at z=0; no chamfers, fillets or other features.

Hard-code all parameters (no randomness), use only the cadquery library, and export the final single solid to the current working directory as part.step (e.g. cq.exporters.export(shape, "part.step")).

Grading is fully local and reproducible: part.step must parse and yield a B-Rep valid solid with positive volume; re-running your script must reproduce the same artifact (volume/bounding box within 1e-6 relative); volume and the three bounding-box edge lengths must match the reference within 1% relative; interface checks: exactly 1 cylindrical face of radius 40 (outer) and exactly 1 cylindrical face of radius 25 (bore); total face count must match exactly.

Respond with a single ```python code block and nothing else.
