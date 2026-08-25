"""gold — cbsk_polygon_s01：在 YZ 平面构造题面规定的 2D 草图并导出 sketch.step。"""
import cadquery as cq

PLANE = cq.Plane.named("YZ")


def w(u, v):
    return PLANE.toWorldCoords((u, v))


edges = []
LINES = [
    ((3.520908, -10.571057), (15.692446, 3.186364)),
    ((15.692446, 3.186364), (14.571057, 21.520908)),
    ((14.571057, 21.520908), (0.813636, 33.692446)),
    ((0.813636, 33.692446), (-17.520908, 32.571057)),
    ((-17.520908, 32.571057), (-29.692446, 18.813636)),
    ((-29.692446, 18.813636), (-28.571057, 0.479092)),
    ((-28.571057, 0.479092), (-14.813636, -11.692446)),
    ((-14.813636, -11.692446), (3.520908, -10.571057)),
]
for a, b in LINES:
    edges.append(cq.Edge.makeLine(w(*a), w(*b)))

cq.exporters.export(cq.Compound.makeCompound(edges), "sketch.step")
