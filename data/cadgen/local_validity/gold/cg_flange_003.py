"""gold 解（cadquery 圆法兰+螺栓孔环）。判分参考预计算用；模型不可见。"""
import cadquery as cq

PLATE_D = 140.0
THK = 10.0
N_HOLES = 12
HOLE_D = 8.0
PCD = 116.0

part = (cq.Workplane("XY").circle(PLATE_D / 2.0).extrude(THK)
        .faces(">Z").workplane()
        .polarArray(PCD / 2.0, 0.0, 360.0, N_HOLES)
        .circle(HOLE_D / 2.0).cutThruAll())
cq.exporters.export(part.val(), "part.step")
