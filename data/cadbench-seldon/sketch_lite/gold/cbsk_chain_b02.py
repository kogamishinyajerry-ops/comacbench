"""gold — cbsk_chain_b02：在 YZ 平面构造题面规定的 2D 草图并导出 sketch.step。"""
import cadquery as cq

PLANE = cq.Plane.named("YZ")


def w(u, v):
    return PLANE.toWorldCoords((u, v))


edges = []
LINES = [
    ((6, 3), (6, 25)),
    ((6, 25), (-13, 25)),
    ((-13, 25), (-13, 41)),
    ((-13, 41), (28, 41)),
    ((28, 41), (28, 53)),
]
for a, b in LINES:
    edges.append(cq.Edge.makeLine(w(*a), w(*b)))

cq.exporters.export(cq.Compound.makeCompound(edges), "sketch.step")
