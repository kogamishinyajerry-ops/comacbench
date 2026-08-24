# Build the complete curved two-socket Jaw linkage

Using only Autodesk Fusion's visible user interface, build the complete mechanical linkage described below. Work in the root component and use millimetres. Do not use scripts, add-ins, the Fusion API, a terminal, code, or another CAD program.

## Starting state

The supplied design is a clean parametric design in millimetres. It contains only the root component and Origin; it has no sketches, components, construction planes, features, or bodies.

## Coordinate system and overall result

Create one continuous solid body with three functional regions: a large primary socket end, a smooth curved bridge, and a smaller secondary socket end. These are regions of one joined part, not three separate components or bodies. Both socket axes are parallel to the global Y axis. Place the primary socket axis at global (X, Z) = (0, 0) mm and the secondary socket axis at global (X, Z) = (-350, 0) mm, giving exactly 350 mm center-to-center spacing.

The completed part should occupy approximately X = -385 to 57.5 mm, Y = -20 to 51 mm, and Z = -57.5 to 62.5 mm. Small deviations caused by reasonable blends are acceptable, but preserve the two socket locations, their diameters, and the overall proportions.

## Primary socket end

1. Create a concentric circular base flange with an outside diameter of 115 mm and a nominal axial thickness of 12 mm.
2. Add the raised primary cylindrical housing with a 90 mm outside diameter and 30 mm height above the flange.
3. Form the upper stepped collar with approximately 60 mm outside diameter and 54 mm inside diameter.
4. Create a central cylindrical opening of exactly 30 mm diameter along the global Y axis.
5. Give the socket opening a rounded internal seat and a smooth rounded lip comparable to a revolved bearing seat. The exact spline, revolve profile, and small blend radii are not prescribed, but the result must remain concentric, smooth, and mechanically plausible.

## Secondary socket end

1. Center this socket exactly 350 mm in the negative global X direction from the primary socket.
2. Create a 70 mm outside-diameter cylindrical housing with a nominal 42 mm axial height.
3. Form its upper stepped collar with approximately 50 mm outside diameter and 45 mm inside diameter.
4. Create a central cylindrical opening of exactly 30 mm diameter along the global Y axis.
5. Add a rounded internal seat and lip that are visually and functionally consistent with the primary socket, while retaining the smaller outside proportions.

## Curved bridge

Join the two socket housings with a single smooth, tapered, curved solid bridge. A loft between suitable constrained profiles is a good approach, but an equivalent native Fusion construction is acceptable. The bridge must merge cleanly into both housings, remain one solid body, and have continuous, rounded transitions without abrupt block-like steps. It should be broader near the primary end and taper toward the secondary end.

The exact bridge spline, loft rails, and profile control points are intentionally not specified. Match the reference's overall bowed centerline and envelope rather than attempting to infer a unique curve. Use fillets or equivalent native blends where helpful.

## Primary flange annular pattern

Create a 360-degree circular pattern of 18 nominal positions around the primary socket axis on an approximately 102.5 mm pitch-circle diameter. Each patterned feature is a 4 mm high annular tower with 9 mm outside diameter and 6 mm inside diameter, joined to the flange. The bridge overlaps part of the circular pattern; in the intended final solid, 13 annular towers remain exposed as distinct cylindrical rings while the covered positions merge into the bridge region. Preserve the regular angular spacing and concentric placement.

## Design intent and acceptable variation

- The final result must be exactly one visible solid body.
- The two socket axes, 350 mm spacing, Ø30 openings, principal stepped diameters, and annular pattern are authoritative.
- The bridge centerline, loft profiles, detailed revolved seat profiles, and small fillets are intentionally flexible. Diverse native Fusion constructions are acceptable when they produce the same functional layout and a close overall shape.
- Keep features healthy and unsuppressed. Fully constrain sketches where practical and use a circular pattern rather than manually placing repeated towers when possible.
- Do not create disconnected helper solids, separate components, mesh bodies, or surface-only results.

## Completion requirements

Leave the completed design open in Fusion and use the finish action when the task is complete. Do not use Save or Save As; the environment exports the open design automatically. Do not open or import any external CAD file, including another task seed, STEP file, or answer archive.

Recommended interaction budget: up to 180 model turns, 600 action groups, and 3600 seconds.
