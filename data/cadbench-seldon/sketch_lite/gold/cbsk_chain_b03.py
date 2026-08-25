"""gold — cbsk_chain_b03：在 YZ 平面构造题面规定的 2D 草图并导出 sketch.step。"""
import cadquery as cq

PLANE = cq.Plane.named("YZ")


def w(u, v):
    return PLANE.toWorldCoords((u, v))


edges = []
LINES = [
    ((0, 0), (19, 0)),
    ((19, 0), (19, 14)),
    ((19, 14), (7, 14)),
    ((7, 14), (7, 32)),
    ((7, 32), (-15, 32)),
    ((-15, 32), (-15, -9)),
]
for a, b in LINES:
    edges.append(cq.Edge.makeLine(w(*a), w(*b)))

cq.exporters.export(cq.Compound.makeCompound(edges), "sketch.step")
