# L-bracket with inner fillet and leg holes

Model an L-angle bracket as a single solid in cadquery with these exact dimensions (mm):
- Horizontal leg: length 80 along +X (x from 0 to 80), thickness 10 (z from 0 to 10).
- Vertical leg: height 60 along +Z (z from 0 to 60), thickness 10 (x from 0 to 10).
- Both legs share width 40 along +Y (y from 0 to 40); outer corners sharp.
- Inner concave fillet of radius 12 where the two legs meet (tangent to the top face of the horizontal leg and to the inner face of the vertical leg).
- One through hole of diameter 9 in each leg: horizontal-leg hole axis parallel to Z centered at (x=45, y=20); vertical-leg hole axis parallel to X centered at (y=20, z=35).
- No other features.

Hard-code all parameters (no randomness), use only the cadquery library, and export the final single solid to the current working directory as part.step (e.g. cq.exporters.export(shape, "part.step")).

Grading is fully local and reproducible: part.step must parse and yield a B-Rep valid solid with positive volume; re-running your script must reproduce the same artifact (volume/bounding box within 1e-6 relative); volume and the three bounding-box edge lengths must match the reference within 1% relative; interface checks: exactly 2 cylindrical faces of radius 4.5 (leg holes) and exactly 1 cylindrical face of radius 12 (inner fillet); total face count must match exactly.

Respond with a single ```python code block and nothing else.
