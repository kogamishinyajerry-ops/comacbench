"""gold 解（cadquery 圆法兰+螺栓孔环）。判分参考预计算用；模型不可见。"""
import cadquery as cq

PLATE_D = 120.0
THK = 12.0
N_HOLES = 8
HOLE_D = 10.0
PCD = 94.0

part = (cq.Workplane("XY").circle(PLATE_D / 2.0).extrude(THK)
        .faces(">Z").workplane()
        .polarArray(PCD / 2.0, 0.0, 360.0, N_HOLES)
        .circle(HOLE_D / 2.0).cutThruAll())
cq.exporters.export(part.val(), "part.step")
