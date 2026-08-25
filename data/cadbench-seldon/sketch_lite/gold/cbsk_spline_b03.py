"""gold — cbsk_spline_b03：在 XZ 平面构造题面规定的 2D 草图并导出 sketch.step。"""
import cadquery as cq

PLANE = cq.Plane.named("XZ")


def w(u, v):
    return PLANE.toWorldCoords((u, v))


edges = []
LINES = [
    ((26, 0), (-4, -16)),
    ((-4, -16), (-26, 0)),
]
for a, b in LINES:
    edges.append(cq.Edge.makeLine(w(*a), w(*b)))

SPLINES = [
    [(-26, 0), (-22, 19), (-11, 28), (0, 22), (11, 29), (22, 17), (26, 0)],
]
for fit in SPLINES:
    edges.append(cq.Edge.makeSpline([w(u, v) for u, v in fit]))

cq.exporters.export(cq.Compound.makeCompound(edges), "sketch.step")
