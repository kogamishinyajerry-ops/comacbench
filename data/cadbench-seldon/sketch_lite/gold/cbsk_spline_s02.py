"""gold — cbsk_spline_s02：在 XZ 平面构造题面规定的 2D 草图并导出 sketch.step。"""
import cadquery as cq

PLANE = cq.Plane.named("XZ")


def w(u, v):
    return PLANE.toWorldCoords((u, v))


edges = []
LINES = [
    ((34, 0), (6, -20)),
    ((6, -20), (-34, 0)),
]
for a, b in LINES:
    edges.append(cq.Edge.makeLine(w(*a), w(*b)))

SPLINES = [
    [(-34, 0), (-11.333333, 17), (11.333333, 32), (34, 0)],
]
for fit in SPLINES:
    edges.append(cq.Edge.makeSpline([w(u, v) for u, v in fit]))

cq.exporters.export(cq.Compound.makeCompound(edges), "sketch.step")
