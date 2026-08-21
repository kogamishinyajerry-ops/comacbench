"""gold 解（cadquery L 角支架：两腿+内圆角+腿孔）。判分参考预计算用；模型不可见。"""
import math

import cadquery as cq

LEG_X = 120.0
H = 80.0
T = 10.0
WID = 60.0
FILLET_R = 15.0
HOLE_D = 10.0
HX = T + (LEG_X - T) / 2.0
VZ = T + (H - T) / 2.0
OVER = 1.0  # 切割圆柱超出材料 1mm，避免共面布尔退化

profile = (cq.Workplane("XZ")
           .moveTo(0.0, 0.0).lineTo(LEG_X, 0.0).lineTo(LEG_X, T).lineTo(T + FILLET_R, T)
           .threePointArc((T + FILLET_R - FILLET_R / math.sqrt(2.0),
                           T + FILLET_R - FILLET_R / math.sqrt(2.0)),
                          (T, T + FILLET_R))
           .lineTo(T, H).lineTo(0.0, H).close().extrude(WID))
solid = profile.val()
if solid.Center().y < 0.0:
    solid = solid.translate(cq.Vector(0.0, WID, 0.0))
hole_h = cq.Solid.makeCylinder(HOLE_D / 2.0, T + 2.0 * OVER,
                               cq.Vector(HX, WID / 2.0, -OVER), cq.Vector(0.0, 0.0, 1.0))
hole_v = cq.Solid.makeCylinder(HOLE_D / 2.0, T + 2.0 * OVER,
                               cq.Vector(-OVER, WID / 2.0, VZ), cq.Vector(1.0, 0.0, 0.0))
solid = solid.cut(hole_h).cut(hole_v)
cq.exporters.export(solid, "part.step")
