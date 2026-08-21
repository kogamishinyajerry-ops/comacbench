"""gold 解（cadquery 套筒/环形件）。判分参考预计算用；模型不可见。"""
import cadquery as cq

OD = 60.0
BORE_D = 40.0
H = 20.0

part = cq.Workplane("XY").circle(OD / 2.0).circle(BORE_D / 2.0).extrude(H)
cq.exporters.export(part.val(), "part.step")
