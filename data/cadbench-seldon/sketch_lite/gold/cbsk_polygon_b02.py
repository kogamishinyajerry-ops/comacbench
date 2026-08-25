"""gold — cbsk_polygon_b02：在 YZ 平面构造题面规定的 2D 草图并导出 sketch.step。"""
import cadquery as cq

PLANE = cq.Plane.named("YZ")


def w(u, v):
    return PLANE.toWorldCoords((u, v))


edges = []
LINES = [
    ((-38.615146, -15.721934), (-14.65608, -33.776385)),
    ((-14.65608, -33.776385), (12.959065, -22.054451)),
    ((12.959065, -22.054451), (16.615146, 7.721934)),
    ((16.615146, 7.721934), (-7.34392, 25.776385)),
    ((-7.34392, 25.776385), (-34.959065, 14.054451)),
    ((-34.959065, 14.054451), (-38.615146, -15.721934)),
]
for a, b in LINES:
    edges.append(cq.Edge.makeLine(w(*a), w(*b)))

cq.exporters.export(cq.Compound.makeCompound(edges), "sketch.step")
