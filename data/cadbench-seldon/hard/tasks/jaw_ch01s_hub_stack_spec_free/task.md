# Build the three-feature hub stack

Complete the CAD task below in Autodesk Fusion. You may build the geometry with the normal Fusion user interface, or by writing Fusion 360 Python API (adsk) code and executing it in Fusion's Text Commands palette (open it from the View menu if hidden, and make sure the input mode toggle at the bottom right of the palette is set to Py, not Txt), or any combination of both. Work in the root component and use millimetres. Do not use a terminal outside Fusion and do not open or import any external CAD file.

## Required result

Continue in the document that is already open (work in a different document
scores zero). Starting from the supplied tapered housing, add exactly three
features to the end of the part, in order. Each feature is one fully
constrained sketch on the then-current exposed terminal face plus one
one-sided extrusion in the positive X direction with 0° taper and Join:

1. Boss: Ø69 mm circular boss, 10 mm long, concentric with the main X
   axis.
2. Shaft: Ø62 mm circular shaft, 30 mm long, concentric with the main X
   axis.
3. Bolt detail: an annular pad 1 mm high on the shaft's end face — the
   ring between concentric Ø5 mm and Ø3 mm circles whose common
   center lies on the positive horizontal sketch axis, 27 mm from the shaft
   center. Extrude only the annulus (not the inner disk); no pattern.

End state: exactly three new sketches, three new extrusion features, and one
solid body.

## Completion requirements

Finish the sketch and feature operations, leave the completed design open in Fusion, and do not add geometry or features not requested above. Do not use Save or Save As. Do not open or import any external CAD file, including another task seed or answer. The environment exports the open design automatically; use the finish action when the task is complete.
