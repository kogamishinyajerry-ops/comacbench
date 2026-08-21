"""gold 解（cadquery 矩形板+四角孔+边倒圆）。判分参考预计算用；模型不可见。"""
import cadquery as cq

L = 120.0
W = 80.0
T = 10.0
HOLE_D = 8.0
CORNER_R = 10.0
INSET = 18.0

part = (cq.Workplane("XY").rect(L, W).extrude(T)
        .edges("|Z").fillet(CORNER_R)
        .faces(">Z").workplane()
        .pushPoints([(-L / 2.0 + INSET, -W / 2.0 + INSET),
                     (L / 2.0 - INSET, -W / 2.0 + INSET),
                     (-L / 2.0 + INSET, W / 2.0 - INSET),
                     (L / 2.0 - INSET, W / 2.0 - INSET)])
        .circle(HOLE_D / 2.0).cutThruAll())
cq.exporters.export(part.val(), "part.step")
