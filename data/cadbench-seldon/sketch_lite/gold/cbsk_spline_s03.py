"""gold — cbsk_spline_s03：在 XZ 平面构造题面规定的 2D 草图并导出 sketch.step。"""
import cadquery as cq

PLANE = cq.Plane.named("XZ")


def w(u, v):
    return PLANE.toWorldCoords((u, v))


edges = []
LINES = [
    ((30, 0), (-6, -19)),
    ((-6, -19), (-30, 0)),
]
for a, b in LINES:
    edges.append(cq.Edge.makeLine(w(*a), w(*b)))

SPLINES = [
    [(-30, 0), (-18, 30), (-6, 23), (6, 31), (18, 15), (30, 0)],
]
for fit in SPLINES:
    edges.append(cq.Edge.makeSpline([w(u, v) for u, v in fit]))

cq.exporters.export(cq.Compound.makeCompound(edges), "sketch.step")
