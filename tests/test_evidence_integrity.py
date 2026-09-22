"""证据完整性与故障边界：复验报告 §4/§5/§6 的收口回归。

本文件锁住的四条不变量（旧实现全部违反，改动前这些用例会红）：

1. **归档 = 原始字节**。原地复制、复制后复算 SHA-256 与长度；不得经 `read_text`
   归一行尾，不得 `[:100000]` 截断，不得靠"前 64 字符像十六进制"猜编码。
2. **超限显式失败**。超过单文件上限就记 `over_file_limit` 并把 complete 置假，
   不允许截断后仍宣称完整。
3. **复用前核验证据（fail-closed）**。归档缺失/损坏即拒绝复用，不因 result.json
   里曾有过满分就继续授予可复核状态。
4. **故障三阶段一致**。evaluator 的**导入期**异常必须与运行期、返回协议期一样
   落成结构化作废，不得让 traceback 逸出。

另含两条判分侧契约：公开 `reason_code` 词表（不再以关键词出现推断语义）与
越界整数按内容失败处理（不再让 `math.isfinite` 抛 OverflowError 升级成作废）。
"""
import hashlib
import importlib.util
import json
import shutil
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from runners.deliverable_review import (  # noqa: E402
    EVIDENCE_MANIFEST, PROTOCOL, evaluate_deliverables, run_task,
)
from runners.common import load_tasks  # noqa: E402

WORKLOAD_PACK = ROOT / "packs" / "aviation-workload-starter-v1"
WORKLOAD_TASKS = WORKLOAD_PACK / "tasks" / "enterprise.workload"

DELIVERABLES = [
    {"path": "outputs/normalized.json", "kind": "normalized"},
    {"path": "outputs/run_manifest.csv", "kind": "run_manifest"},
    {"path": "outputs/exceptions.csv", "kind": "exceptions"},
]

# oracle 写进 workspace 的字节；测试用同一份常量离线复算，不依赖临时目录存活。
EXPECTED = {
    "outputs/crlf.csv": b"a,b\r\n1,2\r\n",
    "outputs/big.txt": b"x" * 150000,
    "outputs/blob.bin": bytes(range(256)) * 300,
}

# 注意：源串里必须写成 \\r\\n，让 oracle 源码含转义序列而不是真的换行。
ORACLE_SRC = (
    "import json, pathlib\n"
    "w = pathlib.Path.cwd()\n"
    "(w / 'outputs').mkdir(exist_ok=True)\n"
    "(w / 'outputs' / 'crlf.csv').write_bytes(b'a,b\\r\\n1,2\\r\\n')\n"
    "(w / 'outputs' / 'big.txt').write_bytes(b'x' * 150000)\n"
    "(w / 'outputs' / 'blob.bin').write_bytes(bytes(range(256)) * 300)\n"
    "(w / 'manifest.json').write_text(json.dumps({\n"
    f"  'protocol': '{PROTOCOL}',\n"
    "  'deliverables': [\n"
    "    {'path': 'outputs/crlf.csv', 'kind': 'normalized'},\n"
    "    {'path': 'outputs/big.txt', 'kind': 'run_manifest'},\n"
    "    {'path': 'outputs/blob.bin', 'kind': 'exceptions'}]}), encoding='utf-8')\n"
)

PASSING_EVALUATOR = (
    "def evaluate(task, workspace, deliverables):\n"
    "    return {'checks': [{'name': 'all_ok', 'passed': True,\n"
    "                        'expected': 'ok', 'actual': 'ok'}],\n"
    "            'summary': '1/1'}\n"
)

IMPORT_CRASH_EVALUATOR = "raise RuntimeError('boom at import time')\n"

TASK_YAML = (
    "id: ev_01\nregistry_id: enterprise.data\ndomain: data\n"
    "task_type: deliverable_review\nmodel_profile: plain_llm\n"
    "assets_revision: evidence-e2e@1\nenvironment_digest: computed-at-runtime\n"
    "hidden: false\nallowed_tools: [python]\n"
    "input:\n  prompt_file: tasks/enterprise.data/ev_01.md\n"
    "  prompt_sha256: {sha}\n  assets: []\n"
    "output_contract:\n- manifest.json\n"
    "reference:\n  source: synthetic\n  revision: r1\n  uncertainty_note: exact\n"
    "license_provenance:\n  license: CC0-1.0\n  source: synthetic\n  revision: r1\n"
    "grader:\n  answer_format: code\n  exec_kind: file_package\n"
    "  validity_gate: true\n"
    "  evaluator: {{module: ev_eval}}\n"
    "  deliverable_kinds: [normalized, run_manifest, exceptions]\n"
    "  oracle_source: private/ev_oracle.py\n"
    "limits: {{cpu: 1, memory_gb: 1, wall_clock_s: 60, attempts: 1}}\n"
    "scoring:\n  weights: {{physics: 0.55, requirements: 0.45, objective: 0,"
    " robustness: 0}}\n"
    "evaluation:\n  requirements:\n  - {{id: r1, text: deliver,"
    " check: 'evaluator:all_ok'}}\n"
    "  negative_controls: []\n"
)


def _make_pack(root: Path, evaluator_src: str = PASSING_EVALUATOR,
               oracle_src: str = ORACLE_SRC) -> Path:
    pack = root / "pack"
    (pack / "private").mkdir(parents=True)
    (pack / "tasks" / "enterprise.data").mkdir(parents=True)
    (pack / "pack.yaml").write_text(
        "protocol: comacbench.pack.v1\nid: evidence-e2e\ntitle: t\nrevision: '1'\n"
        "license: x\nsource: x\n"
        "suites:\n- id: enterprise.data\n  family: enterprise_data\n"
        "  tasks:\n  - tasks/enterprise.data/ev_01.yaml\n", encoding="utf-8")
    (pack / "private" / "ev_eval.py").write_text(evaluator_src, encoding="utf-8")
    (pack / "private" / "ev_oracle.py").write_text(oracle_src, encoding="utf-8")
    prompt = "deliver\n"
    (pack / "tasks" / "enterprise.data" / "ev_01.md").write_text(
        prompt, encoding="utf-8")
    sha = hashlib.sha256(prompt.encode()).hexdigest()
    (pack / "tasks" / "enterprise.data" / "ev_01.yaml").write_text(
        TASK_YAML.format(sha=sha), encoding="utf-8")
    return pack


def _run_cli(tasks_dir: Path, out: Path, *extra: str):
    return subprocess.run(
        [sys.executable, "-m", "runners.deliverable_review",
         "--tasks", str(tasks_dir), "--out", str(out),
         "--provider", "oracle", *extra],
        cwd=ROOT, text=True, capture_output=True, timeout=120)


class ByteFaithfulArchiveTests(unittest.TestCase):
    """§4：归档必须是被检查过的原始字节。"""

    def setUp(self):
        self._tmp = tempfile.TemporaryDirectory(prefix="evidence-")
        self.tmp = Path(self._tmp.name)
        self.pack = _make_pack(self.tmp)
        self.tasks = self.pack / "tasks" / "enterprise.data"
        self.out = self.tmp / "out"

    def tearDown(self):
        self._tmp.cleanup()

    def test_archived_bytes_equal_originals(self):
        done = _run_cli(self.tasks, self.out)
        self.assertEqual(done.returncode, 0, done.stderr)
        ev_dir = self.out / "evidence" / "ev_01"
        for rel, raw in EXPECTED.items():
            archived = ev_dir / rel
            self.assertTrue(archived.is_file(), f"{rel} 未归档")
            # 旧实现：crlf.csv 被 read_text 归一化成 LF、big.txt 被截到 100000 B、
            # blob.bin 被 hex 化并截断 —— 三者都在此断言下失败。
            self.assertEqual(archived.read_bytes(), raw, f"{rel} 字节不保真")
            self.assertEqual(archived.stat().st_size, len(raw))

    def test_manifest_digests_match_recomputed_bytes(self):
        self.assertEqual(_run_cli(self.tasks, self.out).returncode, 0)
        ev_dir = self.out / "evidence" / "ev_01"
        manifest = json.loads((ev_dir / EVIDENCE_MANIFEST).read_text(encoding="utf-8"))
        self.assertTrue(manifest["complete"])
        self.assertEqual(manifest["task_id"], "ev_01")
        by_path = {e["path"]: e for e in manifest["files"]}
        for rel, raw in EXPECTED.items():
            self.assertEqual(by_path[rel]["sha256"],
                             hashlib.sha256(raw).hexdigest(), rel)
            self.assertEqual(by_path[rel]["bytes"], len(raw), rel)
        # agent 的 manifest.json 原件必须同批归档（旧实现把它排除在外）
        self.assertIn("manifest.json", by_path)
        self.assertEqual(by_path["manifest.json"]["origin"], "agent_declaration")

    def test_result_carries_index_not_content(self):
        self.assertEqual(_run_cli(self.tasks, self.out).returncode, 0)
        row = json.loads((self.out / "result_ev_01.json").read_text(encoding="utf-8"))
        index = json.loads(row["artifacts"]["deliverable_files"])
        self.assertIsInstance(index, list)
        self.assertEqual(row["artifacts"]["deliverable_files_dir"], "evidence/ev_01")
        self.assertNotIn("error", json.dumps(index))
        # result.json 里不能出现交付内容本身——JSON 承载任意字节正是此前失真的根因
        raw_result = (self.out / "result_ev_01.json").read_text(encoding="utf-8")
        self.assertNotIn("a,b\\r\\n1,2", raw_result)
        self.assertNotIn("xxxx", raw_result)

    def test_over_limit_is_explicit_not_truncated(self):
        """超限必须显式失败：不落盘、记 over_file_limit、gate=0。"""
        big = (
            "import json, pathlib\n"
            "w = pathlib.Path.cwd()\n"
            "(w / 'outputs').mkdir(exist_ok=True)\n"
            "(w / 'outputs' / 'huge.bin').write_bytes(b'y' * (9 << 20))\n"
            "(w / 'manifest.json').write_text(json.dumps({\n"
            f"  'protocol': '{PROTOCOL}',\n"
            "  'deliverables': [{'path': 'outputs/huge.bin',"
            " 'kind': 'normalized'}]}), encoding='utf-8')\n")
        pack = _make_pack(self.tmp / "over", oracle_src=big)
        out = self.tmp / "out_over"
        self.assertEqual(_run_cli(pack / "tasks" / "enterprise.data", out).returncode, 0)
        ev_dir = out / "evidence" / "ev_01"
        # 不落盘、更不落半截
        self.assertFalse((ev_dir / "outputs" / "huge.bin").exists())
        manifest = json.loads((ev_dir / EVIDENCE_MANIFEST).read_text(encoding="utf-8"))
        self.assertFalse(manifest["complete"])
        entry = next(e for e in manifest["files"] if e["path"] == "outputs/huge.bin")
        self.assertEqual(entry["error"], "over_file_limit")
        row = json.loads((out / "result_ev_01.json").read_text(encoding="utf-8"))
        self.assertEqual(row["validity_gate"], 0)

    def test_evaluator_output_is_sealed_into_evidence(self):
        self.assertEqual(_run_cli(self.tasks, self.out).returncode, 0)
        ev_dir = self.out / "evidence" / "ev_01"
        manifest = json.loads((ev_dir / EVIDENCE_MANIFEST).read_text(encoding="utf-8"))
        self.assertIn("evaluator_output.json",
                      {e["path"] for e in manifest["files"]})


class EvidenceVerifiedResumeTests(unittest.TestCase):
    """§5：复用前逐条核验归档字节；不可核验即拒绝复用（fail-closed）。"""

    def setUp(self):
        self._tmp = tempfile.TemporaryDirectory(prefix="evidence-resume-")
        self.tmp = Path(self._tmp.name)
        self.pack = _make_pack(self.tmp)
        self.tasks = self.pack / "tasks" / "enterprise.data"
        self.out = self.tmp / "out"
        self.first = _run_cli(self.tasks, self.out)
        self.assertEqual(self.first.returncode, 0, self.first.stderr)
        self.ev_dir = self.out / "evidence" / "ev_01"

    def tearDown(self):
        self._tmp.cleanup()

    def _resume(self):
        return _run_cli(self.tasks, self.out, "--resume")

    def test_clean_resume_reuses(self):
        again = self._resume()
        self.assertEqual(again.returncode, 0, again.stderr)
        self.assertIn("reused (resume)", again.stdout)

    def test_corrupted_evidence_file_refuses_reuse(self):
        target = self.ev_dir / "outputs" / "crlf.csv"
        target.write_bytes(target.read_bytes() + b"corrupted")
        again = self._resume()
        self.assertNotEqual(again.returncode, 0, "损坏的归档仍被复用")
        self.assertIn("[resume]", again.stderr)

    def test_missing_evidence_file_refuses_reuse(self):
        (self.ev_dir / "outputs" / "big.txt").unlink()
        again = self._resume()
        self.assertNotEqual(again.returncode, 0, "缺失的归档仍被复用")
        self.assertIn("[resume]", again.stderr)

    def test_missing_evidence_manifest_refuses_reuse(self):
        (self.ev_dir / EVIDENCE_MANIFEST).unlink()
        again = self._resume()
        self.assertNotEqual(again.returncode, 0, "清单缺失仍被复用")
        self.assertIn("[resume]", again.stderr)

    def test_missing_whole_evidence_dir_refuses_reuse(self):
        shutil.rmtree(self.out / "evidence")
        again = self._resume()
        self.assertNotEqual(again.returncode, 0, "证据目录整体缺失仍被复用")
        self.assertIn("[resume]", again.stderr)

    def test_rewritten_manifest_still_refuses_reuse(self):
        """只改证据目录（连同清单一起改）也必须被拦：result 内联索引是第二道锚。"""
        target = self.ev_dir / "outputs" / "crlf.csv"
        target.write_bytes(b"totally,different\n")
        manifest_path = self.ev_dir / EVIDENCE_MANIFEST
        manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
        raw = target.read_bytes()
        for entry in manifest["files"]:
            if entry["path"] == "outputs/crlf.csv":
                entry["sha256"] = hashlib.sha256(raw).hexdigest()
                entry["bytes"] = len(raw)
        manifest_path.write_text(json.dumps(manifest), encoding="utf-8")
        again = self._resume()
        self.assertNotEqual(again.returncode, 0, "清单与索引不一致仍被复用")
        self.assertIn("[resume]", again.stderr)

    def test_resume_does_not_mutate_existing_results(self):
        before = (self.out / "result_ev_01.json").read_bytes()
        self._resume()
        self.assertEqual((self.out / "result_ev_01.json").read_bytes(), before)


class EvaluatorFailureStageTests(unittest.TestCase):
    """§6.1：导入期异常与运行期同等待遇，不得逸出。"""

    def test_import_error_becomes_structured_voided_result(self):
        with tempfile.TemporaryDirectory(prefix="evidence-import-") as tmp:
            tmp = Path(tmp)
            pack = _make_pack(tmp, evaluator_src=IMPORT_CRASH_EVALUATOR)
            tasks = load_tasks(str(pack / "tasks" / "enterprise.data"))
            oracle_cache = {t.id: ORACLE_SRC for t in tasks}
            # 旧实现：loader.exec_module 的 except 里 re-raise → RuntimeError 逸出
            r = run_task(tasks[0], provider="oracle", model=None, seed=0,
                         env_digest="e", prompt_cache={t.id: "p" for t in tasks},
                         assets_root=pack / "tasks",
                         oracle_cache=oracle_cache,
                         evidence_dir=tmp / "out" / "evidence" / tasks[0].id)
            self.assertEqual(r["validity_gate"], 0)
            self.assertTrue(r.get("voided"))
            self.assertIn("infrastructure_voided", r["gate_failures"])
            details = json.loads(r["artifacts"]["grade_details"])
            self.assertEqual(details["evaluator"]["stage"], "import")
            self.assertFalse(details["evaluator"]["evaluated"])

    def test_protocol_violation_and_runtime_crash_share_the_path(self):
        """三段（加载/执行/返回协议）都走同一失败路径，不再各写各的。"""
        with tempfile.TemporaryDirectory(prefix="evidence-proto-") as tmp:
            tmp = Path(tmp)
            pack = _make_pack(tmp, evaluator_src=(
                "def evaluate(task, workspace, deliverables):\n"
                "    return {'checks': [{'name': 'x', 'passed': 'false'}]}\n"))
            tasks = load_tasks(str(pack / "tasks" / "enterprise.data"))
            r = run_task(tasks[0], provider="oracle", model=None, seed=0,
                         env_digest="e", prompt_cache={t.id: "p" for t in tasks},
                         assets_root=pack / "tasks",
                         oracle_cache={t.id: ORACLE_SRC for t in tasks})
            self.assertTrue(r.get("voided"))
            self.assertEqual(r["validity_gate"], 0)


def _load_workload_evaluator():
    spec = importlib.util.spec_from_file_location(
        "workload_evaluator_under_test",
        WORKLOAD_PACK / "private" / "workload_evaluator.py")
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


class WorkloadJudgeContractTests(unittest.TestCase):
    """§6.2/§6.3：judge 侧的公开契约与数值边界。"""

    @classmethod
    def setUpClass(cls):
        cls.ev = _load_workload_evaluator()
        tasks = load_tasks(str(WORKLOAD_TASKS))
        cls.task = next(t for t in tasks if t.id == "workload_missing_unit_02")

    def _workspace(self, rows, exceptions, case_id="BLEED-CHK-B", version="2026-09-12"):
        root = Path(tempfile.mkdtemp(prefix="workload-"))
        out = root / "outputs"
        out.mkdir(parents=True)
        (out / "normalized.json").write_text(json.dumps(
            {"case_id": case_id, "rows": rows}), encoding="utf-8")
        import csv as _csv
        with (out / "run_manifest.csv").open("w", newline="", encoding="utf-8") as fh:
            wr = _csv.DictWriter(fh, fieldnames=["point", "case_id", "version"])
            wr.writeheader()
            for r in rows:
                wr.writerow({"point": r["point"], "case_id": case_id,
                             "version": version})
        fields = ["point", "reason_code", "reason", "detail"]
        with (out / "exceptions.csv").open("w", newline="", encoding="utf-8") as fh:
            wr = _csv.DictWriter(fh, fieldnames=fields)
            wr.writeheader()
            for e in exceptions:
                wr.writerow(e)
        (root / "manifest.json").write_text(json.dumps({
            "protocol": PROTOCOL,
            "deliverables": DELIVERABLES}), encoding="utf-8")
        return root

    @staticmethod
    def _row(point, alt, mass):
        return {"point": point, "altitude_m": alt, "mass_flow_kg_s": mass,
                "source_version": "2026-09-12"}

    def test_huge_integer_fails_content_not_infrastructure(self):
        """10**400 是模型交付错误 → units_explicit 判失败，不得抛 OverflowError。"""
        rows = [self._row("P1", 0, 1.2), self._row("P3", 11000, 0.72),
                self._row("P2", 10 ** 400, 0.95)]
        ws = self._workspace(rows, [
            {"point": "P2", "reason_code": "missing_unit",
             "reason": "高度缺单位", "detail": "altitude 无单位后缀"}])
        result = self.ev.evaluate(self.task, ws, DELIVERABLES)
        # 关键是"判失败"而不是"抛异常升级成基础设施作废"
        self.assertIn("units_explicit", result["failed"])
        self.assertNotIn("rejection_reasons_match", result["failed"])

    def test_reason_code_off_vocabulary_is_rejected(self):
        """表外 code 必须有明确拒绝语义，不再以关键词出现推断成立。"""
        rows = [self._row("P1", 0, 1.2), self._row("P3", 11000, 0.72)]
        ws = self._workspace(rows, [
            {"point": "P2", "reason_code": "community_event",
             "reason": "community event", "detail": "done"}])
        result = self.ev.evaluate(self.task, ws, DELIVERABLES)
        self.assertIn("rejection_reasons_match", result["failed"])

    def test_reason_code_category_mismatch_is_rejected(self):
        """旧子串逻辑的反例：reason 文本含关键词但 code 类别错，必须被拦。"""
        rows = [self._row("P1", 0, 1.2), self._row("P3", 11000, 0.72)]
        ws = self._workspace(rows, [
            {"point": "P2", "reason_code": "conflict",
             "reason": "no conflict exists", "detail": "no conflict"}],)
        result = self.ev.evaluate(self.task, ws, DELIVERABLES)
        self.assertIn("rejection_reasons_match", result["failed"])

    def test_correct_reason_code_passes_regardless_of_prose(self):
        """自由文本只校验非空，不据措辞判分——这是公开契约的应有语义。"""
        rows = [self._row("P1", 0, 1.2), self._row("P3", 11000, 0.72)]
        ws = self._workspace(rows, [
            {"point": "P2", "reason_code": "missing_unit",
             "reason": "whatever wording the agent likes",
             "detail": "字段缺失单位，需澄清"}])
        result = self.ev.evaluate(self.task, ws, DELIVERABLES)
        self.assertNotIn("rejection_reasons_match", result["failed"])

    def test_empty_detail_still_rejected(self):
        rows = [self._row("P1", 0, 1.2), self._row("P3", 11000, 0.72)]
        ws = self._workspace(rows, [
            {"point": "P2", "reason_code": "missing_unit",
             "reason": "缺单位", "detail": "   "}])
        result = self.ev.evaluate(self.task, ws, DELIVERABLES)
        self.assertIn("rejection_reasons_match", result["failed"])

    def test_reason_code_vocabulary_is_public_and_documented(self):
        codes = set(self.ev.PUBLIC_REASON_CODES)
        self.assertEqual(codes, {"missing_unit", "conflict", "stale"})
        prompt = (WORKLOAD_TASKS / "workload_missing_unit_02.md").read_text(
            encoding="utf-8")
        for code in codes:
            self.assertIn(code, prompt, f"{code} 未在题面公开")


class LineEndingFreezeTests(unittest.TestCase):
    """§3：题面行尾策略必须冻结且与 YAML 摘要一致。"""

    def test_prompts_are_lf_and_digest_matches(self):
        import hashlib as _h
        import yaml
        for yaml_path in sorted(WORKLOAD_TASKS.glob("*.yaml")):
            spec = yaml.safe_load(yaml_path.read_text(encoding="utf-8"))
            rel = spec["input"]["prompt_file"]
            prompt = (WORKLOAD_PACK / rel)
            raw = prompt.read_bytes()
            self.assertNotIn(b"\r\n", raw, f"{prompt.name} 含 CRLF，行尾未统一")
            self.assertEqual(_h.sha256(raw).hexdigest(),
                             spec["input"]["prompt_sha256"], prompt.name)


if __name__ == "__main__":
    unittest.main()
