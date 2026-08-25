"""gold — cbsk_polygon_b01：在 YZ 平面构造题面规定的 2D 草图并导出 sketch.step。"""
import cadquery as cq

PLANE = cq.Plane.named("YZ")


def w(u, v):
    return PLANE.toWorldCoords((u, v))


edges = []
LINES = [
    ((22.213486, -3.737309), (5.314143, 8.997259)),
    ((5.314143, 8.997259), (-12.019334, -3.139773)),
    ((-12.019334, -3.139773), (-5.83267, -23.375439)),
    ((-5.83267, -23.375439), (15.324376, -23.744737)),
    ((15.324376, -23.744737), (22.213486, -3.737309)),
]
for a, b in LINES:
    edges.append(cq.Edge.makeLine(w(*a), w(*b)))

cq.exporters.export(cq.Compound.makeCompound(edges), "sketch.step")
