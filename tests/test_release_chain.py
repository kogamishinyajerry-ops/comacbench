"""发行级测试链（复验报告 §7）：一条**不可跳过**的端到端链路。

报告要求原文：

    干净工作区 → validate → calibrate → 实际接口运行 → 原件归档 →
    复制 run 目录并移除临时目录 → 独立核验 → 正常恢复 → 损坏证据处理 → 完整报告

    不要再用某个模块的全绿替代这整条链。

本文件把这条链实现为**一个**测试方法，全部走真实入口、真实题包
（packs/aviation-workload-starter-v1），不做 mock：

* 前 3 环走用户可见的顶层 CLI（`comacbench validate` / `calibrate`）；
* 第 4 环走 adapter CLI（`runners.deliverable_review`），即顶层 CLI 实际分发到的
  同一个模块入口；
* 后 6 环在**副本**上做归档保真、自包含、独立核验、恢复与损坏处理；
* 末环用仓库自己的报告验收脚本真实渲染 report.html（含 Chromium 层）。

**这条链不允许被跳过。** 不设 `skip` / `xfail` / 环境探测降级：报告渲染层若
不可用，这里必须红——否则"完整报告"这一环会静默消失，链就退化成了模块全绿。

唯一允许的例外是 `COMAC_REPORT_RENDER=static`（离线交付包用），它把"报告必须被真实
浏览器渲染"降为"报告总体验收退出 0 且静态层 PASS"，并**要求该降级被显式记录**在
MANIFEST / 02_EVIDENCE / install 输出里。加 skip 标记不是允许的做法。

链上每一环都登记进 `phases`，收尾断言 10 环**全部**跑到——避免某环被静默短路。
"""
import hashlib
import json
import os
import re
import shutil
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

PACK = ROOT / "packs" / "aviation-workload-starter-v1"
TASKS = PACK / "tasks" / "enterprise.workload"
TASK_IDS = ("workload_baseline_01", "workload_missing_unit_02",
            "workload_conflict_dup_03", "workload_stale_output_04")
EVIDENCE_MANIFEST = "evidence_manifest.json"

# 报告渲染层的最低要求。默认 browser = 必须有 Playwright + Chromium 且浏览器层确实 RUN。
#
# COMAC_REPORT_RENDER=static 是**离线交付包的显式约定**（浏览器二进制无法离线安装，
# 而 Chromium 约 200 MB 且与 benchmark 使用无关）。它不是"跳过"开关：
# static 仍要求 probes/test_report_full.py 整体退出 0 且静态层 PASS，并且该降级必须在
# MANIFEST.json / 02_EVIDENCE.md / install 输出里被明确记录——已声明的降级，不是静默通过。
REPORT_RENDER = os.environ.get("COMAC_REPORT_RENDER", "browser")

PHASES = ("0-干净工作区", "1-validate", "2-calibrate", "3-实际接口运行",
          "4-原件归档", "5-复制run目录并移除临时目录", "6-独立核验",
          "7-正常恢复", "8-损坏证据处理", "9-完整报告", "10-题包零改动")

_ABS_TEMP = re.compile(r"[A-Za-z]:[\\/][^\"\\ ]*(?:Temp|tmp)[^\"\\ ]*", re.I)


def _run(argv, **kw):
    return subprocess.run(argv, cwd=ROOT, text=True, capture_output=True,
                          timeout=900, **kw)


def _comacbench(*args):
    return _run([sys.executable, "-m", "comacbench", *args])


def _adapter(*args):
    return _run([sys.executable, "-m", "runners.deliverable_review", *args])


def _tree_digests(root: Path) -> dict:
    """题包全量文件摘要（跳过 __pycache__/.pyc——导入 evaluator 会生成）。"""
    out = {}
    for p in sorted(root.rglob("*")):
        if not p.is_file():
            continue
        rel = p.relative_to(root).as_posix()
        if "__pycache__" in p.parts or rel.endswith(".pyc"):
            continue
        out[rel] = hashlib.sha256(p.read_bytes()).hexdigest()
    return out


def _sandbox_dirs() -> set:
    """当前系统临时目录里存留的隔离子工作目录。"""
    tmp = Path(tempfile.gettempdir())
    return {p for p in tmp.glob("bm_sandbox_*") if p.is_dir()}


def _absolute_temp_paths(root: Path) -> list:
    """目录内文件是否残留绝对临时路径（自包含性检查）。"""
    hits = []
    for p in sorted(root.rglob("*")):
        if not p.is_file():
            continue
        try:
            text = p.read_text(encoding="utf-8")
        except (UnicodeDecodeError, OSError):
            continue
        for m in _ABS_TEMP.finditer(text):
            hits.append((p.relative_to(root).as_posix(), m.group(0)[:80]))
    return hits


def _verify_archive(run_dir: Path, task_id: str) -> dict:
    """独立复算一个任务的归档证据：清单 ↔ 索引 ↔ 磁盘字节三方对账。"""
    ev_dir = run_dir / "evidence" / task_id
    row = json.loads((run_dir / f"result_{task_id}.json").read_text(encoding="utf-8"))
    index = json.loads(row["artifacts"]["deliverable_files"])
    manifest = json.loads(
        (ev_dir / EVIDENCE_MANIFEST).read_text(encoding="utf-8"))
    assert manifest["protocol"] == "comacbench.evidence.v1", manifest["protocol"]
    assert manifest["task_id"] == task_id
    assert manifest["complete"] is True, f"{task_id} 归档标记为不完整"
    assert row["artifacts"]["deliverable_files_dir"] == f"evidence/{task_id}"
    assert index == manifest["files"], f"{task_id} 内联索引与证据清单不一致"
    for entry in manifest["files"]:
        target = ev_dir / entry["path"]
        assert target.is_file(), f"{task_id}: {entry['path']} 未归档"
        raw = target.read_bytes()
        assert hashlib.sha256(raw).hexdigest() == entry["sha256"], \
            f"{task_id}: {entry['path']} 归档字节与摘要不符"
        assert len(raw) == entry["bytes"], f"{task_id}: {entry['path']} 长度不符"
    return manifest


class ReleaseChainTests(unittest.TestCase):
    """报告 §7 的发行级测试链：一次执行，十环全走。"""

    def test_release_chain_end_to_end(self):
        phases = []

        def mark(name):
            self.assertIn(name, PHASES, f"未知环节 {name}")
            self.assertNotIn(name, [n for n, _ in phases], f"{name} 重复执行")
            phases.append((name, ""))

        with tempfile.TemporaryDirectory(prefix="release-chain-") as temp:
            tmp = Path(temp)

            # ---- 0. 干净工作区 -------------------------------------------------
            pack_before = _tree_digests(PACK)
            self.assertTrue(pack_before, "题包摘要为空，路径错误")
            self.assertEqual(list(tmp.iterdir()), [], "工作区不是干净的")
            sandboxes_before = _sandbox_dirs()
            mark("0-干净工作区")

            # ---- 1. validate（真实顶层 CLI） -----------------------------------
            val_out = tmp / "1-validate"
            r = _comacbench("validate", str(PACK), "--out", str(val_out))
            self.assertEqual(r.returncode, 0, f"validate 失败：{r.stderr or r.stdout}")
            validation = json.loads((val_out / "validation.json").read_text(encoding="utf-8"))
            self.assertIs(validation["runnable"], True, "题包预检不通过（发布会先被拒）")
            blockers = [i for i in validation["issues"] if i["severity"] == "blocker"]
            self.assertEqual(blockers, [], f"仍有 blocker：{blockers}")
            self.assertTrue((val_out / "report.html").is_file(), "validate 未产出反馈报告")
            mark("1-validate")

            # ---- 2. calibrate（参考实现 + 错误负例管线自检） -------------------
            cal_out = tmp / "2-calibrate"
            r = _comacbench("calibrate", str(PACK), "--out", str(cal_out))
            self.assertEqual(r.returncode, 0, f"calibrate 失败：{r.stderr or r.stdout}")
            doc = json.loads((cal_out / "run.json").read_text(encoding="utf-8"))
            self.assertEqual(doc["status"], "complete", doc.get("error"))
            self.assertIs(doc["calibration_passed"], True, "校准未通过")
            self.assertEqual(len(doc["results"]), len(TASK_IDS))
            self.assertTrue(all(row["full_pass"] for row in doc["results"]),
                            f"正例未全绿：{[(r0['id'], r0.get('score')) for r0 in doc['results']]}")
            self.assertEqual(len(doc["controls"]), len(TASK_IDS))
            failed = [(c["task_id"], c["expected_issue"], c["actual_issues"])
                      for c in doc["controls"] if not c["passed"]]
            self.assertEqual(failed, [], f"负例未命中预期诊断：{failed}")
            self.assertTrue(doc["completion"]["complete"], doc["completion"])
            mark("2-calibrate")

            # ---- 3. 实际接口运行（adapter CLI，真实题包） ----------------------
            run_out = tmp / "3-run"
            r = _adapter("--tasks", str(TASKS), "--out", str(run_out),
                         "--provider", "oracle")
            self.assertEqual(r.returncode, 0, f"adapter 运行失败：{r.stderr or r.stdout}")
            for tid in TASK_IDS:
                row = json.loads(
                    (run_out / f"result_{tid}.json").read_text(encoding="utf-8"))
                self.assertEqual(row["validity_gate"], 1,
                                 f"{tid} gate 不为 1：{row.get('gate_failures')}")
                self.assertEqual(row["score"], 1.0, f"{tid} 未满分")
                self.assertIsNone(row["failure_mode"], f"{tid} 有失败模式")
            mark("3-实际接口运行")

            # ---- 4. 原件归档（字节保真） --------------------------------------
            archived = 0
            for tid in TASK_IDS:
                manifest = _verify_archive(run_out, tid)
                archived += len(manifest["files"])
                origins = {e["path"]: e.get("origin") for e in manifest["files"]}
                # agent 自己的 manifest.json 必须同批归档（旧实现把它排除在外）
                self.assertIn("manifest.json", origins, f"{tid} 未归档 agent manifest")
                self.assertEqual(origins["manifest.json"], "agent_declaration")
                # 交付 CSV 由 oracle 用 csv.DictWriter 写出（CRLF）——行尾必须原样保留，
                # 旧实现经 read_text 归一化成 LF，正是 8/12 份哈希不符的根因。
                for name in ("outputs/run_manifest.csv", "outputs/exceptions.csv"):
                    raw = (run_out / "evidence" / tid / name).read_bytes()
                    self.assertIn(b"\r\n", raw, f"{tid}: {name} 行尾被改写")
            self.assertGreaterEqual(archived, 4 * 4)
            mark("4-原件归档")

            # ---- 5. 复制 run 目录并移除临时目录 -------------------------------
            copy_root = tmp / "5-copy"
            shutil.copytree(run_out, copy_root)
            # a) 隔离子工作目录必须已被回收（adapter CLI 退出前确定性收尾）
            self.assertEqual(_sandbox_dirs() - sandboxes_before, set(),
                             "运行后仍残留 bm_sandbox_* 隔离目录")
            # b) run 目录必须自包含：不得残留任何绝对临时路径
            leaks = _absolute_temp_paths(copy_root)
            self.assertEqual(leaks, [], f"run 目录残留绝对临时路径：{leaks[:5]}")
            mark("5-复制run目录并移除临时目录")

            # ---- 6. 独立核验（在副本上，与原件/临时目录无关） -----------------
            for tid in TASK_IDS:
                _verify_archive(copy_root, tid)
            # 副本的 result 集合必须与 validate 声明的任务集合一致
            declared = {t["id"] for t in validation["tasks"]}
            self.assertEqual(declared, set(TASK_IDS))
            recorded = {p.name[len("result_"):-len(".json")]
                        for p in copy_root.glob("result_*.json")}
            self.assertEqual(recorded, declared, "副本结果集合与题包声明不一致")
            mark("6-独立核验")

            # ---- 7. 正常恢复 ---------------------------------------------------
            r = _adapter("--tasks", str(TASKS), "--out", str(copy_root),
                         "--provider", "oracle", "--resume")
            self.assertEqual(r.returncode, 0, f"正常恢复失败：{r.stderr}")
            self.assertEqual(r.stdout.count("reused (resume)"), len(TASK_IDS),
                             f"未全部复用：{r.stdout}")
            mark("7-正常恢复")

            # ---- 8. 损坏证据处理（fail-closed） -------------------------------
            damaged = tmp / "6-damaged"
            shutil.copytree(run_out, damaged)
            victim = damaged / "evidence" / TASK_IDS[0] / "outputs" / "exceptions.csv"
            raw = victim.read_bytes()
            self.assertTrue(raw, "取样的归档文件为空")
            victim.write_bytes(raw + b"tampered")
            r = _adapter("--tasks", str(TASKS), "--out", str(damaged),
                         "--provider", "oracle", "--resume")
            self.assertNotEqual(r.returncode, 0, "归档被篡改却仍复用")
            self.assertIn("[resume]", r.stderr, f"未给出拒绝理由：{r.stderr}")
            mark("8-损坏证据处理")

            # ---- 9. 完整报告 ---------------------------------------------------
            cal_report = (cal_out / "report.html").read_text(encoding="utf-8")
            val_report = (val_out / "report.html").read_text(encoding="utf-8")
            self.assertGreater(len(val_report), 2000, "validate 报告过小")
            self.assertGreater(len(cal_report), 2000, "calibrate 报告过小")
            self.assertIn(PACK.name, cal_report, "报告未内嵌题包标识")
            for tid in TASK_IDS:
                self.assertIn(tid, cal_report, f"报告缺任务 {tid}")
            self.assertIn("calibration_passed", cal_report)
            # 真实渲染：仓库自带的报告验收脚本。退出码即结论（0 = ALL_PASS）。
            harness = _run([sys.executable, "probes/test_report_full.py"])
            self.assertEqual(harness.returncode, 0,
                             f"报告渲染验收失败：\n{harness.stdout[-2000:]}")
            if REPORT_RENDER == "browser":
                # 该脚本会把浏览器层降级为 NOT_RUN 但仍退出 0——那等于"完整报告"
                # 这一环静默消失，发行链不接受。
                self.assertRegex(harness.stdout, r"浏览器层:\s*RUN",
                                 "报告渲染层降级为 NOT_RUN——发行链不允许静默降级；"
                                 "确认 Playwright + Chromium 可用，或显式设 "
                                 "COMAC_REPORT_RENDER=static 并记录该降级。")
            elif REPORT_RENDER == "static":
                # 离线交付包的显式约定：不带 Chromium（约 200 MB，且浏览器二进制
                # 无法离线安装）。此处仍要求静态层 PASS，且**必须**有明确的层结论行，
                # 同时该降级要在 MANIFEST / 02_EVIDENCE / install 输出里被记录——
                # 是"已声明的降级"，不是静默通过。
                self.assertRegex(harness.stdout, r"静态层 TDZ:\s*PASS",
                                 "静态层未通过；离线包至少要保证静态层。")
                self.assertRegex(harness.stdout, r"浏览器层:\s*(RUN|NOT_RUN)",
                                 "报告验收脚本未给出浏览器层结论行。")
            else:
                self.fail(f"COMAC_REPORT_RENDER 取值非法：{REPORT_RENDER!r}"
                          "（只接受 browser / static）")
            mark("9-完整报告")

            # ---- 10. 题包零改动（只读入口 / 不可变题包） ----------------------
            self.assertEqual(_tree_digests(PACK), pack_before,
                             "发行链改动了不可变题包")
            mark("10-题包零改动")

        # 链上每一环都必须真的跑到——防止某环被静默短路
        self.assertEqual([n for n, _ in phases], list(PHASES),
                         f"发行链未走完整：{phases}")


if __name__ == "__main__":
    unittest.main()
