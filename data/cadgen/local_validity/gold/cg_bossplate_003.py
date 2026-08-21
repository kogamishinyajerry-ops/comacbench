"""gold 解（cadquery 带凸台底板）。判分参考预计算用；模型不可见。"""
import cadquery as cq

L = 80.0
W = 80.0
T = 8.0
BOSS_D = 25.0
BOSS_H = 15.0
HOLE_D = 7.0
INSET = 12.0

part = (cq.Workplane("XY").rect(L, W).extrude(T)
        .faces(">Z").workplane().circle(BOSS_D / 2.0).extrude(BOSS_H)
        .faces(">Z").workplane()
        .pushPoints([(-L / 2.0 + INSET, -W / 2.0 + INSET),
                     (L / 2.0 - INSET, -W / 2.0 + INSET),
                     (-L / 2.0 + INSET, W / 2.0 - INSET),
                     (L / 2.0 - INSET, W / 2.0 - INSET)])
        .circle(HOLE_D / 2.0).cutThruAll())
cq.exporters.export(part.val(), "part.step")
