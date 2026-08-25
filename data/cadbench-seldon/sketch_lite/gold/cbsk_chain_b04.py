"""gold — cbsk_chain_b04：在 YZ 平面构造题面规定的 2D 草图并导出 sketch.step。"""
import cadquery as cq

PLANE = cq.Plane.named("YZ")


def w(u, v):
    return PLANE.toWorldCoords((u, v))


edges = []
LINES = [
    ((-8, -12), (21, -12)),
    ((21, -12), (21, 5)),
    ((21, 5), (9, 5)),
    ((9, 5), (9, 26)),
    ((9, 26), (31, 26)),
    ((31, 26), (31, 44)),
    ((31, 44), (-3, 44)),
]
for a, b in LINES:
    edges.append(cq.Edge.makeLine(w(*a), w(*b)))

cq.exporters.export(cq.Compound.makeCompound(edges), "sketch.step")
