"""gold — cbsk_chain_s01：在 YZ 平面构造题面规定的 2D 草图并导出 sketch.step。"""
import cadquery as cq

PLANE = cq.Plane.named("YZ")


def w(u, v):
    return PLANE.toWorldCoords((u, v))


edges = []
LINES = [
    ((-13, -19), (-32, -19)),
    ((-32, -19), (-32, -37)),
    ((-32, -37), (-43, -37)),
    ((-43, -37), (-43, -49)),
]
for a, b in LINES:
    edges.append(cq.Edge.makeLine(w(*a), w(*b)))

cq.exporters.export(cq.Compound.makeCompound(edges), "sketch.step")
