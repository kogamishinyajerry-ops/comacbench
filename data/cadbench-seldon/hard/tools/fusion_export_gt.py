# Fusion 批处理脚本：把镜像的 CADBench-Hard answer.f3d 批量转为本地可解析 GT
#
# 用法（一次性，人在 Fusion 里执行）：
#   1. Fusion 菜单 Utilities -> ADD-INS -> Scripts and Add-Ins -> Scripts 标签 -> 绿色 +
#      -> Create -> Python -> 名字填 cadbench_export -> OK
#   2. 在编辑器里用本文件内容整体替换 cadbench_export.py，保存，点 Run
#   3. 等待完成弹窗（~43 个文档，每个几秒）；产物与日志落 data/cadbench-seldon/hard/
#      step_gt/<task_id>.step（实体任务）与 sketch_gt/<task_id>.json（全部任务的草图几何）
#
# 判分方视角说明：题面「禁脚本/API」约束的是被测 agent 的作答方式；本仓库作为判分方
# 用官方 API 把私有 .f3d 转为开放格式 GT（CC-BY-4.0 允许带署名衍生），不违反基准协议。
#
# 幂等：已存在的产物跳过（sha256 相同的 f3d 去重，先跑哈希再开文档）。
import adsk.core
import adsk.fusion
import traceback
import os
import glob
import hashlib
import json

REPO = os.path.expanduser(
    "~/projects/jerry-personal/JerryDSH-COMACBench/data/cadbench-seldon/hard")
SRC = os.path.join(REPO, "tasks")
DST_STEP = os.path.join(REPO, "step_gt")
DST_SKETCH = os.path.join(REPO, "sketch_gt")
LOG = os.path.join(REPO, "gt_export.log")


def _p2(p):
    try:
        return [round(p.x, 6), round(p.y, 6)]
    except Exception:
        return None


def dump_sketches(design):
    out = []
    for sk in design.rootComponent.sketches:
        ent = {"name": sk.name, "lines": [], "circles": [], "arcs": [], "spline_count": 0}
        try:
            for ln in sk.sketchCurves.sketchLines:
                ent["lines"].append(
                    [_p2(ln.startSketchPoint.geometry), _p2(ln.endSketchPoint.geometry)])
        except Exception:
            pass
        try:
            for c in sk.sketchCurves.sketchCircles:
                ent["circles"].append(
                    [_p2(c.centerSketchPoint.geometry), round(c.radius, 6)])
        except Exception:
            pass
        try:
            for a in sk.sketchCurves.sketchArcs:
                ent["arcs"].append([_p2(a.centerSketchPoint.geometry),
                                    round(a.radius, 6),
                                    round(a.startAngle, 6), round(a.endAngle, 6)])
        except Exception:
            pass
        try:
            ent["spline_count"] = sk.sketchCurves.sketchFittedSplines.count
        except Exception:
            pass
        out.append(ent)
    return out


def process(app, f3d, tid, lines):
    doc = None
    try:
        doc = app.documents.open(f3d, False)
        design = adsk.fusion.Design.cast(app.activeProduct)
        rec = {"task_id": tid, "sketches": dump_sketches(design),
               "body_count": design.rootComponent.bRepBodies.count}
        # 实体非空才导 STEP（STEP 不携带草图）
        if rec["body_count"] > 0:
            out = os.path.join(DST_STEP, tid + ".step")
            opts = design.exportManager.createSTEPExportOptions(
                out, design.rootComponent)
            ok = design.exportManager.execute(opts)
            rec["step_exported"] = bool(ok)
        with open(os.path.join(DST_SKETCH, tid + ".json"), "w") as f:
            json.dump(rec, f, ensure_ascii=False)
        lines.append("OK   {} bodies={} sketches={}".format(
            tid, rec["body_count"], len(rec["sketches"])))
        return True
    except Exception as e:
        lines.append("ERR  {}: {}".format(tid, e))
        return False
    finally:
        if doc:
            doc.close(False)


def run(context):
    ui = None
    lines = []
    try:
        app = adsk.core.Application.get()
        ui = app.userInterface
        os.makedirs(DST_STEP, exist_ok=True)
        os.makedirs(DST_SKETCH, exist_ok=True)

        # 去重：变体对共享同一 answer.f3d（字节级相同）——按 sha256 分组只开一次
        groups = {}
        for f3d in sorted(glob.glob(os.path.join(SRC, "*", "answer.f3d"))):
            h = hashlib.sha256(open(f3d, "rb").read()).hexdigest()
            groups.setdefault(h, []).append(
                (os.path.basename(os.path.dirname(f3d)), f3d))
        lines.append("found {} f3d, {} unique".format(
            sum(len(v) for v in groups.values()), len(groups)))

        ok = fail = 0
        for h, members in sorted(groups.items(), key=lambda kv: kv[1][0][0]):
            primary_tid, f3d = members[0]
            # 组内任一已有产物则整组跳过（幂等续跑）
            if all(os.path.exists(os.path.join(DST_SKETCH, t + ".json"))
                   for t, _ in members):
                lines.append("skip " + ",".join(t for t, _ in members))
                ok += len(members)
                continue
            if process(app, f3d, primary_tid, lines):
                ok += 1
            else:
                fail += 1
                continue
            # 变体复制同一 GT（草图 json + step）
            for t, _ in members[1:]:
                try:
                    rec = json.load(open(os.path.join(DST_SKETCH, primary_tid + ".json")))
                    rec["task_id"] = t
                    rec["gt_dedup_of"] = primary_tid
                    with open(os.path.join(DST_SKETCH, t + ".json"), "w") as f:
                        json.dump(rec, f, ensure_ascii=False)
                    sp = os.path.join(DST_STEP, primary_tid + ".step")
                    if os.path.exists(sp):
                        import shutil
                        shutil.copy(sp, os.path.join(DST_STEP, t + ".step"))
                    ok += 1
                    lines.append("dup  {} -> {}".format(t, primary_tid))
                except Exception as e:
                    fail += 1
                    lines.append("ERR  dup {}: {}".format(t, e))

        with open(LOG, "w") as f:
            f.write("\n".join(lines) +
                    "\nsummary: ok={} fail={}\n".format(ok, fail))
        ui.messageBox("CADBench GT export done.\nok={} fail={}\n\nLog:\n{}".format(
            ok, fail, LOG))
    except:
        if ui:
            ui.messageBox("Failed:\n{}".format(traceback.format_exc()))
