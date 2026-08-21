"""gold 解（cadquery 阶梯轴+中心通孔）。判分参考预计算用；模型不可见。"""
import cadquery as cq

SEGMENTS = [(36.0, 25.0), (24.0, 30.0), (14.0, 18.0)]
BORE_D = 6.0

part = cq.Workplane("XY")
_z = 0.0
for _d, _l in SEGMENTS:
    _seg = cq.Workplane("XY").workplane(offset=_z).circle(_d / 2.0).extrude(_l)
    part = _seg if _z == 0.0 else part.union(_seg)
    _z += _l
part = part.faces(">Z").workplane().circle(BORE_D / 2.0).cutThruAll()
cq.exporters.export(part.val(), "part.step")
